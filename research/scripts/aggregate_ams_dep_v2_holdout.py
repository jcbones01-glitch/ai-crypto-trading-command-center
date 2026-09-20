from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import platform
from pathlib import Path

import numpy as np
import scipy

from research_core.ams_dep_v2_aggregation import summarize, task_index
from research_core.ams_dep_v2_holdout_gate import (
    DEFAULT_HOLDOUT_ADDENDUM,
    assert_ams_dep_v2_holdout_path_allowed,
)

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "research/experiments/ams_dep_synthetic_core_v2.json"
MANIFEST = ROOT / "research/governance/ams_dep_v2_freeze_manifest.json"
SHARD_COUNT = 128


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _coordinate_line(
    dgp_index: int,
    outer_index: int,
    asset_index: int,
    hypothesis_index: int,
) -> bytes:
    return (
        f"{dgp_index}|{outer_index}|{asset_index}|{hypothesis_index}\n"
    ).encode("ascii")


def _per_cell_invalidity_pass(cases: dict, threshold: float) -> bool:
    for case in cases.values():
        by_slot = case["bootstrap_invalidity_by_slot"]
        for slot in by_slot.values():
            maximum = slot.get("per_outer_max")
            if maximum is None or maximum > threshold:
                return False
    return True


def _insert_unique(rows: dict, idx: int, row: dict) -> None:
    if idx in rows:
        raise RuntimeError("duplicate task index")
    rows[idx] = row


def _verify_ledger_against_summary(
    ledger_path: Path,
    summary: dict,
) -> list[dict]:
    raw = ledger_path.read_bytes()
    if sha(raw) != summary["ledger_sha256"]:
        raise RuntimeError("shard ledger compressed hash mismatch")
    uncompressed = gzip.decompress(raw)
    if sha(uncompressed) != summary["ledger_uncompressed_sha256"]:
        raise RuntimeError("shard ledger uncompressed hash mismatch")

    coordinate_hash = hashlib.sha256()
    parsed = []
    for line in uncompressed.splitlines():
        row = json.loads(line)
        coordinate_hash.update(
            _coordinate_line(
                int(row["dgp_index"]),
                int(row["outer_index"]),
                int(row["asset_index"]),
                int(row["hypothesis_index"]),
            )
        )
        parsed.append(row)
    if coordinate_hash.hexdigest() != summary["coordinate_sha256"]:
        raise RuntimeError("shard coordinate hash mismatch")
    if len(parsed) != int(summary["task_count"]):
        raise RuntimeError("shard task-count mismatch")
    return parsed


