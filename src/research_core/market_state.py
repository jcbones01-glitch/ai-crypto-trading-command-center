from __future__ import annotations

from bisect import bisect_left, bisect_right, insort
from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence

from .data_interfaces import MarketBar

STATE_DEFINITION_VERSION = "AMS-V1"
PERCENTILE_REFERENCE_COUNT = 720
LOW_PERCENTILE = Decimal("0.20")
HIGH_PERCENTILE = Decimal("0.80")
VOLATILITY_WINDOW = 24
ACTIVITY_WINDOW = 24
TREND_WINDOW = 168
BULL_THRESHOLD = Decimal("0.10")
BEAR_THRESHOLD = Decimal("-0.10")


@dataclass(frozen=True)
class MarketState:
    timestamp: object
    volatility_state: str | None
    activity_state: str | None
    trend_state: str | None

    @property
    def complete(self) -> bool:
        return (
            self.volatility_state is not None
            and self.activity_state is not None
            and self.trend_state is not None
        )

    @property
    def composite(self) -> tuple[str, str, str] | None:
        if not self.complete:
            return None
        return (
            self.volatility_state,
            self.activity_state,
            self.trend_state,
        )


def _realized_volatility_24(bars: Sequence[MarketBar], i: int) -> Decimal | None:
    if i < VOLATILITY_WINDOW:
        return None
    total = Decimal("0")
    start = i - VOLATILITY_WINDOW + 1
    for j in range(start, i + 1):
        ratio = bars[j].close / bars[j - 1].close
        log_return = ratio.ln()
        total += log_return * log_return
    return total.sqrt()


def _aggregate_volume_24(bars: Sequence[MarketBar], i: int) -> Decimal | None:
    if i < ACTIVITY_WINDOW - 1:
        return None
    return sum(
        (bars[j].volume for j in range(i - ACTIVITY_WINDOW + 1, i + 1)),
        Decimal("0"),
    )


def _trend_return_168(bars: Sequence[MarketBar], i: int) -> Decimal | None:
    if i < TREND_WINDOW:
        return None
    return bars[i].close / bars[i - TREND_WINDOW].close - Decimal("1")


def _label_percentile(rank: Decimal, low_label: str, normal_label: str, high_label: str) -> str:
    if rank <= LOW_PERCENTILE:
        return low_label
    if rank >= HIGH_PERCENTILE:
        return high_label
    return normal_label


def _rolling_percentile_ranks(
    values: Sequence[Decimal | None],
    reference_count: int = PERCENTILE_REFERENCE_COUNT,
) -> list[Decimal | None]:
    """Return causal percentile ranks using only the preceding reference window.

    Rank at index i is count(reference <= current) / reference_count.
    The current observation is excluded from the reference set.
    A rank is unavailable unless all reference observations and current value exist.
    """
    if reference_count <= 0:
        raise ValueError("reference_count must be positive")

    out: list[Decimal | None] = [None] * len(values)
    first_valid = next((i for i, value in enumerate(values) if value is not None), None)
    if first_valid is None:
        return out

    first_i = first_valid + reference_count
    if first_i >= len(values):
        return out

    initial = values[first_i - reference_count:first_i]
    if any(value is None for value in initial):
        return out

    sorted_reference = sorted(value for value in initial if value is not None)
    if len(sorted_reference) != reference_count:
        return out

    denominator = Decimal(reference_count)

    for i in range(first_i, len(values)):
        current = values[i]
        if current is None:
            # Once a discontinuity is represented as a separate segment this should
            # not occur after warm-up; keep behavior safe and explicit.
            out[i] = None
        else:
            rank = Decimal(bisect_right(sorted_reference, current)) / denominator
            out[i] = rank

        if i + 1 >= len(values):
            continue

        outgoing = values[i - reference_count]
        incoming = values[i]
        if outgoing is None or incoming is None:
            # Rebuild only when a caller provides a sequence containing gaps.
            next_start = i + 1 - reference_count
            next_window = values[next_start:i + 1]
            if any(value is None for value in next_window):
                sorted_reference = []
            else:
                sorted_reference = sorted(value for value in next_window if value is not None)
            continue

        pos = bisect_left(sorted_reference, outgoing)
        if pos >= len(sorted_reference) or sorted_reference[pos] != outgoing:
            raise RuntimeError("rolling percentile reference removal failed")
        sorted_reference.pop(pos)
        insort(sorted_reference, incoming)

    return out


def build_market_states(bars: Sequence[MarketBar]) -> list[MarketState]:
    """Build AMS-V1 states for one already-certified continuous segment."""
    volatility_values = [_realized_volatility_24(bars, i) for i in range(len(bars))]
    activity_values = [_aggregate_volume_24(bars, i) for i in range(len(bars))]

    volatility_ranks = _rolling_percentile_ranks(volatility_values)
    activity_ranks = _rolling_percentile_ranks(activity_values)

    states: list[MarketState] = []
    for i, bar in enumerate(bars):
        vol_rank = volatility_ranks[i]
        activity_rank = activity_ranks[i]
        trend_return = _trend_return_168(bars, i)

        volatility_state = (
            _label_percentile(vol_rank, "VOL_LOW", "VOL_NORMAL", "VOL_HIGH")
            if vol_rank is not None
            else None
        )
        activity_state = (
            _label_percentile(activity_rank, "ACTIVITY_LOW", "ACTIVITY_NORMAL", "ACTIVITY_HIGH")
            if activity_rank is not None
            else None
        )
        trend_state = None
        if trend_return is not None:
            if trend_return > BULL_THRESHOLD:
                trend_state = "TREND_BULL"
            elif trend_return < BEAR_THRESHOLD:
                trend_state = "TREND_BEAR"
            else:
                trend_state = "TREND_NEUTRAL"

        states.append(
            MarketState(
                timestamp=bar.timestamp,
                volatility_state=volatility_state,
                activity_state=activity_state,
                trend_state=trend_state,
            )
        )
    return states
