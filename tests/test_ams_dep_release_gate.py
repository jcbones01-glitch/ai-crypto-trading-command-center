import json
from pathlib import Path

import pytest

from research_core.release_gate import (
    ResearchGateError,
    assert_ams_dep_empirical_release_allowed,
    assert_ams_dep_v2_calibration_execution_allowed,
    assert_ams_dep_v2_holdout_execution_allowed,
    load_ams_dep_release_gate,
)

ROOT=Path(__file__).resolve().parents[1]


def test_current_gate_authorizes_calibration_only():
    g=load_ams_dep_release_gate()
    assert g["status"]=="V2_CALIBRATION_FROZEN_AUTHORIZED"
    assert g["independent_v2_design_approved"] is True
    assert g["v2_specification_frozen"] is True
    assert g["v2_engineering_oracles_passed"] is True
    assert g["v2_sharding_plan_verified"] is True
    assert g["v2_calibration_execution_authorized"] is True
    assert g["v2_holdout_execution_authorized"] is False
    assert g["v2_synthetic_calibration_passed"] is False
    assert g["development_market_data_execution_authorized"] is False
    assert g["validation_or_oos_access_authorized"] is False
    assert assert_ams_dep_v2_calibration_execution_allowed()["gate_id"]=="AMS-DEP-EMPIRICAL-RELEASE"


def test_holdout_and_empirical_release_remain_blocked():
    with pytest.raises(ResearchGateError,match="holdout execution blocked"):
        assert_ams_dep_v2_holdout_execution_allowed()
    with pytest.raises(ResearchGateError,match="empirical execution blocked"):
        assert_ams_dep_empirical_release_allowed()


def test_calibration_guard_fails_if_any_prerequisite_is_removed(tmp_path):
    g=load_ams_dep_release_gate().copy()
    required=("independent_v2_design_approved","v2_specification_frozen",
              "v2_engineering_oracles_passed","v2_sharding_plan_verified",
              "v2_calibration_execution_authorized")
    path=tmp_path/"gate.json"
    for field in required:
        candidate=g.copy()
        candidate[field]=False
        path.write_text(json.dumps(candidate))
        with pytest.raises(ResearchGateError):
            assert_ams_dep_v2_calibration_execution_allowed(path)


def test_holdout_needs_passed_calibration_and_separate_authorization(tmp_path):
    g=load_ams_dep_release_gate().copy()
    path=tmp_path/"gate.json"
    g["v2_synthetic_calibration_passed"]=True
    path.write_text(json.dumps(g))
    with pytest.raises(ResearchGateError,match="v2_holdout_execution_authorized"):
        assert_ams_dep_v2_holdout_execution_allowed(path)
    g["v2_holdout_execution_authorized"]=True
    path.write_text(json.dumps(g))
    assert assert_ams_dep_v2_holdout_execution_allowed(path)["v2_holdout_execution_authorized"]


def test_empirical_release_requires_holdout_pipeline_and_separate_approval(tmp_path):
    g=load_ams_dep_release_gate().copy()
    for field in ("v2_synthetic_calibration_passed","v2_synthetic_holdout_passed",
                  "full_pipeline_synthetic_integrity_passed",
                  "separate_empirical_release_approved",
                  "development_market_data_execution_authorized"):
        g[field]=True
    path=tmp_path/"gate.json"
    path.write_text(json.dumps(g))
    assert assert_ams_dep_empirical_release_allowed(path)["gate_id"]=="AMS-DEP-EMPIRICAL-RELEASE"
    g["validation_or_oos_access_authorized"]=True
    path.write_text(json.dumps(g))
    with pytest.raises(ResearchGateError,match="must not authorize Validation/OOS"):
        assert_ams_dep_empirical_release_allowed(path)


def test_future_empirical_runner_must_call_release_guard():
    scripts=ROOT/"research"/"scripts"
    for path in sorted(scripts.glob("*ams_dep*empirical*.py")):
        assert "assert_ams_dep_empirical_release_allowed" in path.read_text()
