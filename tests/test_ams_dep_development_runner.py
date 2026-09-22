from __future__ import annotations

import importlib.util
import inspect
from types import SimpleNamespace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/scripts/run_ams_dep_development_empirical_v1.py"


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "ams_dep_development_runner",
        SCRIPT,
    )
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


def test_support_failure_geometry_uses_actual_accepted_sample_rows():
    mod = load_runner()
    sample = SimpleNamespace(
        rows=(
            SimpleNamespace(hour=100, segment_id=0),
            SimpleNamespace(hour=101, segment_id=0),
            SimpleNamespace(hour=200, segment_id=1),
        )
    )
    result = mod._geometry_provenance(sample, None)
    assert result["accepted_geometry_row_count"] == 3
    assert result["design_shape"] is None
    assert result["hour_vector_sha256"] == mod._digest_lines([100, 101, 200])
    assert result["segment_vector_sha256"] == mod._digest_lines([0, 0, 1])
    assert result["hour_vector_sha256"] != mod._digest_lines([])


def test_failure_artifact_retains_consumed_governance_and_partial_evidence():
    mod = load_runner()
    mod._reset_incident_state()
    mod.INCIDENT_STATE.update(
        {
            "stage": "SOURCE_ETHUSDT",
            "execution_provenance": {
                "executing_commit": "a" * 40,
                "implementation_candidate_commit": "b" * 40,
                "review_anchor_ref": mod.DEFAULT_REVIEW_ANCHOR_REF,
                "review_anchor_sha": "b" * 40,
                "one_shot_claim_ref": mod.DEFAULT_CLAIM_REF,
                "one_shot_claim_sha": "a" * 40,
                "release_gate_sha256": "1" * 64,
                "development_execution_manifest_sha256": "2" * 64,
                "development_execution_spec_sha256": "3" * 64,
                "machine_registration_sha256": "4" * 64,
                "implementation_freeze_sha256": "5" * 64,
                "implementation_blob_evidence": {"x": {"expected": "y"}},
                "workflow_event": "workflow_dispatch",
                "workflow_run_id": "123",
                "workflow_run_attempt": "1",
                "workflow_job": "execute",
                "confirmation_verified": True,
            },
            "source_provenance": {
                "BTCUSDT": {"status": "COMPLETE"},
                "ETHUSDT": {
                    "status": "PARTIAL_SOURCE_FAILURE",
                    "completed_archive_count": 17,
                },
            },
            "sample_provenance": {
                "BTCUSDT": {"accepted_rows": 1000}
            },
            "numerical_provenance": {
                "BTCUSDT": {
                    "hour_vector_sha256": "6" * 64,
                    "segment_vector_sha256": "7" * 64,
                }
            },
            "market_data_accessed": True,
            "development_market_outcomes_accessed": True,
        }
    )
    failure = mod._failure_result(RuntimeError("injected"))
    assert failure["failure_stage"] == "SOURCE_ETHUSDT"
    assert failure["execution_provenance"]["one_shot_claim_sha"] == "a" * 40
    assert (
        failure["source_provenance"]["ETHUSDT"]["completed_archive_count"]
        == 17
    )
    assert failure["sample_provenance"]["BTCUSDT"]["accepted_rows"] == 1000
    assert "hour_vector_sha256" in failure["numerical_provenance"]["BTCUSDT"]
    assert failure["protected_access"]["validation_or_oos_accessed"] is False


def test_main_falls_back_to_incident_artifact_if_result_write_fails(monkeypatch):
    mod = load_runner()

    def fake_run():
        mod._reset_incident_state()
        mod.INCIDENT_STATE["stage"] = "RESULT_ARTIFACT_WRITE"
        mod.INCIDENT_STATE["execution_provenance"] = {
            "one_shot_claim_ref": mod.DEFAULT_CLAIM_REF,
            "one_shot_claim_sha": "a" * 40,
        }
        raise RuntimeError("injected result-stage failure")

    writes = []

    def fake_write(path, value):
        writes.append((path, value))
        if path == mod.OUTPUT_PATH:
            raise OSError("injected primary artifact failure")

    monkeypatch.setattr(mod, "run", fake_run)
    monkeypatch.setattr(mod, "_write_json", fake_write)

    with np.testing.assert_raises(SystemExit):
        mod.main()

    assert writes[0][0] == mod.OUTPUT_PATH
    assert writes[1][0] == mod.INCIDENT_PATH
    assert writes[1][1]["failure_stage"] == "RESULT_ARTIFACT_WRITE"
    assert "result_write_error" in writes[1][1]


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
