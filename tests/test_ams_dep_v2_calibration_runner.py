import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"research/scripts/run_ams_dep_v2_calibration_shard.py"
CONFIG=ROOT/"research/experiments/ams_dep_synthetic_core_v2.json"


def load_runner():
    spec=importlib.util.spec_from_file_location("v2_calibration_runner",SCRIPT)
    module=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_frozen_manifest_and_calibration_gate_verify_without_simulation():
    runner=load_runner()
    gate,manifest,cfg=runner._verify_freeze()
    assert gate["v2_calibration_execution_authorized"] is True
    assert gate["v2_holdout_execution_authorized"] is False
    assert manifest["status"]=="FROZEN_FOR_SYNTHETIC_CALIBRATION"
    assert cfg["calibration_authorized"] is True
    assert cfg["holdout_authorized"] is False
    assert cfg["market_data_authorized"] is False


def test_all_132000_tasks_are_assigned_exactly_once_to_128_shards():
    runner=load_runner()
    cfg=json.loads(CONFIG.read_text())
    seen=set()
    counts=[]
    for shard in range(128):
        tasks=list(runner._tasks_for_shard(cfg,shard))
        counts.append(len(tasks))
        for task in tasks:
            idx=task[0]
            assert idx not in seen
            assert idx%128==shard
            seen.add(idx)
    assert seen==set(range(132000))
    assert counts.count(1032)==32
    assert counts.count(1031)==96
