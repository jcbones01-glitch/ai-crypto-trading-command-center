import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/scripts/plan_ams_dep_v2_shards.py"
SPEC = ROOT / "research/experiments/ams_dep_synthetic_core_v2_proposed.json"


def load_planner():
    spec = importlib.util.spec_from_file_location("ams_dep_v2_shard_planner", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_planner_has_no_rng_or_numeric_library_dependency():
    source = SCRIPT.read_text()
    forbidden = (
        "numpy",
        "np.random",
        "SeedSequence",
        "PCG64",
        "Generator(",
        "random.",
        "dependent_wild_bootstrap_v2",
    )
    for token in forbidden:
        assert token not in source


def test_128_shard_plan_has_exact_complete_workload():
    planner = load_planner()
    config = json.loads(SPEC.read_text())
    plan = planner.build_plan(config, 128)

    assert plan["classification"] == "COORDINATE_PLAN_ONLY_NO_RNG_NO_CALIBRATION"
    assert plan["slot_task_count"] == 132_000
    assert plan["requested_inner_draws_per_suite"] == 659_868_000
    assert plan["calibration_and_holdout_requested_draws"] == 1_319_736_000
    assert plan["rng_instantiated"] is False
    assert plan["calibration_run"] is False
    assert plan["holdout_run"] is False
    assert plan["market_data_accessed"] is False
    assert plan["validation_or_oos_accessed"] is False

    counts = [item["slot_tasks"] for item in plan["shards"]]
    assert len(counts) == 128
    assert sum(counts) == 132_000
    assert min(counts) == 1_031
    assert max(counts) == 1_032
    assert counts.count(1_032) == 32
    assert counts.count(1_031) == 96
    assert max(item["requested_inner_draws"] for item in plan["shards"]) == 5_158_968
    assert min(item["requested_inner_draws"] for item in plan["shards"]) == 5_153_969
    assert len({item["coordinate_sha256"] for item in plan["shards"]}) == 128


def test_task_index_is_schedule_independent_and_contiguous():
    planner = load_planner()
    outer = 2000
    indices = []
    for dgp in range(11):
        for rep in range(outer):
            for asset in range(2):
                for hypothesis in range(3):
                    indices.append(planner.task_index(dgp, rep, asset, hypothesis, outer))
    assert indices == list(range(132_000))


def test_planner_refuses_execution_authorization_changes():
    planner = load_planner()
    config = json.loads(SPEC.read_text())

    changed = dict(config)
    changed["calibration_authorized"] = True
    try:
        planner.build_plan(changed)
    except RuntimeError as exc:
        assert "calibration_authorized=false" in str(exc)
    else:
        raise AssertionError("planner must refuse an execution-authorized spec")

    changed = dict(config)
    changed["market_data_authorized"] = True
    try:
        planner.build_plan(changed)
    except RuntimeError as exc:
        assert "market_data_authorized=false" in str(exc)
    else:
        raise AssertionError("planner must refuse a market-authorized spec")
