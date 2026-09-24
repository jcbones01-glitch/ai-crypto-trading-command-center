"""PSR-01B missing-data arms and frozen OHLCV base features.

This module accepts already-normalized MarketBar objects only. It performs
no archive, network, or protected-data access. The functions are therefore
safe for synthetic/offline implementation tests before empirical authorization.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import math
from typing import Sequence

import numpy as np

from .data_interfaces import MarketBar, validate_market_data
from .psr01b_core import PSR01BError


HOUR = timedelta(hours=1)
WARMUP_HOURS = 744
GLOBAL_CONTIGUOUS_TRANSITIONS = 336
BASE_FEATURE_NAMES = (
    "RET_1",
    "OPEN_GAP",
    "HIGH_PREVCLOSE",
    "LOW_PREVCLOSE",
    "CLOSE_OPEN",
    "HIGH_LOW",
    "CLOSE_LOCATION",
    "BODY_FRAC",
    "UPPER_WICK_FRAC",
    "LOWER_WICK_FRAC",
    "LOG_VOLUME",
    "LOG_VOLUME_CHANGE",
    "VOLUME_SMA24_RATIO",
    "LOG_DOLLAR_VOLUME",
    "TYPICAL_RETURN_1",
)


@dataclass(frozen=True)
class ArmBars:
    arm: str
    bars: tuple[MarketBar, ...]
    synthetic: tuple[bool, ...]
    segment_ids: tuple[int, ...]
    segment_indices: tuple[int, ...]

    def __post_init__(self) -> None:
        n = len(self.bars)
        if not (
            n == len(self.synthetic)
            == len(self.segment_ids)
            == len(self.segment_indices)
        ):
            raise PSR01BError("arm metadata length mismatch")


@dataclass(frozen=True)
class BaseFeatureResult:
    names: tuple[str, ...]
    matrix: np.ndarray
    deployable: np.ndarray
    segment_ids: np.ndarray
    segment_indices: np.ndarray


def _utc_hour(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise PSR01BError(f"{name} must be timezone-aware")
    if value.utcoffset() != timedelta(0):
        raise PSR01BError(f"{name} must be UTC")
    out = value.astimezone(timezone.utc)
    if out.minute or out.second or out.microsecond:
        raise PSR01BError(f"{name} must be an exact UTC hour")
    return out


def warmup_start(train_start: datetime) -> datetime:
    return _utc_hour(train_start, "train_start") - timedelta(hours=WARMUP_HOURS)


def _validate_normalized_bars(bars: Sequence[MarketBar]) -> tuple[MarketBar, ...]:
    result = tuple(bars)
    if not result:
        raise PSR01BError("at least one normalized bar is required")
    try:
        validate_market_data(list(result))
    except ValueError as exc:
        raise PSR01BError(str(exc)) from exc

    symbol = result[0].symbol
    for bar in result:
        stamp = _utc_hour(bar.timestamp, "bar timestamp")
        if stamp != bar.timestamp.astimezone(timezone.utc):
            raise PSR01BError("bar timestamp normalization mismatch")
        if bar.symbol != symbol:
            raise PSR01BError("mixed symbols are forbidden")
        values = (
            float(bar.open),
            float(bar.high),
            float(bar.low),
            float(bar.close),
            float(bar.volume),
        )
        if not all(math.isfinite(v) for v in values):
            raise PSR01BError("OHLCV values must be finite")
        if min(values[:4]) <= 0.0 or values[4] < 0.0:
            raise PSR01BError("invalid OHLCV domain")
    return result


def clip_to_artificial_state_boundary(
    bars: Sequence[MarketBar],
    *,
    train_start: datetime,
    through_exclusive: datetime,
) -> tuple[MarketBar, ...]:
    """Return only bars allowed to initialize fold state."""
    normalized = _validate_normalized_bars(bars)
    start = warmup_start(train_start)
    end = _utc_hour(through_exclusive, "through_exclusive")
    if not start < end:
        raise PSR01BError("invalid state interval")
    clipped = tuple(
        b for b in normalized if start <= b.timestamp.astimezone(timezone.utc) < end
    )
    if not clipped:
        raise PSR01BError("no bars inside artificial state boundary")
    return clipped


def construct_missing_data_arm(
    bars: Sequence[MarketBar],
    *,
    arm: str,
    interval_start: datetime,
    interval_end_exclusive: datetime,
) -> ArmBars:
    """Construct the frozen PAPER_FILL or PROJECT_GAP_PRESERVING arm."""
    normalized = _validate_normalized_bars(bars)
    start = _utc_hour(interval_start, "interval_start")
    end = _utc_hour(interval_end_exclusive, "interval_end_exclusive")
    if not start < end:
        raise PSR01BError("invalid arm interval")
    selected = tuple(
        b for b in normalized if start <= b.timestamp.astimezone(timezone.utc) < end
    )
    if not selected:
        raise PSR01BError("no accepted bars in arm interval")

    if arm == "PROJECT_GAP_PRESERVING":
        synthetic = [False] * len(selected)
        segment_ids: list[int] = []
        segment_indices: list[int] = []
        segment = 0
        index = 0
        previous: datetime | None = None
        for bar in selected:
            stamp = bar.timestamp.astimezone(timezone.utc)
            if previous is not None:
                if stamp - previous != HOUR:
                    segment += 1
                    index = 0
                else:
                    index += 1
            segment_ids.append(segment)
            segment_indices.append(index)
            previous = stamp
        return ArmBars(
            arm,
            selected,
            tuple(synthetic),
            tuple(segment_ids),
            tuple(segment_indices),
        )

    if arm != "PAPER_FILL":
        raise PSR01BError("unregistered missing-data arm")

    by_time = {b.timestamp.astimezone(timezone.utc): b for b in selected}
    if start not in by_time:
        raise PSR01BError("PAPER_FILL leading gap without previous close")

    filled: list[MarketBar] = []
    synthetic: list[bool] = []
    stamp = start
    previous_close: Decimal | None = None
    symbol = selected[0].symbol
    while stamp < end:
        observed = by_time.get(stamp)
        if observed is not None:
            bar = observed
            is_synthetic = False
        else:
            if previous_close is None:
                raise PSR01BError("PAPER_FILL leading gap without previous close")
            bar = MarketBar(
                timestamp=stamp,
                symbol=symbol,
                open=previous_close,
                high=previous_close,
                low=previous_close,
                close=previous_close,
                volume=Decimal("0"),
            )
            is_synthetic = True
        filled.append(bar)
        synthetic.append(is_synthetic)
        previous_close = bar.close
        stamp += HOUR

    return ArmBars(
        arm,
        tuple(filled),
        tuple(synthetic),
        tuple(0 for _ in filled),
        tuple(range(len(filled))),
    )


def _feature_row(
    bars: tuple[MarketBar, ...],
    segment_indices: tuple[int, ...],
    i: int,
) -> np.ndarray:
    bar = bars[i]
    o = float(bar.open)
    h = float(bar.high)
    l = float(bar.low)
    c = float(bar.close)
    v = float(bar.volume)

    values = np.full(len(BASE_FEATURE_NAMES), np.nan, dtype=np.float64)
    high_low = h - l
    values[4] = math.log(c / o)
    values[5] = math.log(h / l)
    values[6] = 0.0 if h == l else (2.0 * c - h - l) / high_low
    values[7] = 0.0 if h == l else (c - o) / high_low
    values[8] = 0.0 if h == l else (h - max(o, c)) / high_low
    values[9] = 0.0 if h == l else (min(o, c) - l) / high_low
    values[10] = math.log1p(v)
    values[13] = math.log1p(c * v)

    j = segment_indices[i]
    if j >= 1:
        prev = bars[i - 1]
        if segment_indices[i - 1] != j - 1:
            raise PSR01BError("segment metadata/predecessor mismatch")
        prev_c = float(prev.close)
        prev_v = float(prev.volume)
        prev_tp = (float(prev.high) + float(prev.low) + float(prev.close)) / 3.0
        tp = (h + l + c) / 3.0
        values[0] = math.log(c / prev_c)
        values[1] = math.log(o / prev_c)
        values[2] = math.log(h / prev_c)
        values[3] = math.log(l / prev_c)
        values[11] = math.log((v + 1.0) / (prev_v + 1.0))
        values[14] = math.log(tp / prev_tp)

    if j >= 23:
        start = i - 23
        if segment_indices[start] != j - 23:
            raise PSR01BError("24-bar volume window crossed a gap")
        mean_v = float(np.mean([float(x.volume) for x in bars[start : i + 1]]))
        values[12] = 0.0 if mean_v == 0.0 else v / mean_v - 1.0

    return values


def compute_base_ohlcv_features(arm_bars: ArmBars) -> BaseFeatureResult:
    """Compute the frozen 15 reconstructed OHLCV features."""
    bars = _validate_normalized_bars(arm_bars.bars)
    if len(bars) != len(arm_bars.segment_indices):
        raise PSR01BError("arm metadata length mismatch")

    matrix = np.vstack(
        [_feature_row(bars, arm_bars.segment_indices, i) for i in range(len(bars))]
    )
    segment_indices = np.asarray(arm_bars.segment_indices, dtype=np.int64)
    segment_ids = np.asarray(arm_bars.segment_ids, dtype=np.int64)
    deployable = segment_indices >= GLOBAL_CONTIGUOUS_TRANSITIONS

    if np.any(deployable & ~np.isfinite(matrix).all(axis=1)):
        raise PSR01BError("deployable base-feature row is nonfinite")

    return BaseFeatureResult(
        BASE_FEATURE_NAMES,
        matrix,
        deployable,
        segment_ids,
        segment_indices,
    )
