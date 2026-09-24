"""Second lock and one-shot claim for AMS-DEP Development empirical V2."""
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

from .release_gate import ResearchGateError, assert_ams_dep_empirical_release_allowed

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXECUTION_MANIFEST = ROOT / "research/governance/ams_dep_development_execution_manifest_v2.json"
DEFAULT_IMPLEMENTATION_FREEZE = ROOT / "research/governance/ams_dep_development_implementation_freeze_v2.json"
DEFAULT_REGISTRATION = ROOT / "research/governance/ams_dep_development_execution_v2.json"
DEFAULT_CLAIM_REF = "refs/tags/ams-dep-development-execution-claimed-v2"
DEFAULT_REVIEW_ANCHOR_REF = "refs/heads/ams-dep-development-implementation-reviewed-v2"
EXACT_CONFIRMATION = "AMS_DEP_DEVELOPMENT_EMPIRICAL_V2"

ALLOWED_POST_CANDIDATE_PATHS = {
    "research/governance/ams_dep_development_implementation_freeze_v2.json",
    "research/governance/ams_dep_development_execution_manifest_v2.json",
    "research/governance/ams_dep_release_gate_v1.json",
}

EXPECTED_IMPLEMENTATION_PATHS = {
    ".github/workflows/ams-dep-development-empirical-v2.yml",
    "research/scripts/run_ams_dep_development_empirical_v2.py",
    "src/research_core/ams_dep_treatment_aware_normalization_v2.py",
    "src/research_core/ams_dep_development_source_v2.py",
    "src/research_core/ams_dep_empirical_access_v2.py",
    "src/research_core/ams_dep_development_execution_lock_v2.py",
    "tests/test_ams_dep_development_v2_authorized_preflight.py",
    "tests/test_ams_dep_development_v2_execution_lock.py",
    "tests/test_ams_dep_development_v2_normalization.py",
    "tests/test_ams_dep_development_v2_runner.py",
    "tests/test_ams_dep_development_v2_source.py",
    "tests/test_ams_dep_development_v2_workflow.py",
}


class DevelopmentExecutionV2Error(ResearchGateError):
    """Raised when the Development V2 execution contract is not open."""


def _load_json(path: Path, identity_field: str, identity_value: str) -> dict:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise DevelopmentExecutionV2Error(
            f"cannot load V2 execution governance file: {path}"
        ) from exc
    if data.get(identity_field) != identity_value:
        raise DevelopmentExecutionV2Error(
            f"unexpected V2 governance identity: {path}"
        )
    return data


def load_development_execution_manifest() -> dict:
    return _load_json(
        DEFAULT_EXECUTION_MANIFEST,
        "manifest_id",
        "AMS-DEP-DEVELOPMENT-EXECUTION-V2",
    )


def load_development_implementation_freeze() -> dict:
    return _load_json(
        DEFAULT_IMPLEMENTATION_FREEZE,
        "freeze_id",
        "AMS-DEP-DEVELOPMENT-IMPLEMENTATION-FREEZE-V2",
    )


def load_development_registration() -> dict:
    return _load_json(
        DEFAULT_REGISTRATION,
        "registration_id",
        "AMS-DEP-DEVELOPMENT-EMPIRICAL-EXECUTION-V2",
    )


def _git_blob(relative: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "hash-object", "--", relative],
            cwd=ROOT,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise DevelopmentExecutionV2Error(
            f"cannot hash frozen V2 path: {relative}"
        ) from exc


