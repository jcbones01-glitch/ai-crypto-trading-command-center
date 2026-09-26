"""PSR-01B frozen numerical/accounting primitives.

This module is intentionally source-agnostic.  It must not open market archives,
perform network I/O, or access AMS-DEP Validation/OOS.  It implements only
deterministic primitives from PSR-01B bounded specification revision 4 so they
can be exercised with synthetic/offline fixtures before any empirical
authorization exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import math
import struct
from typing import Iterable, Sequence

import numpy as np


FORECAST_PREFIX = b"PSR01B_FORECAST_VECTOR_V1\x00"
ARM_ORDER = ("PAPER_FILL", "PROJECT_GAP_PRESERVING")
TRANSACTION_COST = 0.001
COST_LAMBDA = 2.0
RISK_FREE_ANNUAL = 0.042
HOURS_PER_YEAR = 8760.0
BOOTSTRAP_ROOT = 2026092402


class PSR01BError(RuntimeError):
    """Fail-closed PSR-01B numerical contract violation."""


@dataclass(frozen=True)
class StrategyResult:
    returns: np.ndarray
    positions: np.ndarray
    turnover: float
    completed_trades: int


@dataclass(frozen=True)
class BootstrapResult:
    available: bool
    all_record_mean: float
    inference_universe_mean: float | None
    eligible_segments: int
    p_value: float | None
    ci_95: tuple[float, float] | None
    sharpe_difference_available: bool
    observed_inference_sharpe_difference: float | None
    sharpe_difference_ci_95: tuple[float, float] | None


def seed_from_coordinates(*coordinates: int) -> int:
    if not coordinates or any(isinstance(x, bool) or not isinstance(x, (int, np.integer)) for x in coordinates):
        raise PSR01BError("seed coordinates must be non-empty integers")
    state = np.random.SeedSequence([int(x) for x in coordinates]).generate_state(
        1, dtype=np.uint32
    )
    return int(state[0])


def split_origin_eligible(origin: datetime, split_start: datetime, split_end: datetime) -> bool:
    if any(v.tzinfo is None for v in (origin, split_start, split_end)):
        raise PSR01BError("split datetimes must be timezone-aware")
    if not split_start < split_end:
        raise PSR01BError("invalid split")
    target_label = origin + timedelta(hours=1)
    return split_start <= origin < split_end and split_start <= target_label < split_end


def forecast_vector_sha256(
    timestamps_unix_seconds: Sequence[int], forecasts: Sequence[float]
) -> str:
    ts = np.asarray(timestamps_unix_seconds)
    fc = np.asarray(forecasts, dtype=np.float64)
    if ts.ndim != 1 or fc.ndim != 1 or len(ts) != len(fc):
        raise PSR01BError("forecast timestamps/values must be aligned 1-D vectors")
    if len(ts) and (
        not np.issubdtype(ts.dtype, np.integer)
        or np.any(np.diff(ts.astype(np.int64)) <= 0)
    ):
        raise PSR01BError("forecast timestamps must be strict ascending integer Unix seconds")
    if not np.isfinite(fc).all():
        raise PSR01BError("forecast vector must be finite")

    payload = bytearray(FORECAST_PREFIX)
    payload.extend(struct.pack("<Q", len(fc)))
    for stamp, value in zip(ts.astype(np.int64), fc):
        payload.extend(struct.pack("<qd", int(stamp), float(value)))
    return hashlib.sha256(bytes(payload)).hexdigest()


def _validated_vector(values: Sequence[float], name: str) -> np.ndarray:
    out = np.asarray(values, dtype=np.float64)
    if out.ndim != 1 or not np.isfinite(out).all():
        raise PSR01BError(f"{name} must be a finite 1-D vector")
    return out


def _segment_strategy(
    forecasts: np.ndarray,
    realized_log_returns: np.ndarray,
    *,
    cost_aware: bool,
    terminal_liquidation: bool = True,
) -> StrategyResult:
    if len(forecasts) != len(realized_log_returns):
        raise PSR01BError("forecast/realized vectors must align")
    if len(forecasts) == 0:
        raise PSR01BError("empty evaluation segment")

    previous_position = 0
    positions = np.zeros(len(forecasts), dtype=np.int8)
    net = np.zeros(len(forecasts), dtype=np.float64)
    turnover = 0.0
    completed = 0

    for i, (forecast, log_return) in enumerate(zip(forecasts, realized_log_returns)):
        desired = 1 if forecast > 0.0 else 0
        if cost_aware:
            threshold = COST_LAMBDA * TRANSACTION_COST * abs(desired - previous_position)
            position = desired if abs(forecast) > threshold else previous_position
        else:
            position = desired

        change = abs(position - previous_position)
        turnover += change
        if previous_position == 1 and position == 0:
            completed += 1
        net[i] = position * math.expm1(float(log_return)) - TRANSACTION_COST * change
        positions[i] = position
        previous_position = position

    if terminal_liquidation and previous_position:
        turnover += 1.0
        completed += 1
        net[-1] -= TRANSACTION_COST

    if not np.isfinite(net).all():
        raise PSR01BError("nonfinite strategy return")
    return StrategyResult(net, positions, float(turnover), int(completed))


def evaluate_strategy_segments(
    forecast_segments: Sequence[Sequence[float]],
    realized_log_return_segments: Sequence[Sequence[float]],
    *,
    rule: str,
) -> StrategyResult:
    if rule not in {"BASELINE_SIGN", "COST_AWARE"}:
        raise PSR01BError("unregistered strategy rule")
    if len(forecast_segments) != len(realized_log_return_segments) or not forecast_segments:
        raise PSR01BError("segments must be non-empty and aligned")

    all_returns: list[np.ndarray] = []
    all_positions: list[np.ndarray] = []
    turnover = 0.0
    completed = 0
    for f_raw, r_raw in zip(forecast_segments, realized_log_return_segments):
        f = _validated_vector(f_raw, "forecasts")
        r = _validated_vector(r_raw, "realized_log_returns")
        result = _segment_strategy(f, r, cost_aware=(rule == "COST_AWARE"))
        all_returns.append(result.returns)
        all_positions.append(result.positions)
        turnover += result.turnover
        completed += result.completed_trades

    return StrategyResult(
        np.concatenate(all_returns),
        np.concatenate(all_positions),
        float(turnover),
        int(completed),
    )


def performance_metrics(returns: Sequence[float]) -> dict[str, float | int | None]:
    r = _validated_vector(returns, "returns")
    n = len(r)
    if n == 0:
        raise PSR01BError("empty return sequence")
    if np.any(1.0 + r <= 0.0):
        raise PSR01BError("wealth would be nonpositive")

    wealth = np.cumprod(1.0 + r)
    total_return = float(wealth[-1] - 1.0)
    arc = float((wealth[-1] ** (HOURS_PER_YEAR / n)) - 1.0)
    asd = float(math.sqrt(HOURS_PER_YEAR) * np.std(r, ddof=1)) if n >= 2 else float("nan")
    sharpe = None
    if np.isfinite(asd) and asd > 0.0:
        sharpe = float((arc - RISK_FREE_ANNUAL) / asd)

    equity = np.concatenate(([1.0], wealth))
    running_peak = np.maximum.accumulate(equity)
    drawdown = equity / running_peak - 1.0
    mdd = float(np.min(drawdown))
    return {
        "N": n,
        "total_return": total_return,
        "ARC": arc,
        "ASD": asd,
        "SHARPE": sharpe,
        "max_drawdown": mdd,
    }


def holm_two(raw_p_by_arm: dict[str, float]) -> dict[str, dict[str, float | bool]]:
    if set(raw_p_by_arm) != set(ARM_ORDER):
        raise PSR01BError("Holm family must contain exactly the two registered arms")
    pairs: list[tuple[float, int, str]] = []
    for idx, arm in enumerate(ARM_ORDER):
        p = float(raw_p_by_arm[arm])
        if not np.isfinite(p) or p < 0.0 or p > 1.0:
            raise PSR01BError("invalid raw p-value")
        pairs.append((p, idx, arm))
    pairs.sort(key=lambda x: (x[0], x[1]))

    adjusted_sorted: list[float] = []
    running = 0.0
    m = 2
    for j, (p, _, _) in enumerate(pairs):
        running = max(running, (m - j) * p)
        adjusted_sorted.append(min(1.0, running))

    out: dict[str, dict[str, float | bool]] = {}
    for (_, _, arm), adj in zip(pairs, adjusted_sorted):
        out[arm] = {"adjusted_p": float(adj), "reject": bool(adj <= 0.05)}
    return {arm: out[arm] for arm in ARM_ORDER}


def _circular_indices(rng: np.random.Generator, n: int, block_length: int) -> np.ndarray:
    blocks = math.ceil(n / block_length)
    starts = rng.integers(0, n, size=blocks)
    pieces = [(start + np.arange(block_length)) % n for start in starts]
    return np.concatenate(pieces)[:n]


def paired_segment_bootstrap(
    baseline_segments: Sequence[Sequence[float]],
    cost_aware_segments: Sequence[Sequence[float]],
    *,
    block_hours: int,
    arm_index: int,
    draws: int = 10_000,
) -> BootstrapResult:
    if block_hours not in {24, 72, 168}:
        raise PSR01BError("unregistered block length")
    if arm_index not in {0, 1}:
        raise PSR01BError("invalid arm index")
    if not isinstance(draws, int) or draws <= 0:
        raise PSR01BError("draws must be a positive integer")
    if len(baseline_segments) != len(cost_aware_segments) or not baseline_segments:
        raise PSR01BError("paired segments must be non-empty and aligned")

    pairs: list[tuple[np.ndarray, np.ndarray]] = []
    all_diffs: list[np.ndarray] = []
    eligible: list[tuple[np.ndarray, np.ndarray]] = []
    for b_raw, c_raw in zip(baseline_segments, cost_aware_segments):
        b = _validated_vector(b_raw, "baseline segment")
        c = _validated_vector(c_raw, "cost-aware segment")
        if len(b) != len(c) or len(b) == 0:
            raise PSR01BError("paired segment lengths must align and be positive")
        pairs.append((b, c))
        d = c - b
        all_diffs.append(d)
        if len(d) >= 2 * block_hours:
            eligible.append((b, c))

    all_record_mean = float(np.mean(np.concatenate(all_diffs)))
    if len(eligible) < 2:
        return BootstrapResult(
            False,
            all_record_mean,
            None,
            len(eligible),
            None,
            None,
            False,
            None,
            None,
        )

    observed_diffs = np.concatenate([c - b for b, c in eligible])
    observed_mean = float(np.mean(observed_diffs))
    rng = np.random.Generator(
        np.random.PCG64(seed_from_coordinates(BOOTSTRAP_ROOT, block_hours, arm_index))
    )

    observed_baseline = np.concatenate([b for b, _ in eligible])
    observed_cost_aware = np.concatenate([c for _, c in eligible])
    observed_baseline_metrics = performance_metrics(observed_baseline)
    observed_cost_aware_metrics = performance_metrics(observed_cost_aware)
    observed_baseline_sharpe = observed_baseline_metrics["SHARPE"]
    observed_cost_aware_sharpe = observed_cost_aware_metrics["SHARPE"]
    observed_sharpe_difference = None
    if observed_baseline_sharpe is not None and observed_cost_aware_sharpe is not None:
        observed_sharpe_difference = float(observed_cost_aware_sharpe - observed_baseline_sharpe)

    centered_draws = np.empty(draws, dtype=np.float64)
    uncentered_draws = np.empty(draws, dtype=np.float64)
    sharpe_difference_draws = np.full(draws, np.nan, dtype=np.float64)
    sharpe_available = observed_sharpe_difference is not None

    for rep in range(draws):
        centered_parts: list[np.ndarray] = []
        raw_diff_parts: list[np.ndarray] = []
        raw_baseline_parts: list[np.ndarray] = []
        raw_cost_aware_parts: list[np.ndarray] = []
        for b, c in eligible:
            d = c - b
            idx = _circular_indices(rng, len(d), block_hours)
            centered_parts.append((d - observed_mean)[idx])
            raw_diff_parts.append(d[idx])
            # Revision-4 requires identical sampled indices on the uncentered
            # paired strategy return records for complementary Sharpe evidence.
            raw_baseline_parts.append(b[idx])
            raw_cost_aware_parts.append(c[idx])

        centered_draws[rep] = np.mean(np.concatenate(centered_parts))
        uncentered_draws[rep] = np.mean(np.concatenate(raw_diff_parts))

        if sharpe_available:
            baseline_draw = np.concatenate(raw_baseline_parts)
            cost_aware_draw = np.concatenate(raw_cost_aware_parts)
            baseline_metrics = performance_metrics(baseline_draw)
            cost_aware_metrics = performance_metrics(cost_aware_draw)
            baseline_sharpe = baseline_metrics["SHARPE"]
            cost_aware_sharpe = cost_aware_metrics["SHARPE"]
            if baseline_sharpe is None or cost_aware_sharpe is None:
                sharpe_available = False
            else:
                sharpe_difference_draws[rep] = float(cost_aware_sharpe - baseline_sharpe)

    p_value = float((1 + np.count_nonzero(centered_draws >= observed_mean)) / (draws + 1))
    q = np.quantile(uncentered_draws, [0.025, 0.975], method="linear")

    sharpe_ci = None
    if sharpe_available and np.isfinite(sharpe_difference_draws).all():
        sharpe_q = np.quantile(
            sharpe_difference_draws,
            [0.025, 0.975],
            method="linear",
        )
        sharpe_ci = (float(sharpe_q[0]), float(sharpe_q[1]))
    else:
        sharpe_available = False

    return BootstrapResult(
        True,
        all_record_mean,
        observed_mean,
        len(eligible),
        p_value,
        (float(q[0]), float(q[1])),
        bool(sharpe_available),
        observed_sharpe_difference if sharpe_available else None,
        sharpe_ci,
    )


def classify_success(arm_summaries: dict[str, dict[str, float | int | None]]) -> str:
    if set(arm_summaries) != set(ARM_ORDER):
        raise PSR01BError("success classification requires both registered arms")

    required = (
        "all_record_mean",
        "inference_universe_mean",
        "eligible_primary_segments",
        "primary_p_value",
        "cost_aware_turnover",
        "baseline_turnover",
        "cost_aware_completed_trades",
        "cost_aware_sharpe",
        "baseline_sharpe",
    )
    for arm in ARM_ORDER:
        s = arm_summaries[arm]
        missing = [key for key in required if key not in s]
        if missing:
            raise PSR01BError(
                f"success classification missing required fields for {arm}: {missing}"
            )
        # Revision-4 explicitly makes unavailable primary inference or unavailable
        # Sharpe evidence unable to satisfy a success criterion.  These are
        # scientific non-replication outcomes, not runtime errors.
        if int(s["eligible_primary_segments"]) < 2:
            return "BOUNDED_H2_NOT_REPLICATED"
        if any(
            s[key] is None
            for key in (
                "inference_universe_mean",
                "primary_p_value",
                "cost_aware_sharpe",
                "baseline_sharpe",
            )
        ):
            return "BOUNDED_H2_NOT_REPLICATED"

    raw_ps = {arm: float(arm_summaries[arm]["primary_p_value"]) for arm in ARM_ORDER}
    holm = holm_two(raw_ps)

    passed = True
    for arm in ARM_ORDER:
        s = arm_summaries[arm]
        passed &= float(s["all_record_mean"]) > 0.0
        passed &= float(s["inference_universe_mean"]) > 0.0
        passed &= bool(holm[arm]["reject"])
        passed &= float(s["cost_aware_turnover"]) < float(s["baseline_turnover"])
        passed &= int(s["cost_aware_completed_trades"]) >= 20
        passed &= float(s["cost_aware_sharpe"]) - float(s["baseline_sharpe"]) > 0.0
    return "BOUNDED_H2_REPLICATION" if passed else "BOUNDED_H2_NOT_REPLICATED"
