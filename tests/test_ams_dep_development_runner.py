from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/scripts/run_ams_dep_development_empirical_v1.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("ams_dep_development_runner", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_empirical_seed_and_family_contract_is_exact():
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


def test_original_fit_failure_becomes_unavailable_without_bootstrap_loop():
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


def test_support_failure_slot_is_retained_as_unavailable():
    mod = load_runner()
    result = mod._unavailable_support_slot()
    assert result["available"] is False
    assert result["raw_p"] is None
    assert result["error"] == "INSUFFICIENT_REGISTERED_SUPPORT"


def test_invalidity_above_one_percent_blocks_holm_interpretation():
    mod = load_runner()
    slots = {
        name: {
            "available": True,
            "invalid_fraction": 0.0,
        }
        for name in mod.SLOTS
    }
    assert mod._inference_validity_fail(slots) is False
    slots["BTC_DEP"]["invalid_fraction"] = 0.010001
    assert mod._inference_validity_fail(slots) is True
    slots["BTC_DEP"]["invalid_fraction"] = 0.01
    assert mod._inference_validity_fail(slots) is False


def test_runner_uses_frozen_dwb_path_not_engineering_or_asymptotic_fallback():
    text = SCRIPT.read_text()
    assert "for bootstrap_index in range(BOOTSTRAP_DRAWS)" in text
    assert "pseudo_y = fitted + residual * weights" in text
    assert "bootstrap_p_value(observed, statistics)" in text
    assert "engineering_fixture(" not in text
    assert "wald_zero(" not in text
    assert "2026092201" in text
    assert "4294967295" in text


def test_runner_has_no_user_controlled_empirical_parameters():
    mod = load_runner()
    assert tuple(inspect.signature(mod.run).parameters) == ()
    text = SCRIPT.read_text()
    for forbidden in (
        "argparse",
        "--symbol",
        "--partition",
        "--seed",
        "--draw",
        "--gate",
        "--validation",
        "--oos",
        "--pnl",
        "--paper",
        "--live",
    ):
        assert forbidden not in text