def verify_frozen_implementation(freeze: dict) -> dict[str, str]:
    mapping = freeze.get("implementation_file_git_blob_sha1") or {}
    if set(mapping) != EXPECTED_IMPLEMENTATION_PATHS:
        raise DevelopmentExecutionV2Error(
            "V2 implementation freeze path set is incomplete or altered"
        )

    registration = load_development_registration()
    approved_upstream = registration.get("pinned_upstream_git_blob_sha1") or {}
    frozen_upstream = freeze.get("pinned_upstream_git_blob_sha1") or {}
    if not approved_upstream or frozen_upstream != approved_upstream:
        raise DevelopmentExecutionV2Error(
            "V2 frozen upstream pin map differs from approved registration"
        )

    spec_path = registration.get("specification_path")
    spec_blob = registration.get("specification_git_blob_sha1")
    if not spec_path or _git_blob(spec_path) != spec_blob:
        raise DevelopmentExecutionV2Error(
            "approved V2 specification blob mismatch"
        )

    observed: dict[str, str] = {}
    for relative, expected in mapping.items():
        if not (ROOT / relative).exists():
            raise DevelopmentExecutionV2Error(
                f"missing frozen V2 implementation path: {relative}"
            )
        actual = _git_blob(relative)
        observed[relative] = actual
        if actual != expected:
            raise DevelopmentExecutionV2Error(
                f"frozen V2 implementation blob mismatch: {relative}"
            )

    for relative, expected in approved_upstream.items():
        if not (ROOT / relative).exists():
            raise DevelopmentExecutionV2Error(
                f"missing frozen V2 upstream path: {relative}"
            )
        if _git_blob(relative) != expected:
            raise DevelopmentExecutionV2Error(
                f"frozen V2 upstream blob mismatch: {relative}"
            )
    return observed


