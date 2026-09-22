import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/scripts/aggregate_ams_dep_v2_holdout.py"


def load_aggregator():
    spec = importlib.util.spec_from_file_location("v2_holdout_aggregator", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _case(maximum: float):
    return {
        "calibration_screen_pass": True,
        "bootstrap_invalidity_by_slot": {
            "BTC_DEP": {"per_outer_max": maximum},
            "BTC_TIME": {"per_outer_max": 0.0},
            "BTC_STATE": {"per_outer_max": 0.0},
            "ETH_DEP": {"per_outer_max": 0.0},
            "ETH_TIME": {"per_outer_max": 0.0},
            "ETH_STATE": {"per_outer_max": 0.0},
        },
    }


def test_per_cell_invalidity_rule_accepts_boundary_and_rejects_above():
    agg = load_aggregator()
    assert agg._per_cell_invalidity_pass({"x": _case(0.01)}, 0.01)
    assert not agg._per_cell_invalidity_pass({"x": _case(0.01001)}, 0.01)


def test_duplicate_task_detection_is_fail_closed():
    agg = load_aggregator()
    rows = {}
    agg._insert_unique(rows, 7, {"task_index": 7})
    with pytest.raises(RuntimeError, match="duplicate task index"):
        agg._insert_unique(rows, 7, {"task_index": 7})


def test_shard_artifact_integrity_checks_compressed_uncompressed_and_coordinates(
    tmp_path,
):
    agg = load_aggregator()
    row = {
        "task_index": 0,
        "dgp_index": 0,
        "case": "iid_null",
        "outer_index": 0,
        "asset_index": 0,
        "hypothesis_index": 0,
    }
    payload = (json.dumps(row) + "\n").encode()
    compressed = gzip.compress(payload, mtime=0)
    ledger = tmp_path / "shard_000.jsonl.gz"
    ledger.write_bytes(compressed)

    coordinate = hashlib.sha256()
    coordinate.update(b"0|0|0|0\n")
    summary = {
        "ledger_sha256": hashlib.sha256(compressed).hexdigest(),
        "ledger_uncompressed_sha256": hashlib.sha256(payload).hexdigest(),
        "coordinate_sha256": coordinate.hexdigest(),
        "task_count": 1,
    }
    parsed = agg._verify_ledger_against_summary(ledger, summary)
    assert parsed == [row]

    bad = dict(summary)
    bad["ledger_sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="compressed hash mismatch"):
        agg._verify_ledger_against_summary(ledger, bad)
