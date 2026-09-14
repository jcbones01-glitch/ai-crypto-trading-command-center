# HYP-0003 — Volatility/Range Breakout

## Classification

- Evidence status: HYPOTHESIS
- Research stage: DEVELOPMENT
- Market: Spot
- Assets: BTCUSDT, ETHUSDT
- Timeframe: 1h

## Falsifiable statement

A breakout above the prior 24-hour high, conditioned on elevated recent range expansion, can capture persistent directional moves well enough after costs and slippage to outperform cash and offer positive risk-adjusted performance during Development.

## Why it might exist

Expansion from compressed or recently expanding ranges can coincide with new information and sustained directional order flow. This is a hypothesis, not an established edge.

## Pre-registered model

- Calculate the highest close over the prior 24 completed bars, excluding the current bar.
- Calculate the current 24-hour high-low range divided by the 24-hour mean close as a simple normalized range measure.
- Enter long when current close is above the prior 24-bar highest close AND normalized 24-hour range is at least 1.0%.
- Exit when close falls below the 24-hour lowest close from the prior completed window.
- Position sizing: 100% of equity while active; otherwise 0%.
- Spot only; no leverage.
- Required lookback: 24 bars.

## Parameters

- Breakout lookback: 24h (fixed)
- Range lookback: 24h (fixed)
- Minimum normalized range: 1.0% (fixed)
- Search space: none for initial experiment.

## Costs and execution

- Commission: 10 bps per side.
- Slippage: 5 bps per side.
- Fill timing: deterministic bar-close execution according to the existing backtester.
- Liquidity assumptions: no unlimited-liquidity claim.

## Research plan

Development: 2017-08-17 to 2022-01-01.
Validation: 2022-01-01 to 2024-01-01 only after promotion.
OOS: LOCKED.

Primary metrics: return, drawdown, trade count, turnover, volatility, risk-adjusted metrics, and concentration.
Benchmarks: same-period buy-and-hold and cash/no-position.
Robustness: parameter neighborhood, fee/slippage, timing, BTC/ETH transferability, regime segmentation, sample size, drawdown/recovery, and benchmark comparison.

## Invalidation criteria

Reject or do not promote if profitability depends on a narrow threshold, collapses under realistic execution costs, is concentrated in a small number of trades/regimes, or fails material robustness tests.

## Decision

No result has been observed yet. This file registers the hypothesis before the backtest.
