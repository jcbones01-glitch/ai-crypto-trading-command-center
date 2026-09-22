"""Verification for the final AMS-DEP V2 holdout execution bundle."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from research_core.release_gate import DEFAULT_GATE

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXECUTION_MANIFEST = (
    ROOT / "research/governance/ams_dep_v2_holdout_execution_manifest_v1.json"
)

REQUIRED_SAFETY_PATHS = {
    "src/research_core/release_gate.py",
    "tests/test_ams_dep_release_gate.py",
    "src/research_core/ams_dep_v2_holdout_gate.py",
    "src/research_core/ams_dep_v2_holdout_bundle.py",
    "research/scripts/claim_ams_dep_v2_holdout.py",
    "research/scripts/run_ams_dep_v2_holdout_shard.py",
    "research/scripts/aggregate_ams_dep_v2_holdout.py",
    "tests/test_ams_dep_v2_holdout_gate.py",
    "tests/test_ams_dep_v2_holdout_claim.py",
    "tests/test_ams_dep_v2_holdout_runner.py",
    "tests/test_ams_dep_v2_holdout_aggregation.py",
    ".github/workflows/ams-dep-v2-holdout-preflight.yml",
    ".github/workflows/ams-dep-v2-frozen-holdout.yml",
}


class HoldoutBundleError(RuntimeError):
    """Raised when the final authorized execution bundle is incomplete."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_execution_manifest(
    path: Path | str = DEFAULT_EXECUTION_MANIFEST,
) -> dict:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        data = json.loads(p.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise HoldoutBundleError(f"cannot load holdout execution manifest: {p}") from exc
    if data.get("manifest_id") != "AMS-DEP-V2-HOLDOUT-EXECUTION-BUNDLE":
        raise HoldoutBundleError("unexpected holdout execution manifest identity")
    return data


def verify_execution_bundle(
    addendum: dict,
    path: Path | str = DEFAULT_EXECUTION_MANIFEST,
) -> dict:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    manifest = load_execution_manifest(p)
    if manifest.get("status") != "AUTHORIZED":
        raise HoldoutBundleError("holdout execution manifest is not AUTHORIZED")
    if addendum.get("execution_manifest_path") != str(
        p.relative_to(ROOT)
    ):
        raise HoldoutBundleError("authorized addendum points to unexpected execution manifest")

    forbidden = manifest.get("forbidden_permissions") or {}
    if not forbidden or any(value is not False for value in forbidden.values()):
        raise HoldoutBundleError("execution manifest opens or omits forbidden permissions")

    expected_manifest_sha = addendum.get("execution_manifest_sha256")
    if not expected_manifest_sha:
        raise HoldoutBundleError("authorized addendum lacks execution manifest SHA-256")
    actual_manifest_sha = sha256_file(p)
    if actual_manifest_sha != expected_manifest_sha:
        raise HoldoutBundleError("execution manifest SHA-256 mismatch")

    if manifest.get("reviewed_holdout_code_commit") != addendum.get(
        "reviewed_holdout_code_commit"
    ):
        raise HoldoutBundleError("reviewed code commit mismatch")
    if manifest.get("one_shot_claim_ref") != addendum.get("one_shot_claim_ref"):
        raise HoldoutBundleError("one-shot claim ref mismatch")

    gate_path = Path(DEFAULT_GATE)
    if sha256_file(gate_path) != manifest.get("main_gate_sha256"):
        raise HoldoutBundleError("authorized main release gate SHA-256 mismatch")

    mapping = manifest.get("safety_file_git_blob_sha1") or {}
    missing = sorted(REQUIRED_SAFETY_PATHS - set(mapping))
    if missing:
        raise HoldoutBundleError(
            "execution manifest missing safety-critical paths: " + ", ".join(missing)
        )
    for relative, expected in mapping.items():
        path_obj = ROOT / relative
        if not path_obj.exists():
            raise HoldoutBundleError(f"missing safety-critical file: {relative}")
        actual = subprocess.check_output(
            ["git", "hash-object", "--", relative],
            cwd=ROOT,
            text=True,
        ).strip()
        if actual != expected:
            raise HoldoutBundleError(f"safety-critical blob mismatch: {relative}")
    return manifest
