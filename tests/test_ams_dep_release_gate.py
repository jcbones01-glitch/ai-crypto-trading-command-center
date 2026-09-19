from pathlib import Path

import pytest

from research_core.release_gate import (
    ResearchGateError,
    assert_ams_dep_empirical_release_allowed,
    assert_ams_dep_v2_calibration_execution_allowed,
    assert_ams_dep_v2_holdout_execution_allowed,
    assert_ams_dep_v2_synthetic_execution_allowed,
    load_ams_dep_release_gate,
)


ROOT = Path(__file__).resolve().parents[1]


def test_current_ams_dep_gate_authorizes_calibration_only():
    gate = load_ams_dep_release_gate()
    assert gate["status"] == "V2_SYNTHETIC_CALIBRATION_AUTHORIZED"
    assert gate["design_review_issue"] == 44
    assert gate["v1_calibration_failed"] is True
    assert gate["conditional_v2_design_review_received"] is True
    assert gate["independent_ratification_decision"] == "RATIFY_V2_FREEZE_FOR_SYNTHETIC_CALIBRATION"
    assert gate["independent_v2_design_approved"] is True
    assert gate["v2_specification_frozen"] is True
    assert gate["v2_engineering_oracles_passed"] is True
    assert gate["v2_sharding_plan_verified"] is True
    assert gate["v2_calibration_execution_authorized"] is True
    assert gate["v2_holdout_execution_authorized"] is False
    assert gate["v2_synthetic_calibration_passed"] is False
    assert gate["development_market_data_execution_authorized"] is False
    assert gate["validation_or_oos_access_authorized"] is False
    assert gate["strategy_pnl_authorized"] is False
    assert gate["paper_trading_authorized"] is False
    assert gate["live_trading_authorized"] is False


def test_current_gate_allows_calibration_but_blocks_holdout_and_empirical():
    assert assert_ams_dep_v2_calibration_execution_allowed()["v2_calibration_execution_authorized"] is True
    assert assert_ams_dep_v2_synthetic_execution_allowed()["v2_calibration_execution_authorized"] is True
    with pytest.raises(ResearchGateError, match="V2 holdout execution blocked"):
        assert_ams_dep_v2_holdout_execution_allowed()
    with pytest.raises(ResearchGateError, match="empirical execution blocked"):
        assert_ams_dep_empirical_release_allowed()


def test_empirical_gate_requires_all_release_conditions_and_never_oos(tmp_path):
    gate = load_ams_dep_release_gate().copy()
    for key in (
        "independent_v2_design_approved",
        "v2_specification_frozen",
        "v2_synthetic_calibration_passed",
        "v2_synthetic_holdout_passed",
        "full_pipeline_synthetic_integrity_passed",
        "separate_empirical_release_approved",
        "development_market_data_execution_authorized",
    ):
        gate[key] = True

    allowed = tmp_path / "allowed.json"
    import json
    allowed.write_text(json.dumps(gate))
    assert assert_ams_dep_empirical_release_allowed(allowed)["gate_id"] == "AMS-DEP-EMPIRICAL-RELEASE"

    gate["validation_or_oos_access_authorized"] = True
    forbidden = tmp_path / "forbidden.json"
    forbidden.write_text(json.dumps(gate))
    with pytest.raises(ResearchGateError, match="must not authorize Validation/OOS"):
        assert_ams_dep_empirical_release_allowed(forbidden)


def test_any_future_ams_dep_empirical_runner_must_call_release_guard():
    scripts = ROOT / "research" / "scripts"
    candidates = sorted(scripts.glob("*ams_dep*empirical*.py"))
    for path in candidates:
        text = path.read_text()
        assert "assert_ams_dep_empirical_release_allowed" in text, (
            f"{path} is an AMS-DEP empirical runner but does not call the "
            "machine-enforced release gate"
        )


def test_calibration_flag_alone_cannot_bypass_review_freeze_or_oracles(tmp_path):
    import json
    gate = load_ams_dep_release_gate().copy()
    gate["v2_calibration_execution_authorized"] = True
    path = tmp_path / "gate.json"
    for field in (
        "independent_v2_design_approved",
        "v2_specification_frozen",
        "v2_engineering_oracles_passed",
        "v2_sharding_plan_verified",
    ):
        gate[field] = False
        path.write_text(json.dumps(gate))
        with pytest.raises(ResearchGateError):
            assert_ams_dep_v2_calibration_execution_allowed(path)
        gate[field] = True
    path.write_text(json.dumps(gate))
    assert assert_ams_dep_v2_calibration_execution_allowed(path)["v2_calibration_execution_authorized"]


def test_holdout_cannot_unlock_before_calibration_passes(tmp_path):
    import json
    gate = load_ams_dep_release_gate().copy()
    for key in (
        "independent_v2_design_approved",
        "v2_specification_frozen",
        "v2_engineering_oracles_passed",
        "v2_sharding_plan_verified",
        "v2_holdout_execution_authorized",
    ):
        gate[key] = True
    gate["v2_synthetic_calibration_passed"] = False
    path = tmp_path / "gate.json"
    path.write_text(json.dumps(gate))
    with pytest.raises(ResearchGateError, match="v2_synthetic_calibration_passed"):
        assert_ams_dep_v2_holdout_execution_allowed(path)


def test_empirical_release_requires_successful_unopened_holdout(tmp_path):
    import json
    gate = load_ams_dep_release_gate().copy()
    for key in (
        "independent_v2_design_approved",
        "v2_specification_frozen",
        "v2_synthetic_calibration_passed",
        "full_pipeline_synthetic_integrity_passed",
        "separate_empirical_release_approved",
        "development_market_data_execution_authorized",
    ):
        gate[key] = True
    gate["v2_synthetic_holdout_passed"] = False
    path = tmp_path / "gate.json"
    path.write_text(json.dumps(gate))
    with pytest.raises(ResearchGateError, match="v2_synthetic_holdout_passed"):
        assert_ams_dep_empirical_release_allowed(path)
