"""Machine-enforced AMS-DEP research release gate.

This module does not choose statistical methods or grant approval. It reads the
versioned governance artifact and fails closed unless every required empirical
release condition is explicitly true.
"""
from __future__ import annotations

import json
from pathlib import Path


class ResearchGateError(RuntimeError):
    """Raised when protected AMS-DEP work is not authorized."""


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GATE = ROOT / "research/governance/ams_dep_release_gate_v1.json"


def load_ams_dep_release_gate(path: Path | str = DEFAULT_GATE) -> dict:
    gate_path = Path(path)
    if not gate_path.is_absolute():
        gate_path = ROOT / gate_path
    try:
        data = json.loads(gate_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ResearchGateError(f"cannot load AMS-DEP release gate: {gate_path}") from exc
    if data.get("gate_id") != "AMS-DEP-EMPIRICAL-RELEASE":
        raise ResearchGateError("unexpected AMS-DEP release gate identity")
    return data


def assert_ams_dep_v2_synthetic_execution_allowed(path: Path | str = DEFAULT_GATE) -> dict:
    gate = load_ams_dep_release_gate(path)
    required = ("independent_v2_design_approved", "v2_specification_frozen",
                "v2_engineering_oracles_passed", "v2_synthetic_execution_authorized")
    if any(gate.get(field) is not True for field in required):
        raise ResearchGateError(
            f"AMS-DEP V2 synthetic execution blocked: {gate.get('status', 'UNKNOWN')}"
        )
    return gate


def assert_ams_dep_empirical_release_allowed(path: Path | str = DEFAULT_GATE) -> dict:
    gate = load_ams_dep_release_gate(path)
    required = (
        "independent_v2_design_approved",
        "v2_specification_frozen",
        "v2_synthetic_calibration_passed",
        "full_pipeline_synthetic_integrity_passed",
        "separate_empirical_release_approved",
        "development_market_data_execution_authorized",
    )
    missing = [name for name in required if gate.get(name) is not True]
    if missing:
        raise ResearchGateError(
            "AMS-DEP empirical execution blocked; unmet gate fields: "
            + ", ".join(missing)
        )
    if gate.get("validation_or_oos_access_authorized") is True:
        raise ResearchGateError(
            "AMS-DEP Development release gate must not authorize Validation/OOS access"
        )
    return gate
