from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/scripts/run_ams_dep_development_empirical_v2.py"


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "ams_dep_development_runner_v2",
        SCRIPT,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_v2_retains_exact_empirical_seed_and_family_contract():
    mod = load_runner()
    assert mod.EMPIRICAL_BOOTSTRAP_ROOT == 2026092201
    assert mod.EMPIRICAL_SENTINEL == 4294967295
    assert mod.ASSET_ORDER == ("BTCUSDT", "ETHUSDT")
    assert mod.HYPOTHESIS_ORDER == ("DEP", "TIME", "STATE")
    assert mod.BOOTSTRAP_DRAWS == 4999
    assert mod.INVALID_FRACTION_CEILING == 0.01
    assert tuple(mod.SLOTS) == (
        "BTC_DEP",
        "BTC_TIME",
        "BTC_STATE",
        "ETH_DEP",
        "ETH_TIME",
        "ETH_STATE",
    )


def test_original_fit_failure_remains_unavailable_without_bootstrap():
    mod = load_runner()
    inputs = {
        "design": np.zeros((2, 14), dtype=float),
        "target": np.zeros(2, dtype=float),
        "hours": np.asarray([1, 2], dtype=np.int64),
        "segments": np.asarray([0, 0], dtype=np.int64),
    }
    result = mod._run_slot(inputs, "DEP", 0, 0)
    assert result["available"] is False
    assert result["raw_p"] is None
    assert result["requested_draws"] == 0


def test_v2_invalidity_rule_is_strictly_greater_than_one_percent():
    mod = load_runner()
    slots = {
        name: {"available": True, "invalid_fraction": 0.01}
        for name in mod.SLOTS
    }
    assert mod._inference_validity_fail(slots) is False
    slots["BTC_DEP"]["invalid_fraction"] = 0.010001
    assert mod._inference_validity_fail(slots) is True


def test_v2_geometry_provenance_uses_actual_accepted_sample_rows():
    mod = load_runner()
    sample = SimpleNamespace(
        rows=(
            SimpleNamespace(hour=100, segment_id=0),
            SimpleNamespace(hour=101, segment_id=0),
            SimpleNamespace(hour=200, segment_id=1),
        )
    )
    value = mod._geometry_provenance(sample, None)
    assert value["accepted_geometry_row_count"] == 3
    assert value["design_shape"] is None
    assert value["hour_vector_sha256"] == mod._digest_lines([100, 101, 200])
    assert value["segment_vector_sha256"] == mod._digest_lines([0, 0, 1])


def test_v2_parent_v1_incident_is_immutable_provenance():
    mod = load_runner()
    assert mod.PARENT_V1 == {
        "run_id": 35834431025,
        "artifact_id": 10738551310,
        "claim_ref": "refs/tags/ams-dep-development-execution-claimed-v1",
        "claim_target": "969f6aeadda4143b0882b8e9169e3f6dd9c177ed",
        "artifact_zip_sha256":
            "b947d8a9d73dd05da0455ad8c1fb7ab845f4a187ff56ec99856b385fc0e403c7",
        "result_json_sha256":
            "19f53015e725526b8baa8da89fec5cdbf58d7e6f9a1985fcc626309ab0e2cca7",
    }


def test_v2_failure_artifact_has_no_repair_flags():
    mod = load_runner()
    mod._reset_incident_state()
    failure = mod._failure_result(RuntimeError("injected"))
    assert failure["version"] == 2
    assert failure["timestamp_rounding_used"] is False
    assert failure["interpolation_used"] is False
    assert failure["synthetic_bar_used"] is False
    assert failure["arbitrary_exception_skip_used"] is False


def test_v2_runner_uses_frozen_dwb_path_without_shortcuts():
    text = SCRIPT.read_text()
    assert "for bootstrap_index in range(BOOTSTRAP_DRAWS)" in text
    assert "pseudo_y = fitted + residual * weights" in text
    assert "bootstrap_p_value(observed, statistics)" in text
    assert "engineering_fixture(" not in text
    assert "wald_zero(" not in text
    assert "2026092201" in text
    assert "4294967295" in text


def test_v2_runner_has_no_user_controlled_empirical_parameters():
    mod = load_runner()
    assert tuple(inspect.signature(mod.run).parameters) == ()
    text = SCRIPT.read_text()
    for forbidden in (
        "argparse",
        "--symbol",
        "--partition",
        "--seed",
        "--draw",
        "--validation",
        "--oos",
        "--pnl",
        "--paper",
        "--live",
    ):
        assert forbidden not in text
