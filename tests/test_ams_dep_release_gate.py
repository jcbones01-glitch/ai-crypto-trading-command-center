from pathlib import Path

import pytest

from research_core.release_gate import (
    ResearchGateError,
    assert_ams_dep_empirical_release_allowed,
    assert_ams_dep_v2_synthetic_execution_allowed,
    load_ams_dep_release_gate,
)


ROOT = Path(__file__).resolve().parents[1]


def test_current_ams_dep_gate_is_explicitly_blocked():
    gate = load_ams_dep_release_gate()
    assert gate["status"] == "BLOCKED_INDEPENDENT_REVIEW"
    assert gate["design_review_issue"] == 44
    assert gate["v1_calibration_failed"] is True
    assert gate["independent_v2_design_approved"] is False
    assert gate["v2_synthetic_execution_authorized"] is False
    assert gate["development_market_data_execution_authorized"] is False
    assert gate["validation_or_oos_access_authorized"] is False
    assert gate["strategy_pnl_authorized"] is False
    assert gate["paper_trading_authorized"] is False
    assert gate["live_trading_authorized"] is False


def test_current_gate_blocks_v2_synthetic_and_empirical_execution():
    with pytest.raises(ResearchGateError, match="V2 synthetic execution blocked"):
        assert_ams_dep_v2_synthetic_execution_allowed()
    with pytest.raises(ResearchGateError, match="empirical execution blocked"):
        assert_ams_dep_empirical_release_allowed()


def test_empirical_gate_requires_all_release_conditions_and_never_oos(tmp_path):
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
