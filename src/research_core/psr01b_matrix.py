"""PSR-01B exact 28-column deployment matrix and split-row eligibility.

Pure implementation glue over already-built PSR-01B synthetic/offline feature
objects. No source acquisition or empirical execution is performed here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
from typing import Sequence

import numpy as np

from .psr01b_core import PSR01BError, split_origin_eligible
from .psr01b_egarch import replay_segment
from .psr01b_features import ArmBars, BaseFeatureResult, BASE_FEATURE_NAMES
from .psr01b_ta import FeatureSelectionResult, GROUP_ORDER


EGARCH_FEATURE_NAMES = (
    "EGARCH_SIGMA_NEXT",
    "EGARCH_LOG_SIGMA_NEXT",
    "EGARCH_Z_CURRENT",
)
SELECTED_FEATURE_NAMES = tuple(f"SELECTED__{group}" for group in GROUP_ORDER)
DEPLOYED_FEATURE_NAMES = BASE_FEATURE_NAMES + SELECTED_FEATURE_NAMES + EGARCH_FEATURE_NAMES

if len(DEPLOYED_FEATURE_NAMES) != 28:
    raise RuntimeError("PSR-01B deployed feature registry must contain exactly 28 columns")


@dataclass(frozen=True)
class EGARCHFeatureResult:
    matrix: np.ndarray
    finite: np.ndarray


@dataclass(frozen=True)
class DeployedMatrixResult:
    names: tuple[str, ...]
    matrix: np.ndarray
    deployable: np.ndarray


@dataclass(frozen=True)
class SplitRows:
    indices: np.ndarray
    X: np.ndarray
    y: np.ndarray
    origin_timestamps: tuple[datetime, ...]


def _utc_hour(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise PSR01BError(f"{name} must be timezone-aware")
    if value.utcoffset() != timedelta(0):
        raise PSR01BError(f"{name} must be UTC")
    out = value.astimezone(timezone.utc)
    if out.minute or out.second or out.microsecond:
        raise PSR01BError(f"{name} must be an exact UTC hour")
    return out


def build_egarch_features(
    arm: ArmBars,
    *,
    replay_start: datetime,
    params: Sequence[float],
    order: tuple[int, int, int],
) -> EGARCHFeatureResult:
    """Replay fixed EGARCH parameters from a training-start reset.

    The return whose endpoint is exactly replay_start is included when a
    contiguous predecessor bar exists. Later actual gaps start new independent
    return segments and reset the latent state.
    """
    start = _utc_hour(replay_start, "replay_start")
    n = len(arm.bars)
    if n == 0:
        raise PSR01BError("empty arm")
    matrix = np.full((n, 3), np.nan, dtype=np.float64)

    groups: list[tuple[list[int], list[float]]] = []
    current_indices: list[int] = []
    current_returns: list[float] = []
    previous_endpoint_index: int | None = None

    for i in range(1, n):
        previous = arm.bars[i - 1]
        current = arm.bars[i]
        stamp = _utc_hour(current.timestamp, "bar timestamp")
        prev_stamp = _utc_hour(previous.timestamp, "bar timestamp")
        if stamp < start:
            continue
        contiguous = stamp - prev_stamp == timedelta(hours=1)
        if not contiguous:
            if current_indices:
                groups.append((current_indices, current_returns))
                current_indices, current_returns = [], []
            previous_endpoint_index = None
            continue

        y = 100.0 * math.log(float(current.close) / float(previous.close))
        if not np.isfinite(y):
            raise PSR01BError("nonfinite EGARCH input return")

        if (
            previous_endpoint_index is not None
            and i != previous_endpoint_index + 1
        ):
            if current_indices:
                groups.append((current_indices, current_returns))
            current_indices, current_returns = [], []

        current_indices.append(i)
        current_returns.append(y)
        previous_endpoint_index = i

    if current_indices:
        groups.append((current_indices, current_returns))
    if not groups:
        raise PSR01BError("no EGARCH returns at or after replay_start")

    for indices, returns_y in groups:
        replay = replay_segment(returns_y, params, order)
        rows = np.asarray(indices, dtype=np.int64)
        matrix[rows, 0] = replay.sigma_next
        matrix[rows, 1] = replay.log_sigma_next
        matrix[rows, 2] = replay.z_current

    finite = np.isfinite(matrix).all(axis=1)
    return EGARCHFeatureResult(matrix, finite)


def assemble_deployed_matrix(
    *,
    base: BaseFeatureResult,
    selection: FeatureSelectionResult,
    egarch: EGARCHFeatureResult,
) -> DeployedMatrixResult:
    n = len(base.matrix)
    if base.matrix.shape != (n, 15):
        raise PSR01BError("base feature matrix must have exactly 15 columns")
    if selection.selected_matrix.shape != (n, 10):
        raise PSR01BError("selected TA matrix must have exactly 10 columns")
    if egarch.matrix.shape != (n, 3):
        raise PSR01BError("EGARCH matrix must have exactly 3 columns")
    if tuple(base.names) != BASE_FEATURE_NAMES:
        raise PSR01BError("base feature order mismatch")
    expected_selected = tuple(selection.selected_by_group[group] for group in GROUP_ORDER)
    if tuple(selection.selected_names) != expected_selected:
        raise PSR01BError("selected TA group order mismatch")

    matrix = np.column_stack(
        (base.matrix, selection.selected_matrix, egarch.matrix)
    ).astype(np.float64, copy=False)
    if matrix.shape != (n, 28):
        raise PSR01BError("deployed feature matrix must have exactly 28 columns")

    deployable = (
        np.asarray(base.deployable, dtype=bool)
        & np.isfinite(selection.selected_matrix).all(axis=1)
        & np.asarray(egarch.finite, dtype=bool)
        & np.isfinite(matrix).all(axis=1)
    )
    return DeployedMatrixResult(DEPLOYED_FEATURE_NAMES, matrix, deployable)


def eligible_split_rows(
    arm: ArmBars,
    deployed: DeployedMatrixResult,
    targets_next_hour: Sequence[float],
    *,
    split_start: datetime,
    split_end: datetime,
) -> SplitRows:
    """Apply exact half-open split endpoint eligibility to deployed rows."""
    start = _utc_hour(split_start, "split_start")
    end = _utc_hour(split_end, "split_end")
    if not start < end:
        raise PSR01BError("invalid split interval")
    y = np.asarray(targets_next_hour, dtype=np.float64)
    n = len(arm.bars)
    if (
        deployed.matrix.shape != (n, 28)
        or len(deployed.deployable) != n
        or y.shape != (n,)
    ):
        raise PSR01BError("split-row inputs are not aligned")

    indices: list[int] = []
    timestamps: list[datetime] = []
    for i, bar in enumerate(arm.bars):
        origin = _utc_hour(bar.timestamp, "bar timestamp")
        if (
            deployed.deployable[i]
            and np.isfinite(y[i])
            and split_origin_eligible(origin, start, end)
        ):
            indices.append(i)
            timestamps.append(origin)

    if not indices:
        raise PSR01BError("split has no eligible deployed rows")
    idx = np.asarray(indices, dtype=np.int64)
    X = deployed.matrix[idx]
    target = y[idx]
    if not np.isfinite(X).all() or not np.isfinite(target).all():
        raise PSR01BError("eligible split contains nonfinite values")
    return SplitRows(idx, X, target, tuple(timestamps))


def union_original_train_validation_rows(
    training: SplitRows,
    validation: SplitRows,
) -> tuple[np.ndarray, np.ndarray]:
    """Concatenate independently eligible train and validation rows only."""
    if training.X.shape[1] != 28 or validation.X.shape[1] != 28:
        raise PSR01BError("final-refit matrices must have 28 columns")
    if len(training.X) != len(training.y) or len(validation.X) != len(validation.y):
        raise PSR01BError("final-refit row alignment failure")
    return (
        np.vstack((training.X, validation.X)),
        np.concatenate((training.y, validation.y)),
    )
