"""Second-stage execution lock for the reserved AMS-DEP V2 synthetic holdout.

The existing release gate remains controlling. This module adds a separate
holdout-path authorization artifact so calibration PASS cannot implicitly open
the reserved seed namespace.
"""
from __future__ import annotations

import json
from pathlib import Path

from research_core.release_gate import (
    DEFAULT_GATE,
    ResearchGateError,
    assert_ams_dep_v2_holdout_execution_allowed,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HOLDOUT_ADDENDUM = (
    ROOT / "research/governance/ams_dep_v2_holdout_execution_addendum_v1.json"
)


class HoldoutAuthorizationError(ResearchGateError):
    """Raised when the separate V2 holdout execution addendum is closed."""


def load_holdout_addendum(
    path: Path | str = DEFAULT_HOLDOUT_ADDENDUM,
) -> dict:
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    try:
        data = json.loads(p.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise HoldoutAuthorizationError(
            f"cannot load AMS-DEP V2 holdout addendum: {p}"
        ) from exc
    if data.get("addendum_id") != "AMS-DEP-V2-HOLDOUT-EXECUTION":
        raise HoldoutAuthorizationError("unexpected AMS-DEP V2 holdout addendum identity")
    return data


def assert_ams_dep_v2_holdout_path_allowed(
    gate_path: Path | str = DEFAULT_GATE,
    addendum_path: Path | str = DEFAULT_HOLDOUT_ADDENDUM,
) -> tuple[dict, dict]:
    """Require both the main release gate and the independent holdout addendum.

    This helper performs no RNG work and consumes no holdout seed.
    """
    gate = assert_ams_dep_v2_holdout_execution_allowed(gate_path)
    addendum = load_holdout_addendum(addendum_path)

    required = (
        "calibration_artifact_verified",
        "holdout_path_independently_reviewed",
        "seed_separation_verified",
        "artifact_integrity_controls_verified",
        "duplicate_task_detection_verified",
        "per_cell_invalidity_guard_verified",
        "explicit_holdout_execution_authorized",
    )
    missing = [name for name in required if addendum.get(name) is not True]
    if addendum.get("status") != "AUTHORIZED":
        missing.insert(0, "status=AUTHORIZED")
    if addendum.get("reserved_holdout_seeds_consumed") is not False:
        missing.append("reserved_holdout_seeds_consumed=false")
    if not addendum.get("authorized_execution_commit"):
        missing.append("authorized_execution_commit")
    if not addendum.get("holdout_file_git_blob_sha1"):
        missing.append("holdout_file_git_blob_sha1")

    for forbidden in (
        "market_data_authorized",
        "validation_or_oos_authorized",
        "strategy_pnl_authorized",
        "paper_trading_authorized",
        "live_trading_authorized",
    ):
        if addendum.get(forbidden) is not False:
            missing.append(f"{forbidden}=false")

    if missing:
        raise HoldoutAuthorizationError(
            "AMS-DEP V2 holdout path blocked; unmet addendum fields: "
            + ", ".join(missing)
        )
    return gate, addendum
