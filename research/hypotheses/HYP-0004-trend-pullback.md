# HYP-0004 — Trend Pullback

## Classification

- Evidence status: HYPOTHESIS
- Research stage: DEVELOPMENT
- Market: Spot
- Assets: BTCUSDT, ETHUSDT
- Timeframe: 1h

## Falsifiable statement

When the medium-term trend is positive, temporary pullbacks that recover above a short-term moving average may provide better long-entry timing than continuous trend exposure, after explicit costs and slippage.

## Why it might exist

Trend persistence and temporary countertrend moves may coexist: pullbacks can reduce entry price relative to chasing extended moves. This is a hypothesis, not an established edge.

## Pre-registered model

- Compute EMA(200) and SMA(24) on close.
- Trend regime is positive when EMA(200) is rising versus its value 24 hours earlier and current close is above EMA(200).
- Enter long when the positive trend regime holds and current close crosses from below to above SMA(24).
- Exit when close falls below SMA(24) or the positive trend regime becomes false.
- Position sizing: 100% of equity while active; otherwise 0%.
- Spot only; no leverage.
- Required lookback: 224 bars (200-bar EMA plus 24-hour slope comparison).

## Parameters

- Trend EMA: 200h (fixed)
- Trend slope comparison: 24h (fixed)
- Pullback/trigger SMA: 24h (fixed)
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

Reject or do not promote if the rule is not reproducible, materially underperforms both relevant baselines without a compensating risk advantage, or is unstable under reasonable parameter and execution perturbations.

## Decision

No result has been observed yet. This file registers the hypothesis before the backtest.
