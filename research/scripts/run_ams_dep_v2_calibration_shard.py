"""Guarded frozen AMS-DEP V2 calibration shard runner.

Synthetic calibration only. There is deliberately no holdout mode and no
market-data import. Execution requires the machine calibration gate.
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
from research_core.release_gate import assert_ams_dep_v2_calibration_execution_allowed

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "research/experiments/ams_dep_synthetic_core_v2.json"
MANIFEST = ROOT / "research/governance/ams_dep_v2_freeze_manifest.json"
OUTDIR = ROOT / "research/experiments/ams_dep_v2_calibration_shards"
SHARD_COUNT = 128
HYPOTHESES = ("DEP", "TIME", "STATE")


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _task_index(dgp_index: int, outer_index: int, asset_index: int,
                hypothesis_index: int, outer_replications: int) -> int:
    return (((dgp_index * outer_replications) + outer_index) * 2 + asset_index) * 3 + hypothesis_index


def _coordinate_line(dgp_index: int, outer_index: int, asset_index: int,
                     hypothesis_index: int) -> bytes:
    return f"{dgp_index}|{outer_index}|{asset_index}|{hypothesis_index}\n".encode("ascii")


def _verify_freeze() -> tuple[dict, dict, dict]:
    gate = assert_ams_dep_v2_calibration_execution_allowed()
    if not MANIFEST.exists():
        raise RuntimeError("missing frozen V2 manifest")
    manifest = json.loads(MANIFEST.read_text())
    if manifest.get("status") != "FROZEN_FOR_SYNTHETIC_CALIBRATION":
        raise RuntimeError("unexpected V2 freeze-manifest status")
    for relative, expected in manifest["file_sha256"].items():
        path = ROOT / relative
        if not path.exists() or _digest(path.read_bytes()) != expected:
            raise RuntimeError(f"frozen file hash mismatch: {relative}")

    config = json.loads(CONFIG.read_text())
    if config.get("status") != "FROZEN_FOR_SYNTHETIC_CALIBRATION_RATIFIED":
        raise RuntimeError("V2 config is not frozen")
    if config.get("calibration_authorized") is not True:
        raise RuntimeError("frozen config does not authorize calibration")
    if config.get("holdout_authorized") is not False:
        raise RuntimeError("holdout must remain unauthorized")
    if config.get("market_data_authorized") is not False:
        raise RuntimeError("market data must remain unauthorized")
    if config.get("bootstrap_requested_draws") != BOOTSTRAP_DRAWS:
        raise RuntimeError("bootstrap draw count mismatch")
    if config.get("calibration_replications_per_dgp") != 2000:
        raise RuntimeError("outer calibration count mismatch")
    if platform.python_version() != "3.12.14":
        raise RuntimeError("unregistered Python version")
    if np.__version__ != "2.2.6" or scipy.__version__ != "1.15.3":
        raise RuntimeError("unregistered numerical dependency versions")
    subprocess.run(
        ["git", "diff", "--exit-code", "HEAD", "--"],
        cwd=ROOT, check=True, stdout=subprocess.DEVNULL,
    )
    return gate, manifest, config


def _tasks_for_shard(config: dict, shard_id: int):
    if not 0 <= shard_id < SHARD_COUNT:
        raise ValueError("shard_id outside frozen 0..127 range")
    outer = int(config["calibration_replications_per_dgp"])
    for dgp_index, case in enumerate(config["cases"]):
        for outer_index in range(outer):
            for asset_index in range(2):
                for hypothesis_index, hypothesis in enumerate(HYPOTHESES):
                    index = _task_index(
                        dgp_index, outer_index, asset_index, hypothesis_index, outer
                    )
                    if index % SHARD_COUNT == shard_id:
                        yield (
                            index, dgp_index, case, outer_index,
                            asset_index, hypothesis_index, hypothesis,
                        )


def _run_slot(config: dict, dgp_index: int, case: str, outer_index: int,
              asset_index: int, hypothesis_index: int, hypothesis: str) -> dict:
    data_root = int(config["data_roots"]["calibration"])
    bootstrap_root = int(config["bootstrap_roots"]["calibration"])
    samples = simulate_case(case, dgp_index, outer_index, config, data_root)
    sample = samples[asset_index]
    x = primary_design(sample.x, sample.years, sample.states)
    geometry = ParzenGeometry(sample.hours, sample.segments)

    try:
        model = FixedOLS(x)
        observed = wald(model.fit(sample.y, geometry), hypothesis)
        fitted, residual = restricted_components(x, sample.y, geometry, hypothesis)
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
        weights = geometry.multipliers([
            bootstrap_root, 2, dgp_index, outer_index,
            asset_index, hypothesis_index, bootstrap_index,
        ])
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

    gate, manifest, config = _verify_freeze()
    shard_id = args.shard_id
    tasks = list(_tasks_for_shard(config, shard_id))
    expected = 1032 if shard_id < 32 else 1031
    if len(tasks) != expected:
        raise RuntimeError(f"unexpected shard task count: {len(tasks)} != {expected}")

    OUTDIR.mkdir(parents=True, exist_ok=True)
    rows = []
    coordinate_hash = hashlib.sha256()
    for position, task in enumerate(tasks, 1):
        (index, dgp_index, case, outer_index,
         asset_index, hypothesis_index, hypothesis) = task
        coordinate_hash.update(
            _coordinate_line(dgp_index, outer_index, asset_index, hypothesis_index)
        )
        slot = _run_slot(
            config, dgp_index, case, outer_index,
            asset_index, hypothesis_index, hypothesis,
        )
        rows.append({
            "task_index": index,
            "dgp_index": dgp_index,
            "case": case,
            "outer_index": outer_index,
            "asset_index": asset_index,
            "asset": ASSETS[asset_index],
            "hypothesis_index": hypothesis_index,
            "hypothesis": hypothesis,
            **slot,
        })
        if position % 25 == 0 or position == len(tasks):
            print(f"shard {shard_id}: {position}/{len(tasks)}", flush=True)

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
        "classification": "FROZEN_AMS_DEP_V2_SYNTHETIC_CALIBRATION_SHARD",
        "suite": "calibration",
        "shard_id": shard_id,
        "shard_count": SHARD_COUNT,
        "task_count": len(rows),
        "coordinate_sha256": coordinate_hash.hexdigest(),
        "ledger_sha256": _digest(compressed),
        "ledger_uncompressed_sha256": _digest(ledger),
        "executing_commit": executing_commit,
        "freeze_manifest_sha256": _digest(MANIFEST.read_bytes()),
        "frozen_spec_sha256": _digest(CONFIG.read_bytes()),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "blas_threads": 1,
        "calibration_authorized": gate["v2_calibration_execution_authorized"],
        "holdout_run": False,
        "market_data_accessed": False,
        "validation_or_oos_accessed": False,
    }
    (OUTDIR / f"shard_{shard_id:03d}_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