def _verify_execution_commit(candidate: str, executing_sha: str) -> tuple[str, ...]:
    if executing_sha == candidate:
        return ()
    try:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", candidate, executing_sha],
            cwd=ROOT,
            check=False,
        )
    except OSError as exc:
        raise DevelopmentExecutionV2Error("cannot verify V2 execution ancestry") from exc
    if ancestor.returncode != 0:
        raise DevelopmentExecutionV2Error(
            "V2 executing commit is not descended from reviewed candidate"
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
        raise DevelopmentExecutionV2Error(
            "cannot verify V2 post-candidate changes"
        ) from exc
    forbidden = sorted(set(changed) - ALLOWED_POST_CANDIDATE_PATHS)
    if forbidden:
        raise DevelopmentExecutionV2Error(
            "V2 result-affecting or unapproved post-candidate path changed: "
            + ", ".join(forbidden)
        )
    return changed


def _request(url: str, token: str, *, method: str = "GET", data: bytes | None = None) -> Request:
    return Request(
        url,
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ams-dep-development-v2-governance",
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
        raise DevelopmentExecutionV2Error("unexpected V2 fixed governance ref")
    if not repository or "/" not in repository or not token:
        raise DevelopmentExecutionV2Error(
            "repository and GitHub token are required for V2 durable-ref verification"
        )
    short_ref = ref.removeprefix("refs/")
    url = f"https://api.github.com/repos/{repository}/git/ref/{quote(short_ref, safe='/')}"
    try:
        response = opener(_request(url, token))
        with response:
            body = response.read()
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise DevelopmentExecutionV2Error(
            f"GitHub V2 durable-ref lookup failed with HTTP {exc.code}"
        ) from exc
    try:
        resolved = json.loads(body)
    except json.JSONDecodeError as exc:
        raise DevelopmentExecutionV2Error(
            "invalid GitHub V2 durable-ref response"
        ) from exc
    if resolved.get("ref") != ref:
        raise DevelopmentExecutionV2Error("GitHub returned unexpected V2 durable ref")
    target = resolved.get("object", {}).get("sha")
    if not target:
        raise DevelopmentExecutionV2Error("GitHub V2 durable ref lacks target SHA")
    return str(target)


def create_fixed_ref(
    repository: str,
    sha: str,
    token: str,
    *,
    ref: str,
    opener: Callable = urlopen,
) -> dict:
    """Atomically create a fixed V2 governance ref; no update/delete helper exists."""
    if ref not in {DEFAULT_CLAIM_REF, DEFAULT_REVIEW_ANCHOR_REF}:
        raise DevelopmentExecutionV2Error("unexpected V2 fixed governance ref")
    if not repository or "/" not in repository or not sha or not token:
        raise DevelopmentExecutionV2Error(
            "repository, SHA, and token are required for V2 fixed-ref creation"
        )
    payload = json.dumps({"ref": ref, "sha": sha}).encode("utf-8")
    url = f"https://api.github.com/repos/{repository}/git/refs"
    try:
        response = opener(_request(url, token, method="POST", data=payload))
        with response:
            body = response.read()
    except HTTPError as exc:
        if exc.code == 422:
            raise DevelopmentExecutionV2Error(
                f"V2 fixed governance ref already exists or cannot be created: {ref}"
            ) from exc
        raise DevelopmentExecutionV2Error(
            f"GitHub V2 create-ref failed with HTTP {exc.code}"
        ) from exc
    try:
        created = json.loads(body)
    except json.JSONDecodeError as exc:
        raise DevelopmentExecutionV2Error(
            "invalid GitHub V2 create-ref response"
        ) from exc
    if created.get("ref") != ref or created.get("object", {}).get("sha") != sha:
        raise DevelopmentExecutionV2Error(
            "GitHub returned unexpected V2 fixed governance ref"
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
        repository, token, DEFAULT_REVIEW_ANCHOR_REF, opener=opener
    )
    if target is None:
        raise DevelopmentExecutionV2Error(
            "V2 independent-review candidate anchor does not exist"
        )
    if target != candidate:
        raise DevelopmentExecutionV2Error(
            "V2 independent-review candidate anchor target mismatch"
        )
    return {"ref": DEFAULT_REVIEW_ANCHOR_REF, "sha": target}


def assert_development_execution_allowed(
    executing_sha: str | None = None,
    *,
    repository: str | None = None,
    token: str | None = None,
    ref_opener: Callable = urlopen,
) -> dict:
    gate = assert_ams_dep_empirical_release_allowed()
    manifest = load_development_execution_manifest()
    freeze = load_development_implementation_freeze()

    missing: list[str] = []
    if manifest.get("status") != "AUTHORIZED_FOR_FIRST_DEVELOPMENT_V2_EXECUTION":
        missing.append("status=AUTHORIZED_FOR_FIRST_DEVELOPMENT_V2_EXECUTION")
    for field in ("development_execution_authorized", "independent_implementation_reviewed"):
        if manifest.get(field) is not True:
            missing.append(f"{field}=true")
    if manifest.get("first_empirical_execution_claimed") is not False:
        missing.append("first_empirical_execution_claimed=false")
    if manifest.get("first_empirical_execution_executed") is not False:
        missing.append("first_empirical_execution_executed=false")
    if manifest.get("one_shot_claim_ref") != DEFAULT_CLAIM_REF:
        missing.append("V2 one_shot_claim_ref")
    if manifest.get("review_anchor_ref") != DEFAULT_REVIEW_ANCHOR_REF:
        missing.append("V2 review_anchor_ref")
    if manifest.get("confirmation_token") != EXACT_CONFIRMATION:
        missing.append("V2 confirmation_token")

    candidate = manifest.get("implementation_candidate_commit")
    reviewed = manifest.get("reviewed_implementation_commit")
    freeze_candidate = freeze.get("implementation_candidate_commit")
    freeze_reviewed = freeze.get("reviewed_implementation_commit")
    if not candidate:
        missing.append("V2 implementation candidate")
    if reviewed != candidate or freeze_candidate != candidate or freeze_reviewed != candidate:
        missing.append("V2 reviewed candidate equality")

    if freeze.get("status") != "FROZEN_FOR_INDEPENDENT_REVIEW":
        missing.append("V2 freeze status")
    if freeze.get("independent_review_required") is not True:
        missing.append("V2 freeze independent_review_required=true")
    if freeze.get("independent_implementation_reviewed") is not True:
        missing.append("V2 freeze independent_implementation_reviewed=true")
    if freeze.get("review_anchor_ref") != DEFAULT_REVIEW_ANCHOR_REF:
        missing.append("V2 freeze review_anchor_ref")

    if executing_sha is None:
        executing_sha = os.environ.get("GITHUB_SHA")
    if not executing_sha:
        missing.append("V2 executing commit SHA")

    protected = manifest.get("protected_permissions") or {}
    for field in (
        "validation_or_oos_access_authorized",
        "strategy_pnl_authorized",
        "paper_trading_authorized",
        "live_trading_authorized",
        "directed_cross_asset_lagged_diagnostics_authorized",
    ):
        if protected.get(field) is not False:
            missing.append(f"V2 manifest {field}=false")

    for field in (
        "validation_or_oos_access_authorized",
        "strategy_pnl_authorized",
        "paper_trading_authorized",
        "live_trading_authorized",
    ):
        if gate.get(field) is not False:
            missing.append(f"canonical {field}=false")

    if missing:
        raise DevelopmentExecutionV2Error(
            "AMS-DEP Development V2 execution blocked; unmet fields: "
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
        raise DevelopmentExecutionV2Error("unexpected Development V2 claim ref")
    return _resolve_fixed_ref(repository, token, ref, opener=opener) is not None


def assert_claim_absent(repository: str, token: str, *, opener: Callable = urlopen) -> None:
    if claim_exists(repository, token, opener=opener):
        raise DevelopmentExecutionV2Error(
            f"first Development V2 execution claim already exists: {DEFAULT_CLAIM_REF}"
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
        raise DevelopmentExecutionV2Error("unexpected Development V2 claim ref")
    return create_fixed_ref(repository, sha, token, ref=ref, opener=opener)


def assert_claim_environment(
    executing_sha: str | None = None,
    *,
    repository: str | None = None,
    token: str | None = None,
    opener: Callable = urlopen,
) -> dict:
    expected_sha = executing_sha or os.environ.get("GITHUB_SHA")
    forwarded_ref = os.environ.get("AMS_DEP_DEVELOPMENT_V2_CLAIM_REF")
    forwarded_sha = os.environ.get("AMS_DEP_DEVELOPMENT_V2_CLAIM_SHA")
    if forwarded_ref != DEFAULT_CLAIM_REF:
        raise DevelopmentExecutionV2Error(
            "forwarded Development V2 claim ref is missing or incorrect"
        )
    if not expected_sha or forwarded_sha != expected_sha:
        raise DevelopmentExecutionV2Error(
            "forwarded Development V2 claim SHA mismatch"
        )
    repository = repository or os.environ.get("GITHUB_REPOSITORY", "")
    token = token or os.environ.get("GITHUB_TOKEN", "")
    durable_sha = _resolve_fixed_ref(
        repository, token, DEFAULT_CLAIM_REF, opener=opener
    )
    if durable_sha is None:
        raise DevelopmentExecutionV2Error(
            "durable Development V2 claim does not exist"
        )
    if durable_sha != expected_sha:
        raise DevelopmentExecutionV2Error(
            "durable Development V2 claim target mismatch"
        )
    return {"ref": DEFAULT_CLAIM_REF, "sha": durable_sha}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "claim"))
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--sha", default=os.environ.get("GITHUB_SHA", ""))
    parser.add_argument("--confirmation", default="")
    parser.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT"))
    args = parser.parse_args()

    if args.confirmation != EXACT_CONFIRMATION:
        raise DevelopmentExecutionV2Error(
            "exact Development V2 confirmation token required"
        )

    token = os.environ.get("GITHUB_TOKEN", "")
    assert_development_execution_allowed(
        args.sha,
        repository=args.repository,
        token=token,
    )
    if args.action == "preflight":
        assert_claim_absent(args.repository, token)
        print("AMS_DEP_DEVELOPMENT_V2_PREFLIGHT_PASS")
        return

    claim = create_claim(args.repository, args.sha, token)
    if args.github_output:
        with Path(args.github_output).open("a", encoding="utf-8") as handle:
            handle.write(f"claim_ref={claim['ref']}\n")
            handle.write(f"claim_sha={claim['sha']}\n")
    print(json.dumps(claim, sort_keys=True))


if __name__ == "__main__":
    main()
