"""Second lock and one-shot claim for AMS-DEP Development empirical V1."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from .release_gate import (
    ResearchGateError,
    assert_ams_dep_empirical_release_allowed,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXECUTION_MANIFEST = (
    ROOT / "research/governance/ams_dep_development_execution_manifest_v1.json"
)
DEFAULT_IMPLEMENTATION_FREEZE = (
    ROOT / "research/governance/ams_dep_development_implementation_freeze_v1.json"
)
DEFAULT_REGISTRATION = (
    ROOT / "research/governance/ams_dep_development_execution_v1.json"
)
DEFAULT_CLAIM_REF = "refs/tags/ams-dep-development-execution-claimed-v1"
DEFAULT_REVIEW_ANCHOR_REF = (
    "refs/heads/ams-dep-development-implementation-reviewed-v1"
)
EXACT_CONFIRMATION = "AMS_DEP_DEVELOPMENT_EMPIRICAL_V1"

ALLOWED_POST_CANDIDATE_PATHS = {
    "research/governance/ams_dep_development_implementation_freeze_v1.json",
    "research/governance/ams_dep_development_execution_manifest_v1.json",
    "research/governance/ams_dep_release_gate_v1.json",
}
EXPECTED_IMPLEMENTATION_PATHS = {
    ".github/workflows/ams-dep-development-empirical-v1.yml",
    "research/scripts/run_ams_dep_development_empirical_v1.py",
    "src/research_core/ams_dep_development_execution_lock.py",
    "src/research_core/ams_dep_development_source.py",
    "src/research_core/ams_dep_empirical_access.py",
    "tests/test_ams_dep_development_authorized_preflight.py",
    "tests/test_ams_dep_development_execution_lock.py",
    "tests/test_ams_dep_development_runner.py",
    "tests/test_ams_dep_development_source.py",
    "tests/test_ams_dep_development_workflow.py",
}


class DevelopmentExecutionError(ResearchGateError):
    """Raised when the first Development execution contract is not open."""


def _load_json(path: Path, identity_field: str, identity_value: str) -> dict:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise DevelopmentExecutionError(
            f"cannot load execution governance file: {path}"
        ) from exc
    if data.get(identity_field) != identity_value:
        raise DevelopmentExecutionError(f"unexpected governance identity: {path}")
    return data


def load_development_execution_manifest() -> dict:
    return _load_json(
        DEFAULT_EXECUTION_MANIFEST,
        "manifest_id",
        "AMS-DEP-DEVELOPMENT-EXECUTION-V1",
    )


def load_development_implementation_freeze() -> dict:
    return _load_json(
        DEFAULT_IMPLEMENTATION_FREEZE,
        "freeze_id",
        "AMS-DEP-DEVELOPMENT-IMPLEMENTATION-FREEZE-V1",
    )


def load_development_registration() -> dict:
    return _load_json(
        DEFAULT_REGISTRATION,
        "registration_id",
        "AMS-DEP-DEVELOPMENT-EMPIRICAL-EXECUTION-V1",
    )


def _git_blob(relative: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "hash-object", "--", relative],
            cwd=ROOT,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise DevelopmentExecutionError(
            f"cannot hash frozen path: {relative}"
        ) from exc


def verify_frozen_implementation(freeze: dict) -> dict[str, str]:
    mapping = freeze.get("implementation_file_git_blob_sha1") or {}
    if set(mapping) != EXPECTED_IMPLEMENTATION_PATHS:
        raise DevelopmentExecutionError(
            "implementation freeze path set is incomplete or altered"
        )

    registration = load_development_registration()
    approved_upstream = registration.get("pinned_upstream_git_blob_sha1") or {}
    frozen_upstream = freeze.get("pinned_upstream_git_blob_sha1") or {}
    if not approved_upstream or frozen_upstream != approved_upstream:
        raise DevelopmentExecutionError(
            "frozen upstream pin map differs from approved registration"
        )

    spec_path = registration.get("specification_path")
    spec_blob = registration.get("specification_git_blob_sha1")
    if not spec_path or _git_blob(spec_path) != spec_blob:
        raise DevelopmentExecutionError(
            "approved Development specification blob mismatch"
        )

    observed: dict[str, str] = {}
    for relative, expected in mapping.items():
        path = ROOT / relative
        if not path.exists():
            raise DevelopmentExecutionError(
                f"missing frozen implementation path: {relative}"
            )
        actual = _git_blob(relative)
        observed[relative] = actual
        if actual != expected:
            raise DevelopmentExecutionError(
                f"frozen implementation blob mismatch: {relative}"
            )

    for relative, expected in approved_upstream.items():
        path = ROOT / relative
        if not path.exists():
            raise DevelopmentExecutionError(
                f"missing frozen upstream path: {relative}"
            )
        if _git_blob(relative) != expected:
            raise DevelopmentExecutionError(
                f"frozen upstream blob mismatch: {relative}"
            )
    return observed


def _verify_execution_commit(
    candidate: str,
    executing_sha: str,
) -> tuple[str, ...]:
    if executing_sha == candidate:
        return ()
    try:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", candidate, executing_sha],
            cwd=ROOT,
            check=False,
        )
    except OSError as exc:
        raise DevelopmentExecutionError(
            "cannot verify execution ancestry"
        ) from exc
    if ancestor.returncode != 0:
        raise DevelopmentExecutionError(
            "executing commit is not descended from the reviewed implementation candidate"
        )
    try:
        changed = tuple(
            value
            for value in subprocess.check_output(
                ["git", "diff", "--name-only", candidate, executing_sha],
                cwd=ROOT,
                text=True,
            ).splitlines()
            if value
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise DevelopmentExecutionError(
            "cannot verify post-candidate changes"
        ) from exc
    forbidden = sorted(set(changed) - ALLOWED_POST_CANDIDATE_PATHS)
    if forbidden:
        raise DevelopmentExecutionError(
            "result-affecting or unapproved post-candidate path changed: "
            + ", ".join(forbidden)
        )
    return changed


def _request(
    url: str,
    token: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
) -> Request:
    return Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ams-dep-development-v1-governance",
        },
    )


def _resolve_fixed_ref(
    repository: str,
    token: str,
    ref: str,
    *,
    opener: Callable = urlopen,
) -> str | None:
    if ref not in {DEFAULT_CLAIM_REF, DEFAULT_REVIEW_ANCHOR_REF}:
        raise DevelopmentExecutionError("unexpected fixed governance ref")
    if not repository or "/" not in repository or not token:
        raise DevelopmentExecutionError(
            "repository and GitHub token are required for durable-ref verification"
        )

    short_ref = ref.removeprefix("refs/")
    url = (
        f"https://api.github.com/repos/{repository}/git/ref/"
        f"{quote(short_ref, safe='/')}"
    )
    try:
        response = opener(_request(url, token))
        with response:
            body = response.read()
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise DevelopmentExecutionError(
            f"GitHub durable-ref lookup failed with HTTP {exc.code}"
        ) from exc

    try:
        resolved = json.loads(body)
    except json.JSONDecodeError as exc:
        raise DevelopmentExecutionError(
            "invalid GitHub durable-ref response"
        ) from exc
    if resolved.get("ref") != ref:
        raise DevelopmentExecutionError(
            "GitHub returned unexpected durable ref"
        )
    target = resolved.get("object", {}).get("sha")
    if not target:
        raise DevelopmentExecutionError(
            "GitHub durable ref lacks target SHA"
        )
    return str(target)


def create_fixed_ref(
    repository: str,
    sha: str,
    token: str,
    *,
    ref: str,
    opener: Callable = urlopen,
) -> dict:
    """Atomically create one of the two fixed governance refs.

    There is intentionally no update/delete/repoint helper.
    """
    if ref not in {DEFAULT_CLAIM_REF, DEFAULT_REVIEW_ANCHOR_REF}:
        raise DevelopmentExecutionError("unexpected fixed governance ref")
    if not repository or "/" not in repository:
        raise DevelopmentExecutionError("repository must be owner/name")
    if not sha or not token:
        raise DevelopmentExecutionError(
            "fixed-ref commit SHA and GitHub token are required"
        )

    payload = json.dumps({"ref": ref, "sha": sha}).encode("utf-8")
    url = f"https://api.github.com/repos/{repository}/git/refs"
    try:
        response = opener(_request(url, token, method="POST", data=payload))
        with response:
            body = response.read()
    except HTTPError as exc:
        if exc.code == 422:
            raise DevelopmentExecutionError(
                f"fixed governance ref already exists or cannot be created: {ref}"
            ) from exc
        raise DevelopmentExecutionError(
            f"GitHub create-ref failed with HTTP {exc.code}"
        ) from exc

    try:
        created = json.loads(body)
    except json.JSONDecodeError as exc:
        raise DevelopmentExecutionError(
            "invalid GitHub create-ref response"
        ) from exc
    if created.get("ref") != ref or created.get("object", {}).get("sha") != sha:
        raise DevelopmentExecutionError(
            "GitHub returned unexpected fixed governance ref"
        )
    return {"ref": ref, "sha": sha}


def assert_review_anchor(
    candidate: str,
    *,
    repository: str | None = None,
    token: str | None = None,
    opener: Callable = urlopen,
) -> dict:
    repository = repository or os.environ.get("GITHUB_REPOSITORY", "")
    token = token or os.environ.get("GITHUB_TOKEN", "")
    target = _resolve_fixed_ref(
        repository,
        token,
        DEFAULT_REVIEW_ANCHOR_REF,
        opener=opener,
    )
    if target is None:
        raise DevelopmentExecutionError(
            "independent-review candidate anchor does not exist"
        )
    if target != candidate:
        raise DevelopmentExecutionError(
            "independent-review candidate anchor target mismatch"
        )
    return {"ref": DEFAULT_REVIEW_ANCHOR_REF, "sha": target}


def assert_development_execution_allowed(
    executing_sha: str | None = None,
    *,
    repository: str | None = None,
    token: str | None = None,
    ref_opener: Callable = urlopen,
) -> dict:
    """Require release, reviewed-candidate anchor, pins, and downstream locks."""
    gate = assert_ams_dep_empirical_release_allowed()
    manifest = load_development_execution_manifest()
    freeze = load_development_implementation_freeze()

    required_manifest = (
        "development_execution_authorized",
        "independent_implementation_reviewed",
    )
    missing = [
        name for name in required_manifest if manifest.get(name) is not True
    ]
    if manifest.get("status") != "AUTHORIZED_FOR_FIRST_DEVELOPMENT_EXECUTION":
        missing.append("status=AUTHORIZED_FOR_FIRST_DEVELOPMENT_EXECUTION")
    if manifest.get("first_empirical_execution_claimed") is not False:
        missing.append("first_empirical_execution_claimed=false")
    if manifest.get("first_empirical_execution_executed") is not False:
        missing.append("first_empirical_execution_executed=false")
    if manifest.get("one_shot_claim_ref") != DEFAULT_CLAIM_REF:
        missing.append("one_shot_claim_ref")
    if manifest.get("review_anchor_ref") != DEFAULT_REVIEW_ANCHOR_REF:
        missing.append("review_anchor_ref")
    if manifest.get("confirmation_token") != EXACT_CONFIRMATION:
        missing.append("confirmation_token")

    candidate = manifest.get("implementation_candidate_commit")
    reviewed = manifest.get("reviewed_implementation_commit")
    freeze_candidate = freeze.get("implementation_candidate_commit")
    if not candidate or reviewed != candidate or freeze_candidate != candidate:
        missing.append("reviewed implementation candidate equality")

    if freeze.get("status") != "FROZEN_FOR_INDEPENDENT_REVIEW":
        missing.append("freeze status")
    if freeze.get("independent_review_required") is not True:
        missing.append("freeze independent_review_required=true")

    if executing_sha is None:
        executing_sha = os.environ.get("GITHUB_SHA")
    if not executing_sha:
        missing.append("executing commit SHA")

    protected = manifest.get("protected_permissions") or {}
    for field in (
        "validation_or_oos_access_authorized",
        "strategy_pnl_authorized",
        "paper_trading_authorized",
        "live_trading_authorized",
        "directed_cross_asset_lagged_diagnostics_authorized",
    ):
        if protected.get(field) is not False:
            missing.append(f"manifest {field}=false")

    for field in (
        "validation_or_oos_access_authorized",
        "strategy_pnl_authorized",
        "paper_trading_authorized",
        "live_trading_authorized",
    ):
        if gate.get(field) is not False:
            missing.append(f"canonical {field}=false")

    if missing:
        raise DevelopmentExecutionError(
            "AMS-DEP Development execution blocked; unmet execution fields: "
            + ", ".join(missing)
        )

    verify_frozen_implementation(freeze)
    changed = _verify_execution_commit(candidate, executing_sha)
    anchor = assert_review_anchor(
        candidate,
        repository=repository,
        token=token,
        opener=ref_opener,
    )
    return {
        "gate": gate,
        "manifest": manifest,
        "freeze": freeze,
        "review_anchor": anchor,
        "executing_sha": executing_sha,
        "post_candidate_changed_paths": list(changed),
    }


def claim_exists(
    repository: str,
    token: str,
    *,
    ref: str = DEFAULT_CLAIM_REF,
    opener: Callable = urlopen,
) -> bool:
    if ref != DEFAULT_CLAIM_REF:
        raise DevelopmentExecutionError(
            "unexpected Development claim ref"
        )
    return (
        _resolve_fixed_ref(
            repository,
            token,
            ref,
            opener=opener,
        )
        is not None
    )


def assert_claim_absent(
    repository: str,
    token: str,
    *,
    opener: Callable = urlopen,
) -> None:
    if claim_exists(repository, token, opener=opener):
        raise DevelopmentExecutionError(
            f"first Development execution claim already exists: {DEFAULT_CLAIM_REF}"
        )


def create_claim(
    repository: str,
    sha: str,
    token: str,
    *,
    ref: str = DEFAULT_CLAIM_REF,
    opener: Callable = urlopen,
) -> dict:
    if ref != DEFAULT_CLAIM_REF:
        raise DevelopmentExecutionError(
            "unexpected Development claim ref"
        )
    return create_fixed_ref(
        repository,
        sha,
        token,
        ref=ref,
        opener=opener,
    )


def assert_claim_environment(
    executing_sha: str | None = None,
    *,
    repository: str | None = None,
    token: str | None = None,
    opener: Callable = urlopen,
) -> dict:
    """Verify forwarded claim values and the actual durable GitHub ref."""
    expected_sha = executing_sha or os.environ.get("GITHUB_SHA")
    forwarded_ref = os.environ.get("AMS_DEP_DEVELOPMENT_CLAIM_REF")
    forwarded_sha = os.environ.get("AMS_DEP_DEVELOPMENT_CLAIM_SHA")
    if forwarded_ref != DEFAULT_CLAIM_REF:
        raise DevelopmentExecutionError(
            "forwarded Development claim ref is missing or incorrect"
        )
    if not expected_sha or forwarded_sha != expected_sha:
        raise DevelopmentExecutionError(
            "forwarded Development claim SHA mismatch"
        )

    repository = repository or os.environ.get("GITHUB_REPOSITORY", "")
    token = token or os.environ.get("GITHUB_TOKEN", "")
    durable_sha = _resolve_fixed_ref(
        repository,
        token,
        DEFAULT_CLAIM_REF,
        opener=opener,
    )
    if durable_sha is None:
        raise DevelopmentExecutionError(
            "durable Development claim does not exist"
        )
    if durable_sha != expected_sha:
        raise DevelopmentExecutionError(
            "durable Development claim target mismatch"
        )
    return {"ref": DEFAULT_CLAIM_REF, "sha": durable_sha}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "claim"))
    parser.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY", ""),
    )
    parser.add_argument("--sha", default=os.environ.get("GITHUB_SHA", ""))
    parser.add_argument("--confirmation", default="")
    parser.add_argument(
        "--github-output",
        default=os.environ.get("GITHUB_OUTPUT"),
    )
    args = parser.parse_args()

    if args.confirmation != EXACT_CONFIRMATION:
        raise DevelopmentExecutionError(
            "exact Development confirmation token required"
        )

    token = os.environ.get("GITHUB_TOKEN", "")
    assert_development_execution_allowed(
        args.sha,
        repository=args.repository,
        token=token,
    )
    if args.action == "preflight":
        assert_claim_absent(args.repository, token)
        print("AMS_DEP_DEVELOPMENT_PREFLIGHT_PASS")
        return

    claim = create_claim(args.repository, args.sha, token)
    if args.github_output:
        with Path(args.github_output).open("a", encoding="utf-8") as handle:
            handle.write(f"claim_ref={claim['ref']}\n")
            handle.write(f"claim_sha={claim['sha']}\n")
    print(json.dumps(claim, sort_keys=True))


if __name__ == "__main__":
    main()
