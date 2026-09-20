"""Build the final AMS-DEP V2 holdout execution manifest after authorization.

This script performs no holdout simulation and consumes no RNG. It is intended
for the governance-only authorization transition after independent approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from research_core.ams_dep_v2_holdout_bundle import REQUIRED_SAFETY_PATHS
from research_core.ams_dep_v2_holdout_gate import load_holdout_addendum
from research_core.release_gate import DEFAULT_GATE, load_ams_dep_release_gate

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = (
    ROOT / "research/governance/ams_dep_v2_holdout_execution_manifest_v1.json"
)


def _blob(relative: str) -> str:
    return subprocess.check_output(
        ["git", "hash-object", "--", relative],
        cwd=ROOT,
        text=True,
    ).strip()


def build_manifest() -> dict:
    gate = load_ams_dep_release_gate()
    addendum = load_holdout_addendum()
    if gate.get("v2_synthetic_calibration_passed") is not True:
        raise RuntimeError("cannot build execution manifest before calibration PASS")
    if gate.get("v2_holdout_execution_authorized") is not True:
        raise RuntimeError("main holdout gate is not authorized")
    if addendum.get("status") != "AUTHORIZED":
        raise RuntimeError("holdout addendum is not AUTHORIZED")
    if addendum.get("holdout_path_independently_reviewed") is not True:
        raise RuntimeError("holdout path lacks independent approval")
    if addendum.get("explicit_holdout_execution_authorized") is not True:
        raise RuntimeError("holdout execution is not explicitly authorized")
    reviewed = addendum.get("reviewed_holdout_code_commit")
    if not reviewed:
        raise RuntimeError("reviewed holdout code commit missing")
    claim_ref = addendum.get("one_shot_claim_ref")
    if not claim_ref:
        raise RuntimeError("one-shot claim ref missing")

    return {
        "manifest_id": "AMS-DEP-V2-HOLDOUT-EXECUTION-BUNDLE",
        "version": 1,
        "status": "AUTHORIZED",
        "review_issue": 54,
        "reviewed_holdout_code_commit": reviewed,
        "main_gate_sha256": hashlib.sha256(Path(DEFAULT_GATE).read_bytes()).hexdigest(),
        "one_shot_claim_ref": claim_ref,
        "safety_file_git_blob_sha1": {
            path: _blob(path) for path in sorted(REQUIRED_SAFETY_PATHS)
        },
        "forbidden_permissions": {
            "development_market_data_execution_authorized": gate.get(
                "development_market_data_execution_authorized"
            ),
            "validation_or_oos_access_authorized": gate.get(
                "validation_or_oos_access_authorized"
            ),
            "strategy_pnl_authorized": gate.get("strategy_pnl_authorized"),
            "paper_trading_authorized": gate.get("paper_trading_authorized"),
            "live_trading_authorized": gate.get("live_trading_authorized"),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    manifest = build_manifest()
    if any(manifest["forbidden_permissions"].values()):
        raise RuntimeError("forbidden empirical/trading permission opened")
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(hashlib.sha256(args.output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
