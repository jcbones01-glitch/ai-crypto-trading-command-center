"""Monthly 10-month moving-average trend rule (Faber 2007).

For each asset: if the latest completed monthly close is above the average of
the last 10 monthly closes, hold an equal share of the account in it;
otherwise hold that share in cash.
"""
from __future__ import annotations

import math
from typing import Mapping, Sequence

from .config import LOOKBACK_MONTHS


def is_uptrend(monthly_closes: Sequence[float], lookback: int = LOOKBACK_MONTHS) -> bool:
    closes = [float(x) for x in monthly_closes]
    if len(closes) < lookback:
        raise ValueError(f"need at least {lookback} monthly closes, got {len(closes)}")
    window = closes[-lookback:]
    if any(not math.isfinite(x) or x <= 0 for x in window):
        raise ValueError("monthly closes must be finite and positive")
    return window[-1] > sum(window) / lookback


def target_weights(
    closes_by_symbol: Mapping[str, Sequence[float]],
    universe: Sequence[str],
    lookback: int = LOOKBACK_MONTHS,
) -> dict[str, float]:
    """Return weight per symbol (0 or 1/N).  Missing weight is cash."""
    if not universe:
        raise ValueError("universe is empty")
    share = 1.0 / len(universe)
    weights: dict[str, float] = {}
    for symbol in universe:
        if symbol not in closes_by_symbol:
            raise ValueError(f"missing price history for {symbol}")
        weights[symbol] = share if is_uptrend(closes_by_symbol[symbol], lookback) else 0.0
    return weights
