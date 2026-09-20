import json
from pathlib import Path

import pytest

from research_core.ams_dep_v2_holdout_gate import (
    HoldoutAuthorizationError,
    assert_ams_dep_v2_holdout_path_allowed,
    load_holdout_addendum,
)
from research_core.release_gate import ResearchGateError, load_ams_dep_release_gate


def _write(path: Path, value: dict) -> Path:
    path.write_text(json.dumps(value))
    return path


def _authorized_gate() -> dict:
    gate = load_ams_dep_release_gate().copy()
    gate["v2_synthetic_calibration_passed"] = True
    gate["v2_holdout_execution_authorized"] = True
    return gate


def _authorized_addendum() -> dict:
    addendum = load_holdout_addendum().copy()
    addendum.update(
        {
            "status": "AUTHORIZED",
            "calibration_artifact_verified": True,
            "holdout_path_independently_reviewed": True,
            "seed_separation_verified": True,
            "artifact_integrity_controls_verified": True,
            "duplicate_task_detection_verified": True,
            "per_cell_invalidity_guard_verified": True,
            "explicit_holdout_execution_authorized": True,
            "reviewed_holdout_code_commit": "example-commit",
            "reserved_holdout_seeds_consumed": False,
            "holdout_file_git_blob_sha1": {"example": "example"},
        }
    )
    return addendum


def test_current_holdout_authority_is_fail_closed():
    with pytest.raises(ResearchGateError):
        assert_ams_dep_v2_holdout_path_allowed()


def test_dual_gate_requires_main_gate_and_addendum(tmp_path):
    gate_path = _write(tmp_path / "gate.json", _authorized_gate())
    addendum_path = _write(
        tmp_path / "addendum.json", _authorized_addendum()
    )
    gate, addendum = assert_ams_dep_v2_holdout_path_allowed(
        gate_path, addendum_path
    )
    assert gate["v2_synthetic_calibration_passed"] is True
    assert gate["v2_holdout_execution_authorized"] is True
    assert addendum["explicit_holdout_execution_authorized"] is True


@pytest.mark.parametrize(
    "field",
    [
        "calibration_artifact_verified",
        "holdout_path_independently_reviewed",
        "seed_separation_verified",
        "artifact_integrity_controls_verified",
        "duplicate_task_detection_verified",
        "per_cell_invalidity_guard_verified",
        "explicit_holdout_execution_authorized",
    ],
)
def test_each_addendum_review_flag_fails_closed(tmp_path, field):
    gate_path = _write(tmp_path / "gate.json", _authorized_gate())
    addendum = _authorized_addendum()
    addendum[field] = False
    addendum_path = _write(tmp_path / "addendum.json", addendum)
    with pytest.raises(HoldoutAuthorizationError, match=field):
        assert_ams_dep_v2_holdout_path_allowed(gate_path, addendum_path)


def test_holdout_cannot_open_if_reserved_namespace_marked_consumed(tmp_path):
    gate_path = _write(tmp_path / "gate.json", _authorized_gate())
    addendum = _authorized_addendum()
    addendum["reserved_holdout_seeds_consumed"] = True
    addendum_path = _write(tmp_path / "addendum.json", addendum)
    with pytest.raises(
        HoldoutAuthorizationError,
        match="reserved_holdout_seeds_consumed=false",
    ):
        assert_ams_dep_v2_holdout_path_allowed(gate_path, addendum_path)


def test_holdout_cannot_open_without_calibration_pass(tmp_path):
    gate = _authorized_gate()
    gate["v2_synthetic_calibration_passed"] = False
    gate_path = _write(tmp_path / "gate.json", gate)
    addendum_path = _write(
        tmp_path / "addendum.json", _authorized_addendum()
    )
    with pytest.raises(ResearchGateError, match="v2_synthetic_calibration_passed"):
        assert_ams_dep_v2_holdout_path_allowed(gate_path, addendum_path)