def _load_shard_evidence(
    input_dir: Path,
    config: dict,
    manifest_sha: str,
    spec_sha: str,
    addendum_sha: str,
    execution_manifest_sha: str,
    expected_claim_ref: str,
    expected_claim_sha: str,
    expected_shards: int = SHARD_COUNT,
) -> tuple[dict, set[str], dict]:
    ledgers = sorted(input_dir.rglob("shard_*.jsonl.gz"))
    summaries = sorted(input_dir.rglob("shard_*_summary.json"))
    if len(ledgers) != expected_shards or len(summaries) != expected_shards:
        raise RuntimeError(
            f"expected {expected_shards} shard ledgers and summaries"
        )

    summary_by_shard = {}
    commits = set()
    for path in summaries:
        s = json.loads(path.read_text())
        shard = int(s["shard_id"])
        if shard in summary_by_shard:
            raise RuntimeError("duplicate shard summary")
        if s.get("classification") != "FROZEN_AMS_DEP_V2_SYNTHETIC_HOLDOUT_SHARD":
            raise RuntimeError("unexpected holdout shard classification")
        if s.get("suite") != "holdout":
            raise RuntimeError("non-holdout shard summary")
        if s.get("holdout_run") is not True:
            raise RuntimeError("holdout flag not set")
        if s.get("calibration_run") is not False:
            raise RuntimeError("calibration flag set during holdout")
        if (
            s.get("market_data_accessed")
            or s.get("validation_or_oos_accessed")
            or s.get("strategy_pnl_calculated")
        ):
            raise RuntimeError("forbidden access flag")
        if s.get("main_holdout_gate_authorized") is not True:
            raise RuntimeError("shard lacks main holdout authorization")
        if s.get("addendum_holdout_authorized") is not True:
            raise RuntimeError("shard lacks addendum holdout authorization")
        if s.get("one_shot_claim_ref") != expected_claim_ref:
            raise RuntimeError("mixed/unexpected one-shot claim ref")
        if s.get("one_shot_claim_sha") != expected_claim_sha:
            raise RuntimeError("mixed/unexpected one-shot claim SHA")
        if s.get("python") != "3.12.14":
            raise RuntimeError("unexpected Python version")
        if s.get("numpy") != "2.2.6" or s.get("scipy") != "1.15.3":
            raise RuntimeError("unexpected numerical dependency version")
        if s.get("blas_threads") != 1:
            raise RuntimeError("unexpected BLAS thread count")
        if (
            s["freeze_manifest_sha256"] != manifest_sha
            or s["frozen_spec_sha256"] != spec_sha
            or s["holdout_addendum_sha256"] != addendum_sha
            or s["execution_manifest_sha256"] != execution_manifest_sha
        ):
            raise RuntimeError("mixed holdout provenance")
        summary_by_shard[shard] = s
        commits.add(s["executing_commit"])

    if set(summary_by_shard) != set(range(expected_shards)):
        raise RuntimeError("incomplete shard-summary coverage")
    if len(commits) != 1:
        raise RuntimeError("mixed execution commits")
    if next(iter(commits)) != expected_claim_sha:
        raise RuntimeError("execution commit does not match one-shot claim SHA")

    n_outer = int(config["holdout_replications_per_dgp"])
    expected = len(config["cases"]) * n_outer * 6
    rows = {}
    shard_hashes = {}

    ledger_by_shard = {}
    for path in ledgers:
        shard = int(path.name[6:9])
        if shard in ledger_by_shard:
            raise RuntimeError("duplicate shard ledger")
        ledger_by_shard[shard] = path
    if set(ledger_by_shard) != set(range(expected_shards)):
        raise RuntimeError("incomplete shard-ledger coverage")

    for shard in range(expected_shards):
        path = ledger_by_shard[shard]
        summary = summary_by_shard[shard]
        shard_hashes[path.name] = sha(path.read_bytes())
        for row in _verify_ledger_against_summary(path, summary):
            idx = int(row["task_index"])
            dgp = int(row["dgp_index"])
            outer = int(row["outer_index"])
            asset = int(row["asset_index"])
            hyp = int(row["hypothesis_index"])
            if idx != task_index(dgp, outer, asset, hyp, n_outer):
                raise RuntimeError("task coordinate mismatch")
            if idx % expected_shards != shard:
                raise RuntimeError("task assigned to wrong shard")
            if config["cases"][dgp] != row["case"]:
                raise RuntimeError("DGP mismatch")
            _insert_unique(rows, idx, row)

    if expected_shards == SHARD_COUNT:
        if set(rows) != set(range(expected)):
            raise RuntimeError("incomplete task coverage")
    return rows, commits, shard_hashes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    gate, addendum = assert_ams_dep_v2_holdout_path_allowed()
    config = json.loads(CONFIG.read_text())
    manifest_sha = sha(MANIFEST.read_bytes())
    spec_sha = sha(CONFIG.read_bytes())
    addendum_sha = sha(DEFAULT_HOLDOUT_ADDENDUM.read_bytes())

    claim_ref = os.environ.get("AMS_DEP_HOLDOUT_CLAIM_REF", "")
    claim_sha = os.environ.get("AMS_DEP_HOLDOUT_CLAIM_SHA", "")
    if not claim_ref or not claim_sha:
        raise RuntimeError("one-shot claim environment is missing")

    rows, commits, shard_hashes = _load_shard_evidence(
        args.input_dir,
        config,
        manifest_sha,
        spec_sha,
        addendum_sha,
        str(addendum["execution_manifest_sha256"]),
        claim_ref,
        claim_sha,
    )

    # The frozen summarizer uses the calibration-count field internally.
    # Calibration and holdout are both registered at 2000. A shallow copy
    # makes that semantic mapping explicit without modifying frozen code.
    holdout_config = dict(config)
    holdout_config["calibration_replications_per_dgp"] = int(
        config["holdout_replications_per_dgp"]
    )
    cases, outer = summarize(holdout_config, rows)

    threshold = float(config["invalid_fraction_upper_bound"])
    per_cell_pass = _per_cell_invalidity_pass(cases, threshold)
    for case in cases.values():
        case["holdout_screen_pass"] = bool(
            case["calibration_screen_pass"]
            and all(
                slot["per_outer_max"] is not None
                and slot["per_outer_max"] <= threshold
                for slot in case["bootstrap_invalidity_by_slot"].values()
            )
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    payload = b"".join(
        (
            json.dumps(item, sort_keys=True, allow_nan=False) + "\n"
        ).encode()
        for item in outer
    )
    compressed = gzip.compress(payload, mtime=0)
    (args.output_dir / "outer_results.jsonl.gz").write_bytes(compressed)

    report = {
        "classification": "FROZEN_AMS_DEP_V2_SYNTHETIC_HOLDOUT",
        "suite": "holdout",
        "executing_commit": next(iter(commits)),
        "freeze_manifest_sha256": manifest_sha,
        "frozen_spec_sha256": spec_sha,
        "holdout_addendum_sha256": addendum_sha,
        "execution_manifest_sha256": str(addendum["execution_manifest_sha256"]),
        "task_count": len(rows),
        "outer_result_count": len(outer),
        "shard_count": SHARD_COUNT,
        "shard_ledger_sha256": shard_hashes,
        "outer_ledger_sha256": sha(compressed),
        "market_data_accessed": False,
        "validation_or_oos_accessed": False,
        "calibration_accessed": False,
        "holdout_accessed": True,
        "strategy_pnl_calculated": False,
        "empirical_release_authorized": False,
        "main_holdout_gate_authorized": gate[
            "v2_holdout_execution_authorized"
        ],
        "addendum_holdout_authorized": addendum[
            "explicit_holdout_execution_authorized"
        ],
        "one_shot_claim_ref": claim_ref,
        "one_shot_claim_sha": claim_sha,
        "per_cell_invalidity_screen_pass": per_cell_pass,
        "cases": cases,
        "holdout_screen_pass": bool(
            per_cell_pass
            and all(v["holdout_screen_pass"] for v in cases.values())
        ),
    }
    (args.output_dir / "summary.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(
        "AMS_DEP_V2_HOLDOUT_SCREEN="
        + ("PASS" if report["holdout_screen_pass"] else "FAIL")
    )


if __name__ == "__main__":
    main()
