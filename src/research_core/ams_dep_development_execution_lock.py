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
    DEFAULT_GATE,
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
DEFAULT_CLAIM_REF = "refs/tags/ams-dep-development-execution-claimed-v1"
EXACT_CONFIRMATION = "AMS_DEP_DEVELOPMENT_EMPIRICAL_V1"


class DevelopmentExecutionError(ResearchGateError):
    """Raised when the first Development execution contract is not open."""


def _load_json(path: Path, identity_field: str, identity_value: str) -> dict:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise DevelopmentExecutionError(f"cannot load execution governance file: {path}") from exc
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


def _git_blob(relative: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "hash-object", "--", relative],
            cwd=ROOT,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise DevelopmentExecutionError(f"cannot hash frozen path: {relative}") from exc


def verify_frozen_implementation(freeze: dict) -> dict[str, str]:
    mapping = freeze.get("implementation_file_git_blob_sha1") or {}
    if not mapping:
        raise DevelopmentExecutionError("implementation freeze has no blob map")
    observed: dict[str, str] = {}
    for relative, expected in mapping.items():
        path = ROOT / relative
        if not path.exists():
            raise DevelopmentExecutionError(f"missing frozen implementation path: {relative}")
        actual = _git_blob(relative)
        observed[relative] = actual
        if actual != expected:
            raise DevelopmentExecutionError(f"frozen implementation blob mismatch: {relative}")
    return observed


def assert_development_execution_allowed(executing_sha: str | None = None) -> dict:
    """Require the main release gate and independently reviewed execution lock."""
    gate = assert_ams_dep_empirical_release_allowed()
    manifest = load_development_execution_manifest()
    freeze = load_development_implementation_freeze()

    required_manifest = (
        "development_execution_authorized",
        "independent_implementation_reviewed",
    )
    missing = [name for name in required_manifest if manifest.get(name) is not True]
    if manifest.get("status") != "AUTHORIZED_FOR_FIRST_DEVELOPMENT_EXECUTION":
        missing.append("status=AUTHORIZED_FOR_FIRST_DEVELOPMENT_EXECUTION")
    if manifest.get("first_empirical_execution_claimed") is not False:
        missing.append("first_empirical_execution_claimed=false")
    if manifest.get("first_empirical_execution_executed") is not False:
        missing.append("first_empirical_execution_executed=false")
    if manifest.get("one_shot_claim_ref") != DEFAULT_CLAIM_REF:
        missing.append("one_shot_claim_ref")
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
    if executing_sha and executing_sha != candidate:
        missing.append("executing commit equals reviewed candidate")

    protected = manifest.get("protected_permissions") or {}
    for field in (
        "validation_or_oos_access_authorized",
        "strategy_pnl_authorized",
        "paper_trading_authorized",
        "live_trading_authorized",
        "directed_cross_asset_lagged_diagnostics_authorized",
    ):
        if protected.get(field) is not False:
            missing.append(f"{field}=false")

    if gate.get("validation_or_oos_access_authorized") is not False:
        missing.append("canonical Validation/OOS gate=false")

    if missing:
        raise DevelopmentExecutionError(
            "AMS-DEP Development execution blocked; unmet execution fields: "
            + ", ".join(missing)
        )

    verify_frozen_implementation(freeze)
    return {
        "gate": gate,
        "manifest": manifest,
        "freeze": freeze,
        "executing_sha": executing_sha,
    }


def assert_claim_environment(executing_sha: str | None = None) -> dict:
    expected_sha = executing_sha or os.environ.get("GITHUB_SHA")
    ref = os.environ.get("AMS_DEP_DEVELOPMENT_CLAIM_REF")
    sha = os.environ.get("AMS_DEP_DEVELOPMENT_CLAIM_SHA")
    if ref != DEFAULT_CLAIM_REF:
        raise DevelopmentExecutionError("durable Development claim ref is not present")
    if not expected_sha or sha != expected_sha:
        raise DevelopmentExecutionError("durable Development claim SHA mismatch")
    return {"ref": ref, "sha": sha}


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
            "User-Agent": "ams-dep-development-v1-claim",
        },
    )


def claim_exists(
    repository: str,
    token: str,
    *,
    ref: str = DEFAULT_CLAIM_REF,
    opener: Callable = urlopen,
) -> bool:
    if ref != DEFAULT_CLAIM_REF:
        raise DevelopmentExecutionError("unexpected Development claim ref")
    if not repository or "/" not in repository or not token:
        raise DevelopmentExecutionError("repository and GitHub token are required")
    short_ref = ref.removeprefix("refs/")
    url = f"https://api.github.com/repos/{repository}/git/ref/{quote(short_ref, safe='/')}"
    try:
        response = opener(_request(url, token))
        with response:
            response.read()
        return True
    except HTTPError as exc:
        if exc.code == 404:
            return False
        raise DevelopmentExecutionError(
            f"GitHub claim lookup failed with HTTP {exc.code}"
        ) from exc


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
        raise DevelopmentExecutionError("unexpected Development claim ref")
    if not repository or "/" not in repository:
        raise DevelopmentExecutionError("repository must be owner/name")
    if not sha or not token:
        raise DevelopmentExecutionError("claim commit SHA and GitHub token are required")

    payload = json.dumps({"ref": ref, "sha": sha}).encode("utf-8")
    url = f"https://api.github.com/repos/{repository}/git/refs"
    try:
        response = opener(_request(url, token, method="POST", data=payload))
        with response:
            body = response.read()
    except HTTPError as exc:
        if exc.code == 422:
            raise DevelopmentExecutionError(
                f"one-shot Development claim already exists or cannot be created: {ref}"
            ) from exc
        raise DevelopmentExecutionError(
            f"GitHub create-ref failed with HTTP {exc.code}"
        ) from exc

    try:
        created = json.loads(body)
    except json.JSONDecodeError as exc:
        raise DevelopmentExecutionError("invalid GitHub create-ref response") from exc
    if created.get("ref") != ref or created.get("object", {}).get("sha") != sha:
        raise DevelopmentExecutionError("GitHub returned unexpected Development claim")
    return {"ref": ref, "sha": sha}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("preflight", "claim"))
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--sha", default=os.environ.get("GITHUB_SHA", ""))
    parser.add_argument("--confirmation", default="")
    parser.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT"))
    args = parser.parse_args()

    if args.confirmation != EXACT_CONFIRMATION:
        raise DevelopmentExecutionError("exact Development confirmation token required")

    token = os.environ.get("GITHUB_TOKEN", "")
    assert_development_execution_allowed(args.sha)
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
