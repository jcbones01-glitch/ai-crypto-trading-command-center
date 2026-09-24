"""PSR-01B frozen TA-candidate and four-block selection layer.

Pure synthetic/offline implementation.  Input is an already-constructed PSR-01B
missing-data arm; this module performs no archive or network I/O.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import calendar
import math
from typing import Mapping, Sequence

import numpy as np
from scipy.stats import spearmanr

from .psr01b_core import PSR01BError
from .psr01b_features import ArmBars, GLOBAL_CONTIGUOUS_TRANSITIONS


WINDOWS = (3, 6, 12, 24, 48, 72, 168, 336)
RETURN_LAGS = (1, 2, 3, 6, 12, 24)
INDICATOR_FAMILIES = (
    "RSI",
    "ROC",
    "DIST_SMA",
    "MACD",
    "MACD_HIST",
    "ATR_RATIO",
    "ROLL_STD",
    "BB_POS",
    "VWAP_DEV",
    "OBV_SLOPE",
    "MFI",
)
GROUPS = {
    "MOM_RSI": ("RSI",),
    "MOM_ROC": ("ROC",),
    "TREND_SMA": ("DIST_SMA",),
    "TREND_MACD": ("MACD", "MACD_HIST"),
    "VOL_ATR_STD": ("ATR_RATIO", "ROLL_STD"),
    "VOL_BB": ("BB_POS",),
    "PRICE_VOLUME_VWAP": ("VWAP_DEV",),
    "VOLUME_OBV": ("OBV_SLOPE",),
    "VOLUME_MFI": ("MFI",),
    "RETURN_LAGS": ("LAG_RETURN",),
}
GROUP_ORDER = tuple(GROUPS)
CANDIDATE_NAMES = tuple(
    [f"{family}__W{w}" for family in INDICATOR_FAMILIES for w in WINDOWS]
    + [f"LAG_RETURN__K{k}" for k in RETURN_LAGS]
)
CANDIDATE_FAMILIES = tuple(
    [family for family in INDICATOR_FAMILIES for _ in WINDOWS]
    + ["LAG_RETURN" for _ in RETURN_LAGS]
)
if len(CANDIDATE_NAMES) != 94:
    raise RuntimeError("PSR-01B candidate registry must contain exactly 94 features")


@dataclass(frozen=True)
class TACandidateResult:
    names: tuple[str, ...]
    families: tuple[str, ...]
    matrix: np.ndarray
    target_next_hour: np.ndarray
    deployable: np.ndarray


@dataclass(frozen=True)
class FeatureSelectionResult:
    selected_by_group: dict[str, str]
    selected_names: tuple[str, ...]
    selected_matrix: np.ndarray
    average_ranks: dict[str, dict[str, float]]
    block_correlations: dict[str, tuple[float, float, float, float]]


def _segment_slices(arm: ArmBars) -> list[slice]:
    ids = np.asarray(arm.segment_ids, dtype=np.int64)
    idx = np.asarray(arm.segment_indices, dtype=np.int64)
    if len(ids) != len(arm.bars) or len(idx) != len(arm.bars):
        raise PSR01BError("arm segment metadata length mismatch")
    if not len(ids):
        raise PSR01BError("empty arm")
    cuts = np.r_[0, np.flatnonzero(np.diff(ids) != 0) + 1, len(ids)]
    out: list[slice] = []
    for a, b in zip(cuts[:-1], cuts[1:]):
        expected = np.arange(b - a, dtype=np.int64)
        if not np.array_equal(idx[a:b], expected):
            raise PSR01BError("segment indices must restart at zero and increment by one")
        out.append(slice(int(a), int(b)))
    return out


def _ema(values: np.ndarray, span: int) -> np.ndarray:
    alpha = 2.0 / (span + 1.0)
    out = np.empty(len(values), dtype=np.float64)
    out[0] = values[0]
    for i in range(1, len(values)):
        out[i] = alpha * values[i] + (1.0 - alpha) * out[i - 1]
    return out


def _window_ols_slope(values: np.ndarray) -> float:
    n = len(values)
    x = np.arange(n, dtype=np.float64)
    xc = x - np.mean(x)
    return float(np.dot(xc, values - np.mean(values)) / np.dot(xc, xc))


def _compute_segment(
    open_: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    volume: np.ndarray,
) -> dict[str, np.ndarray]:
    n = len(close)
    out = {name: np.full(n, np.nan, dtype=np.float64) for name in CANDIDATE_NAMES}

    returns = np.full(n, np.nan, dtype=np.float64)
    if n > 1:
        returns[1:] = np.log(close[1:] / close[:-1])

    typical = (high + low + close) / 3.0
    obv = np.zeros(n, dtype=np.float64)
    for j in range(1, n):
        direction = 1.0 if close[j] > close[j - 1] else (-1.0 if close[j] < close[j - 1] else 0.0)
        obv[j] = obv[j - 1] + direction * volume[j]

    for w in WINDOWS:
        # RSI with Wilder seed/recursion.
        rsi = out[f"RSI__W{w}"]
        if n > w:
            deltas = close[1:] - close[:-1]
            gains = np.maximum(deltas, 0.0)
            losses = np.maximum(-deltas, 0.0)
            avg_gain = float(np.mean(gains[:w]))
            avg_loss = float(np.mean(losses[:w]))
            for j in range(w, n):
                if j > w:
                    avg_gain = (avg_gain * (w - 1) + gains[j - 1]) / w
                    avg_loss = (avg_loss * (w - 1) + losses[j - 1]) / w
                if avg_loss == 0.0:
                    rsi[j] = 50.0 if avg_gain == 0.0 else 100.0
                else:
                    rsi[j] = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)

        roc = out[f"ROC__W{w}"]
        for j in range(w, n):
            roc[j] = close[j] / close[j - w] - 1.0

        dist = out[f"DIST_SMA__W{w}"]
        bb = out[f"BB_POS__W{w}"]
        vwap_dev = out[f"VWAP_DEV__W{w}"]
        obv_slope = out[f"OBV_SLOPE__W{w}"]
        for j in range(w - 1, n):
            s = j - w + 1
            cw = close[s : j + 1]
            vw = volume[s : j + 1]
            mean_c = float(np.mean(cw))
            dist[j] = close[j] / mean_c - 1.0
            sd = float(np.std(cw, ddof=0))
            bb[j] = 0.0 if sd == 0.0 else (close[j] - mean_c) / (2.0 * sd)
            total_v = float(np.sum(vw))
            if total_v == 0.0:
                vwap_dev[j] = 0.0
            else:
                vwap = float(np.sum(typical[s : j + 1] * vw) / total_v)
                vwap_dev[j] = close[j] / vwap - 1.0
            slope = _window_ols_slope(obv[s : j + 1])
            obv_slope[j] = slope / max(float(np.mean(vw)), 1e-12)

        slow = w
        fast = max(2, math.floor(w / 2))
        ema_fast = _ema(close, fast)
        ema_slow = _ema(close, slow)
        raw_macd = ema_fast - ema_slow
        out[f"MACD__W{w}"][:] = raw_macd / close
        signal_span = max(2, math.floor(w / 3))
        signal = _ema(raw_macd, signal_span)
        out[f"MACD_HIST__W{w}"][:] = (raw_macd - signal) / close

        atr = out[f"ATR_RATIO__W{w}"]
        if n > w:
            tr = np.full(n, np.nan, dtype=np.float64)
            tr[1:] = np.maximum.reduce(
                (
                    high[1:] - low[1:],
                    np.abs(high[1:] - close[:-1]),
                    np.abs(low[1:] - close[:-1]),
                )
            )
            atr_value = float(np.mean(tr[1 : w + 1]))
            for j in range(w, n):
                if j > w:
                    atr_value = (atr_value * (w - 1) + tr[j]) / w
                atr[j] = atr_value / close[j]

        roll_std = out[f"ROLL_STD__W{w}"]
        for j in range(w, n):
            roll_std[j] = float(np.std(returns[j - w + 1 : j + 1], ddof=0))

        mfi = out[f"MFI__W{w}"]
        if n > w:
            raw_flow = typical * volume
            pos = np.zeros(n, dtype=np.float64)
            neg = np.zeros(n, dtype=np.float64)
            changes = typical[1:] - typical[:-1]
            pos[1:] = np.where(changes > 0.0, raw_flow[1:], 0.0)
            neg[1:] = np.where(changes < 0.0, raw_flow[1:], 0.0)
            for j in range(w, n):
                positive = float(np.sum(pos[j - w + 1 : j + 1]))
                negative = float(np.sum(neg[j - w + 1 : j + 1]))
                if negative == 0.0:
                    value = 50.0 if positive == 0.0 else 100.0
                else:
                    value = 100.0 - 100.0 / (1.0 + positive / negative)
                mfi[j] = value / 100.0

    for k in RETURN_LAGS:
        lag = out[f"LAG_RETURN__K{k}"]
        for j in range(k, n):
            lag[j] = math.log(close[j] / close[j - k])

    return out


def compute_ta_candidates(arm: ArmBars) -> TACandidateResult:
    """Compute all 94 frozen TA candidates and aligned next-hour targets."""
    n = len(arm.bars)
    if n == 0:
        raise PSR01BError("empty arm")
    matrix = np.full((n, len(CANDIDATE_NAMES)), np.nan, dtype=np.float64)

    slices = _segment_slices(arm)
    name_to_col = {name: i for i, name in enumerate(CANDIDATE_NAMES)}
    for sl in slices:
        bars = arm.bars[sl]
        open_ = np.asarray([float(b.open) for b in bars], dtype=np.float64)
        high = np.asarray([float(b.high) for b in bars], dtype=np.float64)
        low = np.asarray([float(b.low) for b in bars], dtype=np.float64)
        close = np.asarray([float(b.close) for b in bars], dtype=np.float64)
        volume = np.asarray([float(b.volume) for b in bars], dtype=np.float64)
        if not (
            np.isfinite(open_).all()
            and np.isfinite(high).all()
            and np.isfinite(low).all()
            and np.isfinite(close).all()
            and np.isfinite(volume).all()
        ):
            raise PSR01BError("nonfinite OHLCV input")
        features = _compute_segment(open_, high, low, close, volume)
        for name, values in features.items():
            matrix[sl, name_to_col[name]] = values

    segment_indices = np.asarray(arm.segment_indices, dtype=np.int64)
    deployable = segment_indices >= GLOBAL_CONTIGUOUS_TRANSITIONS
    if np.any(deployable & ~np.isfinite(matrix).all(axis=1)):
        raise PSR01BError("deployable TA candidate row is nonfinite")

    target = np.full(n, np.nan, dtype=np.float64)
    for i in range(n - 1):
        contiguous = (
            arm.segment_ids[i + 1] == arm.segment_ids[i]
            and arm.segment_indices[i + 1] == arm.segment_indices[i] + 1
            and arm.bars[i + 1].timestamp - arm.bars[i].timestamp == timedelta(hours=1)
        )
        target[i] = (
            math.log(float(arm.bars[i + 1].close) / float(arm.bars[i].close))
            if contiguous
            else np.nan
        )

    return TACandidateResult(
        CANDIDATE_NAMES,
        CANDIDATE_FAMILIES,
        matrix,
        target,
        deployable,
    )


def spearman_block_correlation(feature: Sequence[float], target: Sequence[float]) -> float | None:
    x = np.asarray(feature, dtype=np.float64)
    y = np.asarray(target, dtype=np.float64)
    if x.ndim != 1 or y.ndim != 1 or len(x) != len(y):
        raise PSR01BError("Spearman vectors must be aligned 1-D arrays")
    finite = np.isfinite(x) & np.isfinite(y)
    if int(np.count_nonzero(finite)) < 100:
        return None
    corr = float(spearmanr(x[finite], y[finite]).statistic)
    return corr if np.isfinite(corr) else None


def select_group_from_block_correlations(
    candidate_names: Sequence[str],
    correlations: Mapping[str, Sequence[float | None]],
) -> tuple[str, dict[str, float]]:
    """Apply the frozen common-four-block rank universe to one group."""
    names = tuple(candidate_names)
    if not names:
        raise PSR01BError("selection group is empty")
    common = [
        name
        for name in names
        if name in correlations
        and len(correlations[name]) == 4
        and all(v is not None and np.isfinite(float(v)) for v in correlations[name])
    ]
    if not common:
        raise PSR01BError("selection group has no common-four-block eligible candidate")

    ranks: dict[str, list[int]] = {name: [] for name in common}
    for block in range(4):
        ordered = sorted(
            common,
            key=lambda name: (-abs(float(correlations[name][block])), name),
        )
        for rank, name in enumerate(ordered, start=1):
            ranks[name].append(rank)
    average = {name: float(np.mean(values)) for name, values in ranks.items()}
    winner = sorted(common, key=lambda name: (average[name], name))[0]
    return winner, average


def _add_months(dt: datetime, months: int) -> datetime:
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise PSR01BError("training boundary must be timezone-aware")
    if dt.utcoffset().total_seconds() != 0:
        raise PSR01BError("training boundary must be UTC")
    total = dt.year * 12 + (dt.month - 1) + months
    year, month0 = divmod(total, 12)
    month = month0 + 1
    day = min(dt.day, calendar.monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def select_four_block_features(
    arm: ArmBars,
    candidates: TACandidateResult,
    *,
    train_start: datetime,
    train_end: datetime,
) -> FeatureSelectionResult:
    """Select one feature per frozen group from four 3-calendar-month blocks."""
    if len(arm.bars) != len(candidates.matrix):
        raise PSR01BError("candidate rows do not align to arm bars")
    if _add_months(train_start, 12) != train_end:
        raise PSR01BError("training window must be exactly 12 calendar months")

    blocks = [(_add_months(train_start, 3 * i), _add_months(train_start, 3 * (i + 1))) for i in range(4)]
    stamps = [b.timestamp.astimezone(timezone.utc) for b in arm.bars]
    name_to_col = {name: i for i, name in enumerate(candidates.names)}

    correlations: dict[str, tuple[float | None, float | None, float | None, float | None]] = {}
    for name in candidates.names:
        col = candidates.matrix[:, name_to_col[name]]
        vals: list[float | None] = []
        for start, end in blocks:
            mask = np.array(
                [
                    start <= stamp < end and start <= stamp + timedelta(hours=1) < end
                    for stamp in stamps
                ],
                dtype=bool,
            )
            vals.append(spearman_block_correlation(col[mask], candidates.target_next_hour[mask]))
        correlations[name] = tuple(vals)  # type: ignore[assignment]

    selected_by_group: dict[str, str] = {}
    average_ranks: dict[str, dict[str, float]] = {}
    for group in GROUP_ORDER:
        allowed_families = GROUPS[group]
        names = [
            name
            for name, family in zip(candidates.names, candidates.families)
            if family in allowed_families
        ]
        winner, averages = select_group_from_block_correlations(names, correlations)
        selected_by_group[group] = winner
        average_ranks[group] = averages

    selected_names = tuple(selected_by_group[group] for group in GROUP_ORDER)
    selected_matrix = np.column_stack([candidates.matrix[:, name_to_col[name]] for name in selected_names])
    finite_correlations = {
        name: tuple(float(v) for v in values)  # type: ignore[arg-type]
        for name, values in correlations.items()
        if all(v is not None for v in values)
    }
    return FeatureSelectionResult(
        selected_by_group,
        selected_names,
        selected_matrix,
        average_ranks,
        finite_correlations,
    )
