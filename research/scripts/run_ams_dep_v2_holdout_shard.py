"""Guarded frozen AMS-DEP V2 reserved-holdout shard runner.

This is an additive orchestration path. It does not modify the frozen V2
scientific implementation. The reserved holdout seed namespace is touched only
after BOTH the main release gate and the separate holdout execution addendum
authorize execution.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import platform
import subprocess
from pathlib import Path

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_name] = "1"

import numpy as np
import scipy

from research_core.ams_dep_v2_holdout_bundle import verify_execution_bundle
from research_core.ams_dep_v2_holdout_gate import (
    DEFAULT_HOLDOUT_ADDENDUM,
    assert_ams_dep_v2_holdout_path_allowed,
)
from research_core.ams_dep_v2_synthetic import ASSETS, simulate_case
from research_core.dependence_statistics import InferenceError, primary_design
from research_core.dependent_wild_bootstrap_v2 import (
    BOOTSTRAP_DRAWS,
    FixedOLS,
    ParzenGeometry,
    bootstrap_p_value,
    restricted_components,
    wald,
)

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "research/experiments/ams_dep_synthetic_core_v2.json"
MANIFEST = ROOT / "research/governance/ams_dep_v2_freeze_manifest.json"
OUTDIR = ROOT / "research/experiments/ams_dep_v2_holdout_shards"
SHARD_COUNT = 128
HYPOTHESES = ("DEP", "TIME", "STATE")
_ACTIVE_CONTEXT = None


class _HoldoutExecutionContext:
    __slots__ = ("claim_ref", "claim_sha")

    def __init__(self, claim_ref: str, claim_sha: str):
        # Construction alone never grants authority.  Only _activate_context(),
        # reached after full gate/bundle/claim verification, can make a context
        # active for reserved holdout computation.
        self.claim_ref = claim_ref
        self.claim_sha = claim_sha


def _activate_context(claim_ref: str, claim_sha: str) -> _HoldoutExecutionContext:
    global _ACTIVE_CONTEXT
    context = _HoldoutExecutionContext(claim_ref, claim_sha)
    _ACTIVE_CONTEXT = context
    return context


def _require_context(context: object) -> _HoldoutExecutionContext:
    if (
        not isinstance(context, _HoldoutExecutionContext)
        or context is not _ACTIVE_CONTEXT
    ):
        raise RuntimeError(
            "reserved holdout computation requires active verified authorization context"
        )
    return context


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _task_index(
    dgp_index: int,
    outer_index: int,
    asset_index: int,
    hypothesis_index: int,
    outer_replications: int,
) -> int:
    return (
        ((dgp_index * outer_replications) + outer_index) * 2 + asset_index
    ) * 3 + hypothesis_index


def _coordinate_line(
    dgp_index: int,
    outer_index: int,
    asset_index: int,
    hypothesis_index: int,
) -> bytes:
    return (
        f"{dgp_index}|{outer_index}|{asset_index}|{hypothesis_index}\n"
    ).encode("ascii")


def _seed_namespace(config: dict) -> dict:
    """Return/validate registered roots without instantiating any RNG."""
    data_cal = int(config["data_roots"]["calibration"])
    data_hold = int(config["data_roots"]["holdout"])
    boot_eng = int(config["bootstrap_roots"]["engineering"])
    boot_cal = int(config["bootstrap_roots"]["calibration"])
    boot_hold = int(config["bootstrap_roots"]["holdout"])
    if data_cal == data_hold:
        raise RuntimeError("calibration and holdout data roots must differ")
    if len({boot_eng, boot_cal, boot_hold}) != 3:
        raise RuntimeError("engineering/calibration/holdout bootstrap roots must differ")
    return {
        "data_calibration": data_cal,
        "data_holdout": data_hold,
        "bootstrap_engineering": boot_eng,
        "bootstrap_calibration": boot_cal,
        "bootstrap_holdout": boot_hold,
    }


def _verify_git_blob_hashes(mapping: dict, label: str) -> None:
    if not mapping:
        raise RuntimeError(f"{label} file hash map is empty")
    for relative, expected in mapping.items():
        path = ROOT / relative
        if not path.exists():
            raise RuntimeError(f"missing {label} file: {relative}")
        actual = subprocess.check_output(
            ["git", "hash-object", "--", relative],
            cwd=ROOT,
            text=True,
        ).strip()
        if actual != expected:
            raise RuntimeError(f"{label} file hash mismatch: {relative}")


def _verify_authority() -> tuple[dict, dict, dict, dict, dict]:
    """Verify both gates, frozen provenance and final execution bundle.

    This function performs no holdout RNG work and does not require the one-shot
    claim to exist yet. It is used by the manual workflow immediately before
    atomically creating that claim.
    """
    gate, addendum = assert_ams_dep_v2_holdout_path_allowed()

    manifest = json.loads(MANIFEST.read_text())
    if manifest.get("status") != "FROZEN_FOR_SYNTHETIC_CALIBRATION":
        raise RuntimeError("unexpected V2 freeze-manifest status")
    _verify_git_blob_hashes(manifest.get("file_git_blob_sha1", {}), "frozen V2")

    config = json.loads(CONFIG.read_text())
    if config.get("status") != "FROZEN_FOR_SYNTHETIC_CALIBRATION_RATIFIED":
        raise RuntimeError("V2 config is not frozen")
    if config.get("calibration_authorized") is not True:
        raise RuntimeError("frozen config calibration flag changed")
    if config.get("holdout_authorized") is not False:
        raise RuntimeError("frozen config holdout flag unexpectedly changed")
    if config.get("market_data_authorized") is not False:
        raise RuntimeError("market data must remain unauthorized")
    if config.get("bootstrap_requested_draws") != BOOTSTRAP_DRAWS:
        raise RuntimeError("bootstrap draw count mismatch")
    if config.get("holdout_replications_per_dgp") != 2000:
        raise RuntimeError("outer holdout count mismatch")
    _seed_namespace(config)

    _verify_git_blob_hashes(
        addendum.get("holdout_file_git_blob_sha1", {}),
        "holdout-path",
    )
    execution_manifest = verify_execution_bundle(addendum)

    executing_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    reviewed_commit = str(addendum["reviewed_holdout_code_commit"])
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", reviewed_commit, executing_commit],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if ancestor.returncode != 0:
        raise RuntimeError(
            "reviewed holdout code commit is not an ancestor of execution"
        )

    if platform.python_version() != "3.12.14":
        raise RuntimeError("unregistered Python version")
    if np.__version__ != "2.2.6" or scipy.__version__ != "1.15.3":
        raise RuntimeError("unregistered numerical dependency versions")
    subprocess.run(
        ["git", "diff", "--exit-code", "HEAD", "--"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    return gate, addendum, manifest, config, execution_manifest


def _validate_claim_record(
    addendum: dict,
    executing_commit: str,
    claim_ref: str,
    claim_sha: str,
    remote_line: str,
) -> None:
    expected_ref = addendum.get("one_shot_claim_ref")
    if claim_ref != expected_ref:
        raise RuntimeError("unexpected one-shot holdout claim ref")
    if claim_sha != executing_commit:
        raise RuntimeError("holdout claim SHA does not equal executing commit")
    parts = remote_line.strip().split()
    if len(parts) != 2 or parts[0] != claim_sha or parts[1] != claim_ref:
        raise RuntimeError("remote one-shot holdout claim does not match execution")


def _verify_claim(addendum: dict) -> tuple[str, str]:
    executing_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    claim_ref = os.environ.get("AMS_DEP_HOLDOUT_CLAIM_REF", "")
    claim_sha = os.environ.get("AMS_DEP_HOLDOUT_CLAIM_SHA", "")
    if not claim_ref or not claim_sha:
        raise RuntimeError("one-shot holdout claim environment is missing")
    remote = subprocess.check_output(
        ["git", "ls-remote", "--refs", "origin", claim_ref],
        cwd=ROOT,
        text=True,
    )
    _validate_claim_record(
        addendum, executing_commit, claim_ref, claim_sha, remote
    )
    return claim_ref, claim_sha


def _verify_holdout() -> tuple[dict, dict, dict, dict, dict, _HoldoutExecutionContext]:
    """Verify final authority plus the durable one-shot execution claim."""
    gate, addendum, manifest, config, execution_manifest = _verify_authority()
    claim_ref, claim_sha = _verify_claim(addendum)
    context = _activate_context(claim_ref, claim_sha)
    return gate, addendum, manifest, config, execution_manifest, context


def _tasks_for_shard(config: dict, shard_id: int):
    if not 0 <= shard_id < SHARD_COUNT:
        raise ValueError("shard_id outside frozen 0..127 range")
    outer = int(config["holdout_replications_per_dgp"])
    for dgp_index, case in enumerate(config["cases"]):
        for outer_index in range(outer):
            for asset_index in range(2):
                for hypothesis_index, hypothesis in enumerate(HYPOTHESES):
                    index = _task_index(
                        dgp_index,
                        outer_index,
                        asset_index,
                        hypothesis_index,
                        outer,
                    )
                    if index % SHARD_COUNT == shard_id:
                        yield (
                            index,
                            dgp_index,
                            case,
                            outer_index,
                            asset_index,
                            hypothesis_index,
                            hypothesis,
                        )


def _run_slot(
    context: _HoldoutExecutionContext,
    config: dict,
    dgp_index: int,
    case: str,
    outer_index: int,
    asset_index: int,
    hypothesis_index: int,
    hypothesis: str,
) -> dict:
    _require_context(context)
    # Reserved roots are read only after gates, bundle and one-shot claim verify.
    data_root = int(config["data_roots"]["holdout"])
    bootstrap_root = int(config["bootstrap_roots"]["holdout"])
    samples = simulate_case(case, dgp_index, outer_index, config, data_root)
    sample = samples[asset_index]
    x = primary_design(sample.x, sample.years, sample.states)
    geometry = ParzenGeometry(sample.hours, sample.segments)

    try:
        model = FixedOLS(x)
        observed = wald(model.fit(sample.y, geometry), hypothesis)
        fitted, residual = restricted_components(
            x, sample.y, geometry, hypothesis
        )
    except (InferenceError, np.linalg.LinAlgError) as exc:
        return {
            "available": False,
            "raw_p": None,
            "observed_wald": None,
            "requested_draws": 0,
            "invalid_draws": 0,
            "invalid_fraction": None,
            "error": str(exc),
        }

    statistics = []
    for bootstrap_index in range(BOOTSTRAP_DRAWS):
        weights = geometry.multipliers(
            [
                bootstrap_root,
                2,
                dgp_index,
                outer_index,
                asset_index,
                hypothesis_index,
                bootstrap_index,
            ]
        )
        try:
            value = wald(
                model.fit(fitted + residual * weights, geometry),
                hypothesis,
            )
        except (InferenceError, np.linalg.LinAlgError):
            value = None
        statistics.append(value)

    p = bootstrap_p_value(observed, statistics)
    return {
        "available": True,
        "raw_p": p["raw_p"],
        "observed_wald": observed,
        "requested_draws": p["requested_draws"],
        "invalid_draws": p["invalid_draws"],
        "invalid_fraction": p["invalid_fraction"],
        "error": None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard-id", required=True, type=int)
    args = parser.parse_args()

    gate, addendum, manifest, config, execution_manifest, context = _verify_holdout()
    shard_id = args.shard_id
    tasks = list(_tasks_for_shard(config, shard_id))
    expected = 1032 if shard_id < 32 else 1031
    if len(tasks) != expected:
        raise RuntimeError(
            f"unexpected shard task count: {len(tasks)} != {expected}"
        )

    OUTDIR.mkdir(parents=True, exist_ok=True)
    rows = []
    coordinate_hash = hashlib.sha256()
    for position, task in enumerate(tasks, 1):
        (
            index,
            dgp_index,
            case,
            outer_index,
            asset_index,
            hypothesis_index,
            hypothesis,
        ) = task
        coordinate_hash.update(
            _coordinate_line(
                dgp_index, outer_index, asset_index, hypothesis_index
            )
        )
        slot = _run_slot(
            context,
            config,
            dgp_index,
            case,
            outer_index,
            asset_index,
            hypothesis_index,
            hypothesis,
        )
        rows.append(
            {
                "task_index": index,
                "dgp_index": dgp_index,
                "case": case,
                "outer_index": outer_index,
                "asset_index": asset_index,
                "asset": ASSETS[asset_index],
                "hypothesis_index": hypothesis_index,
                "hypothesis": hypothesis,
                **slot,
            }
        )
        if position % 25 == 0 or position == len(tasks):
            print(
                f"holdout shard {shard_id}: {position}/{len(tasks)}",
                flush=True,
            )

    ledger = b"".join(
        (json.dumps(row, sort_keys=True, allow_nan=False) + "\n").encode()
        for row in rows
    )
    compressed = gzip.compress(ledger, mtime=0)
    ledger_path = OUTDIR / f"shard_{shard_id:03d}.jsonl.gz"
    ledger_path.write_bytes(compressed)

    executing_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    summary = {
        "classification": "FROZEN_AMS_DEP_V2_SYNTHETIC_HOLDOUT_SHARD",
        "suite": "holdout",
        "shard_id": shard_id,
        "shard_count": SHARD_COUNT,
        "task_count": len(rows),
        "coordinate_sha256": coordinate_hash.hexdigest(),
        "ledger_sha256": _digest(compressed),
        "ledger_uncompressed_sha256": _digest(ledger),
        "executing_commit": executing_commit,
        "freeze_manifest_sha256": _digest(MANIFEST.read_bytes()),
        "frozen_spec_sha256": _digest(CONFIG.read_bytes()),
        "holdout_addendum_sha256": _digest(
            DEFAULT_HOLDOUT_ADDENDUM.read_bytes()
        ),
        "execution_manifest_sha256": addendum["execution_manifest_sha256"],
        "one_shot_claim_ref": context.claim_ref,
        "one_shot_claim_sha": context.claim_sha,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "blas_threads": 1,
        "main_holdout_gate_authorized": gate[
            "v2_holdout_execution_authorized"
        ],
        "addendum_holdout_authorized": addendum[
            "explicit_holdout_execution_authorized"
        ],
        "calibration_run": False,
        "holdout_run": True,
        "market_data_accessed": False,
        "validation_or_oos_accessed": False,
        "strategy_pnl_calculated": False,
    }
    (OUTDIR / f"shard_{shard_id:03d}_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
