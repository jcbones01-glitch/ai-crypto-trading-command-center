"""Simple offline monthly backtest for learning (no costs beyond a flat fee).

Compares the trend rule with buy-and-hold of the benchmark.  Results are for
understanding how the rule behaves, not proof that it will work.
"""
from __future__ import annotations

from typing import Mapping, Sequence

from .config import LOOKBACK_MONTHS
from .strategy import target_weights


def run_backtest(
    closes_by_symbol: Mapping[str, Sequence[float]],
    universe: Sequence[str],
    benchmark: str,
    lookback: int = LOOKBACK_MONTHS,
    cost_per_turnover: float = 0.001,
) -> dict:
    lengths = {len(closes_by_symbol[s]) for s in list(universe) + [benchmark]}
    if len(lengths) != 1:
        raise ValueError("all price series must have the same length")
    n = lengths.pop()
    if n <= lookback:
        raise ValueError("not enough months for the lookback")
    equity, bench = 1.0, 1.0
    peak, max_dd = 1.0, 0.0
    prev = {s: 0.0 for s in universe}
    for t in range(lookback - 1, n - 1):
        history = {s: closes_by_symbol[s][: t + 1] for s in universe}
        w = target_weights(history, universe, lookback)
        turnover = sum(abs(w[s] - prev[s]) for s in universe)
        month_ret = sum(
            w[s] * (closes_by_symbol[s][t + 1] / closes_by_symbol[s][t] - 1) for s in universe
        )
        equity *= 1 + month_ret - cost_per_turnover * turnover
        bench *= closes_by_symbol[benchmark][t + 1] / closes_by_symbol[benchmark][t]
        peak = max(peak, equity)
        max_dd = min(max_dd, equity / peak - 1)
        prev = w
    return {
        "months": n - lookback,
        "strategy_total_return": equity - 1,
        "benchmark_total_return": bench - 1,
        "strategy_max_drawdown": max_dd,
    }
