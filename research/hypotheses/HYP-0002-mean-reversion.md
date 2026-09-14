# HYP-0002 — Short-Horizon Mean Reversion

## Classification

- Evidence status: HYPOTHESIS
- Research stage: DEVELOPMENT
- Market: Spot
- Assets: BTCUSDT, ETHUSDT
- Timeframe: 1h

## Falsifiable statement

After explicit costs and slippage, unusually negative short-horizon price deviations from a medium-term mean are followed often enough by positive reversals to make a simple long-only mean-reversion rule outperform cash and provide a useful risk-adjusted alternative to buy-and-hold during Development.

## Why it might exist

Temporary order-flow imbalance, liquidation pressure, or short-term overreaction may sometimes be followed by price normalization. This is a hypothesis, not an established edge.

## Pre-registered model

- Compute a 48-hour simple moving average of close.
- Compute the percentage deviation of close from that average.
- Enter/hold long when deviation <= -2.0%.
- Exit when deviation >= -0.5% or when the signal becomes invalid at a certified continuity boundary.
- Position sizing: 100% of equity while active; otherwise 0%.
- Spot only; no leverage.
- Required lookback: 48 bars.

## Parameters

- Mean lookback: 48h (fixed)
- Entry deviation: -2.0% (fixed)
- Exit deviation: -0.5% (fixed)
- Search space: none for initial experiment.

## Costs and execution

- Commission: 10 bps per side.
- Slippage: 5 bps per side.
- Fill timing: next bar OPEN after the signal bar closes; no same-bar execution or intrabar assumptions.
- Liquidity assumptions: no claim of unlimited liquidity.

## Research plan

Development: 2017-08-17 to 2022-01-01.
Validation: 2022-01-01 to 2024-01-01 only after promotion.
OOS: LOCKED.

Primary metrics: return, drawdown, trade count, turnover, volatility, and risk-adjusted metrics supported by the engine.
Benchmarks: same-period buy-and-hold and cash/no-position.
Robustness: parameter neighborhood, costs/slippage, timing, BTC/ETH transferability, regimes, sample size, drawdown/recovery, and benchmark comparison.

## Invalidation criteria

Reject or do not promote if the edge disappears after realistic costs, is driven by too few observations, is concentrated in one regime/asset, or is materially unstable under reasonable parameter perturbations.

## Decision

No result has been observed yet. This file registers the hypothesis before the backtest.
