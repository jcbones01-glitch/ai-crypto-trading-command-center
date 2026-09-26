"""PSR-01B Development execution lock and durable one-shot claim."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Callable, Mapping
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .psr01b_core import PSR01BError
from .psr01b_preflight import ROOT

DEFAULT_RESULT_PATH = ROOT / "research/experiments/psr01b_development_v1/result.json"
DEFAULT_CLAIM_REF = "refs/tags/psr01b-development-one-shot-claim-v1"
DEFAULT_REVIEW_ANCHOR_REF = "refs/heads/psr-01b-bounded-implementation-reviewed-v2"
CONFIRMATION_PREFIX = "PSR01B_DEVELOPMENT_V1"
ALLOWED_POST_CANDIDATE_PATHS = {
    "research/governance/psr01b_implementation_freeze_v1.json",
}


def _git_head_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise PSR01BError("cannot determine PSR-01B execution checkout HEAD") from exc


def _git_blob(relative: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "hash-object", "--", relative], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise PSR01BError(f"cannot hash PSR-01B path: {relative}") from exc


def _git_blob_at_commit(commit: str, relative: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", f"{commit}:{relative}"], cwd=ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise PSR01BError(f"cannot resolve reviewed candidate blob: {relative}") from exc


def verify_candidate_blob_contract(
    candidate: str, expected: Mapping[str, str]
) -> dict[str, str]:
    if not isinstance(candidate, str) or len(candidate) != 40:
        raise PSR01BError("invalid PSR-01B reviewed candidate SHA")
    if not expected:
        raise PSR01BError("PSR-01B frozen implementation blob inventory missing")
    observed: dict[str, str] = {}
    for relative, frozen_blob in expected.items():
        candidate_blob = _git_blob_at_commit(candidate, str(relative))
        current_blob = _git_blob(str(relative))
        if candidate_blob != frozen_blob:
            raise PSR01BError(
                f"freeze blob does not equal reviewed candidate: {relative}"
            )
        if current_blob != candidate_blob:
            raise PSR01BError(
                f"execution checkout differs from reviewed candidate blob: {relative}"
            )
        observed[str(relative)] = current_blob
    return observed


def verify_execution_commit(
    candidate: str, executing_sha: str | None = None
) -> tuple[str, ...]:
    executing_sha = executing_sha or os.environ.get("GITHUB_SHA") or _git_head_sha()
    try:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", candidate, executing_sha],
            cwd=ROOT, check=False
        )
    except OSError as exc:
        raise PSR01BError("cannot verify PSR-01B execution ancestry") from exc
    if ancestor.returncode != 0:
        raise PSR01BError(
            "PSR-01B executing commit is not descended from reviewed candidate"
        )
    try:
        changed = tuple(
            x for x in subprocess.check_output(
                ["git", "diff", "--name-only", candidate, executing_sha],
                cwd=ROOT, text=True
            ).splitlines() if x
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise PSR01BError("cannot verify PSR-01B post-candidate tree diff") from exc
    forbidden = sorted(set(changed) - ALLOWED_POST_CANDIDATE_PATHS)
    if forbidden:
        raise PSR01BError(
            "PSR-01B unapproved post-candidate path changed: " + ", ".join(forbidden)
        )
    return changed


def _request(url: str, token: str, *, method: str = "GET", data: bytes | None = None):
    return Request(
        url, data=data, method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "psr01b-development-v1-governance",
        },
    )


def _resolve_fixed_ref(
    repository: str, token: str, ref: str, *, opener: Callable = urlopen
) -> str | None:
    if ref not in {DEFAULT_CLAIM_REF, DEFAULT_REVIEW_ANCHOR_REF}:
        raise PSR01BError("unexpected PSR-01B fixed governance ref")
    if not repository or "/" not in repository or not token:
        raise PSR01BError("repository and token required for durable-ref verification")
    short_ref = ref.removeprefix("refs/")
    url = f"https://api.github.com/repos/{repository}/git/ref/{quote(short_ref, safe='/')}"
    try:
        response = opener(_request(url, token))
        with response:
            body = response.read()
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise PSR01BError(f"durable-ref lookup failed with HTTP {exc.code}") from exc
    try:
        resolved = json.loads(body)
    except json.JSONDecodeError as exc:
        raise PSR01BError("invalid durable-ref response") from exc
    if resolved.get("ref") != ref:
        raise PSR01BError("GitHub returned unexpected PSR-01B durable ref")
    target = resolved.get("object", {}).get("sha")
    if not target:
        raise PSR01BError("PSR-01B durable ref lacks target SHA")
    return str(target)


def create_fixed_ref(
    repository: str, sha: str, token: str, *, ref: str, opener: Callable = urlopen
) -> dict[str, str]:
    if ref not in {DEFAULT_CLAIM_REF, DEFAULT_REVIEW_ANCHOR_REF}:
        raise PSR01BError("unexpected PSR-01B fixed governance ref")
    payload = json.dumps({"ref": ref, "sha": sha}).encode("utf-8")
    url = f"https://api.github.com/repos/{repository}/git/refs"
    try:
        response = opener(_request(url, token, method="POST", data=payload))
        with response:
            body = response.read()
    except HTTPError as exc:
        if exc.code == 422:
            raise PSR01BError(f"fixed governance ref already exists: {ref}") from exc
        raise PSR01BError(f"create-ref failed with HTTP {exc.code}") from exc
    created = json.loads(body)
    if created.get("ref") != ref or created.get("object", {}).get("sha") != sha:
        raise PSR01BError("GitHub returned unexpected created ref")
    return {"ref": ref, "sha": sha}


def assert_review_anchor(
    candidate: str, freeze: Mapping[str, Any], *,
    repository: str | None = None, token: str | None = None,
    opener: Callable = urlopen,
) -> dict[str, str]:
    if freeze.get("review_anchor_ref") != DEFAULT_REVIEW_ANCHOR_REF:
        raise PSR01BError("PSR-01B freeze review-anchor ref mismatch")
    if freeze.get("review_anchor_sha") != candidate:
        raise PSR01BError("PSR-01B freeze review-anchor SHA mismatch")
    repository = repository or os.environ.get("GITHUB_REPOSITORY", "")
    token = token or os.environ.get("GITHUB_TOKEN", "")
    target = _resolve_fixed_ref(repository, token, DEFAULT_REVIEW_ANCHOR_REF, opener=opener)
    if target is None:
        raise PSR01BError("PSR-01B reviewed-candidate anchor does not exist")
    if target != candidate:
        raise PSR01BError("PSR-01B reviewed-candidate anchor target mismatch")
    return {"ref": DEFAULT_REVIEW_ANCHOR_REF, "sha": target}


def expected_confirmation(candidate: str, executing_sha: str) -> str:
    return f"{CONFIRMATION_PREFIX}:{candidate}:{executing_sha}"


def assert_manual_confirmation(
    candidate: str, executing_sha: str, *,
    confirmation: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, str]:
    env = os.environ if environ is None else environ
    supplied = confirmation if confirmation is not None else env.get(
        "PSR01B_DEVELOPMENT_V1_CONFIRMATION", ""
    )
    exact = expected_confirmation(candidate, executing_sha)
    if supplied != exact:
        raise PSR01BError("exact PSR-01B manual confirmation string required")
    if env.get("GITHUB_EVENT_NAME") != "workflow_dispatch":
        raise PSR01BError("PSR-01B execution must be manually dispatched")
    actor, run_id, attempt = (
        env.get("GITHUB_ACTOR"), env.get("GITHUB_RUN_ID"), env.get("GITHUB_RUN_ATTEMPT")
    )
    if not actor or not run_id or not attempt:
        raise PSR01BError("PSR-01B manual confirmation provenance is incomplete")
    return {
        "confirmation": exact, "actor": actor, "workflow_event": "workflow_dispatch",
        "run_id": run_id, "run_attempt": attempt,
        "confirmed_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def _create_claim_tag_object(
    repository: str,
    executing_sha: str,
    token: str,
    *,
    run_id: str,
    run_attempt: str,
    actor: str,
    opener: Callable = urlopen,
) -> dict[str, str]:
    if not repository or "/" not in repository or not token:
        raise PSR01BError("repository and token required for durable-claim creation")
    if not run_id or not run_attempt or not actor:
        raise PSR01BError("PSR-01B claim run provenance is incomplete")
    record = {
        "claim_ref": DEFAULT_CLAIM_REF,
        "execution_sha": executing_sha,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "actor": actor,
    }
    message = json.dumps(record, sort_keys=True, separators=(",", ":"))
    payload = json.dumps(
        {
            "tag": DEFAULT_CLAIM_REF.removeprefix("refs/tags/"),
            "message": message,
            "object": executing_sha,
            "type": "commit",
        }
    ).encode("utf-8")
    url = f"https://api.github.com/repos/{repository}/git/tags"
    try:
        response = opener(_request(url, token, method="POST", data=payload))
        with response:
            body = response.read()
    except HTTPError as exc:
        raise PSR01BError(f"create-claim-tag failed with HTTP {exc.code}") from exc
    try:
        created = json.loads(body)
    except json.JSONDecodeError as exc:
        raise PSR01BError("invalid create-claim-tag response") from exc
    tag_sha = created.get("sha")
    obj = created.get("object", {})
    if (
        created.get("tag") != DEFAULT_CLAIM_REF.removeprefix("refs/tags/")
        or created.get("message", "").strip() != message
        or obj.get("sha") != executing_sha
        or obj.get("type") != "commit"
        or not isinstance(tag_sha, str)
        or len(tag_sha) != 40
    ):
        raise PSR01BError("GitHub returned unexpected PSR-01B claim tag object")
    return {
        "ref": DEFAULT_CLAIM_REF,
        "sha": executing_sha,
        "tag_object_sha": tag_sha,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "actor": actor,
    }


def _resolve_claim_record(
    repository: str, token: str, *, opener: Callable = urlopen
) -> dict[str, str] | None:
    tag_sha = _resolve_fixed_ref(
        repository, token, DEFAULT_CLAIM_REF, opener=opener
    )
    if tag_sha is None:
        return None
    url = f"https://api.github.com/repos/{repository}/git/tags/{tag_sha}"
    try:
        response = opener(_request(url, token))
        with response:
            body = response.read()
    except HTTPError as exc:
        raise PSR01BError(f"claim-tag lookup failed with HTTP {exc.code}") from exc
    try:
        tag = json.loads(body)
        record = json.loads(str(tag.get("message", "")).strip())
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise PSR01BError("invalid durable PSR-01B claim tag") from exc
    obj = tag.get("object", {})
    if (
        tag.get("sha") != tag_sha
        or tag.get("tag") != DEFAULT_CLAIM_REF.removeprefix("refs/tags/")
        or obj.get("type") != "commit"
        or record.get("claim_ref") != DEFAULT_CLAIM_REF
        or record.get("execution_sha") != obj.get("sha")
    ):
        raise PSR01BError("durable PSR-01B claim tag identity mismatch")
    for key in ("execution_sha", "run_id", "run_attempt", "actor"):
        if not isinstance(record.get(key), str) or not record[key]:
            raise PSR01BError("durable PSR-01B claim provenance is incomplete")
    return {
        "ref": DEFAULT_CLAIM_REF,
        "sha": record["execution_sha"],
        "tag_object_sha": tag_sha,
        "run_id": record["run_id"],
        "run_attempt": record["run_attempt"],
        "actor": record["actor"],
    }


def claim_exists(repository: str, token: str, *, opener: Callable = urlopen) -> bool:
    return _resolve_fixed_ref(repository, token, DEFAULT_CLAIM_REF, opener=opener) is not None


def assert_claim_absent(repository: str, token: str, *, opener: Callable = urlopen) -> None:
    if claim_exists(repository, token, opener=opener):
        raise PSR01BError(f"one-shot claim already exists: {DEFAULT_CLAIM_REF}")


def create_claim(
    repository: str,
    sha: str,
    token: str,
    *,
    environ: Mapping[str, str] | None = None,
    opener: Callable = urlopen,
) -> dict[str, str]:
    env = os.environ if environ is None else environ
    tag = _create_claim_tag_object(
        repository,
        sha,
        token,
        run_id=env.get("GITHUB_RUN_ID", ""),
        run_attempt=env.get("GITHUB_RUN_ATTEMPT", ""),
        actor=env.get("GITHUB_ACTOR", ""),
        opener=opener,
    )
    create_fixed_ref(
        repository,
        tag["tag_object_sha"],
        token,
        ref=DEFAULT_CLAIM_REF,
        opener=opener,
    )
    return tag


def assert_claim_environment(
    executing_sha: str, *, repository: str | None = None,
    token: str | None = None, environ: Mapping[str, str] | None = None,
    opener: Callable = urlopen,
) -> dict[str, str]:
    env = os.environ if environ is None else environ
    if env.get("PSR01B_DEVELOPMENT_V1_CLAIM_REF") != DEFAULT_CLAIM_REF:
        raise PSR01BError("forwarded one-shot claim ref is missing or incorrect")
    if env.get("PSR01B_DEVELOPMENT_V1_CLAIM_SHA") != executing_sha:
        raise PSR01BError("forwarded one-shot claim SHA mismatch")
    current_run = env.get("GITHUB_RUN_ID", "")
    current_attempt = env.get("GITHUB_RUN_ATTEMPT", "")
    current_actor = env.get("GITHUB_ACTOR", "")
    if not current_run or not current_attempt or not current_actor:
        raise PSR01BError("PSR-01B current workflow provenance is incomplete")
    if env.get("PSR01B_DEVELOPMENT_V1_CLAIM_RUN_ID") != current_run:
        raise PSR01BError("forwarded one-shot claim run ID mismatch")
    repository = repository or env.get("GITHUB_REPOSITORY", "")
    token = token or env.get("GITHUB_TOKEN", "")
    record = _resolve_claim_record(repository, token, opener=opener)
    if record is None:
        raise PSR01BError("durable PSR-01B one-shot claim does not exist")
    if record["sha"] != executing_sha:
        raise PSR01BError("durable PSR-01B one-shot claim target mismatch")
    if record["run_id"] != current_run:
        raise PSR01BError("durable PSR-01B one-shot claim belongs to another workflow run")
    if record["run_attempt"] != current_attempt:
        raise PSR01BError("durable PSR-01B one-shot claim attempt mismatch")
    if record["actor"] != current_actor:
        raise PSR01BError("durable PSR-01B one-shot claim actor mismatch")
    if env.get("PSR01B_DEVELOPMENT_V1_CLAIM_TAG_OBJECT_SHA") != record["tag_object_sha"]:
        raise PSR01BError("forwarded one-shot claim tag-object SHA mismatch")
    return record


def reservation_path(result_path: Path) -> Path:
    path = Path(result_path)
    return path.with_name(path.name + ".reservation")


def reserve_result_path(result_path: Path, *, candidate: str, executing_sha: str):
    path = Path(result_path)
    if path.exists():
        raise PSR01BError("PSR-01B result path already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    marker = reservation_path(path)
    record = {"candidate": candidate, "executing_sha": executing_sha, "result_path": str(path)}
    if marker.exists():
        try:
            if json.loads(marker.read_text(encoding="utf-8")) != record:
                raise PSR01BError("PSR-01B result path is reserved by another execution")
        except json.JSONDecodeError as exc:
            raise PSR01BError("invalid PSR-01B result reservation") from exc
        return record
    try:
        with marker.open("x", encoding="utf-8") as handle:
            json.dump(record, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise PSR01BError("cannot reserve PSR-01B result path") from exc
    return record


def assert_result_reservation(result_path: Path, *, candidate: str, executing_sha: str):
    path = Path(result_path)
    if path.exists():
        raise PSR01BError("PSR-01B result path already exists")
    try:
        record = json.loads(reservation_path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PSR01BError("PSR-01B result reservation is missing or invalid") from exc
    expected = {"candidate": candidate, "executing_sha": executing_sha, "result_path": str(path)}
    if record != expected:
        raise PSR01BError("PSR-01B result reservation identity mismatch")
    return record


def assert_preclaim_environment(
    candidate: str,
    freeze: Mapping[str, Any],
    result_path: Path,
    *,
    executing_sha: str | None = None,
    confirmation: str | None = None,
    repository: str | None = None,
    token: str | None = None,
    environ: Mapping[str, str] | None = None,
    opener: Callable = urlopen,
) -> dict[str, Any]:
    env = os.environ if environ is None else environ
    executing_sha = executing_sha or env.get("GITHUB_SHA") or _git_head_sha()
    changed = verify_execution_commit(candidate, executing_sha)
    verify_candidate_blob_contract(
        candidate, freeze.get("implementation_file_git_blob_sha1") or {}
    )
    anchor = assert_review_anchor(
        candidate, freeze, repository=repository, token=token, opener=opener
    )
    manual = assert_manual_confirmation(
        candidate, executing_sha, confirmation=confirmation, environ=env
    )
    repository = repository or env.get("GITHUB_REPOSITORY", "")
    token = token or env.get("GITHUB_TOKEN", "")
    assert_claim_absent(repository, token, opener=opener)
    reservation = reserve_result_path(
        result_path, candidate=candidate, executing_sha=executing_sha
    )
    return {
        "executing_sha": executing_sha,
        "post_candidate_changed_paths": list(changed),
        "review_anchor": anchor,
        "manual_confirmation": manual,
        "result_reservation": reservation,
    }


def assert_execution_environment(
    candidate: str,
    freeze: Mapping[str, Any],
    result_path: Path,
    *,
    executing_sha: str | None = None,
    repository: str | None = None,
    token: str | None = None,
    environ: Mapping[str, str] | None = None,
    opener: Callable = urlopen,
) -> dict[str, Any]:
    env = os.environ if environ is None else environ
    executing_sha = executing_sha or env.get("GITHUB_SHA") or _git_head_sha()
    changed = verify_execution_commit(candidate, executing_sha)
    verify_candidate_blob_contract(
        candidate, freeze.get("implementation_file_git_blob_sha1") or {}
    )
    anchor = assert_review_anchor(
        candidate, freeze, repository=repository, token=token, opener=opener
    )
    manual = assert_manual_confirmation(candidate, executing_sha, environ=env)
    claim = assert_claim_environment(
        executing_sha,
        repository=repository,
        token=token,
        environ=env,
        opener=opener,
    )
    reservation = assert_result_reservation(
        result_path, candidate=candidate, executing_sha=executing_sha
    )
    return {
        "executing_sha": executing_sha,
        "post_candidate_changed_paths": list(changed),
        "review_anchor": anchor,
        "manual_confirmation": manual,
        "claim": claim,
        "result_reservation": reservation,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "claim"))
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--sha", default=os.environ.get("GITHUB_SHA", ""))
    parser.add_argument(
        "--confirmation",
        default=os.environ.get("PSR01B_DEVELOPMENT_V1_CONFIRMATION", ""),
    )
    parser.add_argument("--result-path", default=str(DEFAULT_RESULT_PATH))
    parser.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT"))
    args = parser.parse_args()

    from .psr01b_runner import load_implementation_freeze, verify_frozen_execution_identity

    freeze = load_implementation_freeze()
    provenance = verify_frozen_execution_identity(runner_label="ubuntu-24.04")
    candidate = provenance["implementation_candidate_commit"]
    token = os.environ.get("GITHUB_TOKEN", "")
    preclaim = assert_preclaim_environment(
        candidate,
        freeze,
        Path(args.result_path),
        executing_sha=args.sha,
        confirmation=args.confirmation,
        repository=args.repository,
        token=token,
    )
    if args.action == "preflight":
        print(json.dumps(preclaim, sort_keys=True))
        print("PSR01B_DEVELOPMENT_V1_PREFLIGHT_PASS")
        return

    claim = create_claim(args.repository, args.sha, token, environ=os.environ)
    if args.github_output:
        with Path(args.github_output).open("a", encoding="utf-8") as handle:
            handle.write(f"claim_ref={claim['ref']}\n")
            handle.write(f"claim_sha={claim['sha']}\n")
            handle.write(f"claim_tag_object_sha={claim['tag_object_sha']}\n")
            handle.write(f"claim_run_id={claim['run_id']}\n")
    print(json.dumps(claim, sort_keys=True))


if __name__ == "__main__":
    main()
