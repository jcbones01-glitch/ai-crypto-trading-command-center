"""Deterministic AMS-DEP V2 coordinate planner.

This script partitions already-specified task coordinates only. It must never
instantiate an RNG, generate synthetic data, or execute bootstrap draws.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "research/experiments/ams_dep_synthetic_core_v2_proposed.json"
OUT = ROOT / "research/experiments/ams_dep_v2_shard_plan.json"
SHARD_COUNT = 128
ASSETS = ("BTC", "ETH")
HYPOTHESES = ("DEP", "TIME", "STATE")


def task_index(dgp_index: int, outer_index: int, asset_index: int, hypothesis_index: int, outer_replications: int) -> int:
    return (((dgp_index * outer_replications) + outer_index) * len(ASSETS) + asset_index) * len(HYPOTHESES) + hypothesis_index


def coordinate_line(dgp_index: int, outer_index: int, asset_index: int, hypothesis_index: int) -> bytes:
    return f"{dgp_index}|{outer_index}|{asset_index}|{hypothesis_index}\n".encode("ascii")


def build_plan(spec: dict, shard_count: int = SHARD_COUNT) -> dict:
    if shard_count <= 0:
        raise ValueError("positive shard_count required")
    if spec.get("calibration_authorized") is not False:
        raise RuntimeError("planner requires calibration_authorized=false")
    if spec.get("market_data_authorized") is not False:
        raise RuntimeError("planner requires market_data_authorized=false")
    if spec.get("bootstrap_requested_draws") != 4999:
        raise RuntimeError("unexpected bootstrap draw count")
    if spec.get("calibration_replications_per_dgp") != 2000:
        raise RuntimeError("unexpected calibration replication count")
    if spec.get("holdout_replications_per_dgp") != 2000:
        raise RuntimeError("unexpected holdout replication count")
    if spec.get("primary_slots") != [
        "BTC_DEP", "BTC_TIME", "BTC_STATE", "ETH_DEP", "ETH_TIME", "ETH_STATE"
    ]:
        raise RuntimeError("unexpected primary-slot ordering")

    dgps = list(spec["cases"])
    outer = int(spec["calibration_replications_per_dgp"])
    requested_draws = int(spec["bootstrap_requested_draws"])
    task_count = len(dgps) * outer * len(ASSETS) * len(HYPOTHESES)

    shard_hashes = [hashlib.sha256() for _ in range(shard_count)]
    shard_counts = [0] * shard_count
    global_hash = hashlib.sha256()
    observed_indices = set()

    for dgp_index in range(len(dgps)):
        for outer_index in range(outer):
            for asset_index in range(len(ASSETS)):
                for hypothesis_index in range(len(HYPOTHESES)):
                    index = task_index(dgp_index, outer_index, asset_index, hypothesis_index, outer)
                    if index in observed_indices:
                        raise AssertionError("duplicate canonical task index")
                    observed_indices.add(index)
                    line = coordinate_line(dgp_index, outer_index, asset_index, hypothesis_index)
                    global_hash.update(line)
                    shard_id = index % shard_count
                    shard_hashes[shard_id].update(line)
                    shard_counts[shard_id] += 1

    if observed_indices != set(range(task_count)):
        raise AssertionError("canonical task coverage is not contiguous/exact")

    shards = []
    for shard_id, count in enumerate(shard_counts):
        shards.append({
            "shard_id": shard_id,
            "slot_tasks": count,
            "requested_inner_draws": count * requested_draws,
            "coordinate_sha256": shard_hashes[shard_id].hexdigest(),
        })

    return {
        "classification": "COORDINATE_PLAN_ONLY_NO_RNG_NO_CALIBRATION",
        "shard_count": shard_count,
        "dgp_count": len(dgps),
        "dgp_order": dgps,
        "outer_replications_per_dgp": outer,
        "asset_order": list(ASSETS),
        "hypothesis_order": list(HYPOTHESES),
        "bootstrap_requested_draws": requested_draws,
        "slot_task_count": task_count,
        "requested_inner_draws_per_suite": task_count * requested_draws,
        "calibration_and_holdout_requested_draws": 2 * task_count * requested_draws,
        "canonical_coordinate_sha256": global_hash.hexdigest(),
        "assignment_rule": "shard_id = task_index % shard_count",
        "task_index_rule": "(((dgp_index * outer_replications) + outer_index) * 2 + asset_index) * 3 + hypothesis_index",
        "rng_instantiated": False,
        "calibration_run": False,
        "holdout_run": False,
        "market_data_accessed": False,
        "validation_or_oos_accessed": False,
        "shards": shards,
    }


def main() -> None:
    raw = SPEC.read_bytes()
    spec = json.loads(raw)
    plan = build_plan(spec)
    plan["spec_path"] = str(SPEC.relative_to(ROOT))
    plan["spec_sha256"] = hashlib.sha256(raw).hexdigest()
    OUT.write_text(json.dumps(plan, indent=2) + "\n")
    print(json.dumps({
        key: plan[key]
        for key in (
            "classification",
            "shard_count",
            "slot_task_count",
            "requested_inner_draws_per_suite",
            "calibration_and_holdout_requested_draws",
            "canonical_coordinate_sha256",
            "rng_instantiated",
            "calibration_run",
            "market_data_accessed",
        )
    }, indent=2))


if __name__ == "__main__":
    main()
