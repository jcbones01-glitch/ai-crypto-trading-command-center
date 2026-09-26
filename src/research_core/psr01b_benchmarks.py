"""PSR-01B contextual benchmark accounting.

Benchmarks are descriptive only and never participate in the PSR-01B primary
success gate.  This module is source-agnostic and operates on synthetic/offline
return segments.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np

from .psr01b_core import (
    PSR01BError,
    StrategyResult,
    TRANSACTION_COST,
    evaluate_strategy_segments,
)


def buy_and_hold_segments(
    realized_log_return_segments: Sequence[Sequence[float]],
) -> StrategyResult:
    if not realized_log_return_segments:
        raise PSR01BError("buy-and-hold requires at least one evaluation segment")

    returns_parts = []
    position_parts = []
    turnover = 0.0
    completed = 0
    for raw in realized_log_return_segments:
        r = np.asarray(raw, dtype=np.float64)
        if r.ndim != 1 or len(r) == 0 or not np.isfinite(r).all():
            raise PSR01BError("benchmark return segment must be finite and non-empty")
        net = np.expm1(r)
        net = np.asarray(net, dtype=np.float64)
        # Enter from cash at first eligible origin and liquidate once at segment
        # end.  In the gap-preserving arm each model-eligible post-gap segment
        # is a fresh segment, so this also enforces the required flat gap.
        net[0] -= TRANSACTION_COST
        net[-1] -= TRANSACTION_COST
        returns_parts.append(net)
        position_parts.append(np.ones(len(r), dtype=np.int8))
        turnover += 2.0
        completed += 1

    return StrategyResult(
        np.concatenate(returns_parts),
        np.concatenate(position_parts),
        turnover,
        completed,
    )


def momentum_24h_segments(
    prior_24h_cumulative_log_return_segments: Sequence[Sequence[float]],
    realized_log_return_segments: Sequence[Sequence[float]],
) -> StrategyResult:
    if len(prior_24h_cumulative_log_return_segments) != len(realized_log_return_segments):
        raise PSR01BError("momentum signal/return segment count mismatch")
    if not prior_24h_cumulative_log_return_segments:
        raise PSR01BError("momentum benchmark requires at least one evaluation segment")

    signals = []
    for raw in prior_24h_cumulative_log_return_segments:
        x = np.asarray(raw, dtype=np.float64)
        if x.ndim != 1 or len(x) == 0 or not np.isfinite(x).all():
            raise PSR01BError("24h momentum signal must be finite and non-empty")
        signals.append(x)

    # BASELINE_SIGN implements the required unfiltered desired-position rule:
    # long iff cumulative prior-24h log return is positive, otherwise flat.
    return evaluate_strategy_segments(
        signals,
        realized_log_return_segments,
        rule="BASELINE_SIGN",
    )
