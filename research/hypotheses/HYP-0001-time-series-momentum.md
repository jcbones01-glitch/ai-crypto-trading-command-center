# HYP-0001 — Time-Series Momentum

## Classification

- Evidence status: HYPOTHESIS
- Research stage: DEVELOPMENT
- Market: Spot
- Assets: BTCUSDT, ETHUSDT
- Timeframe: 1h

## Falsifiable statement

After accounting for explicit transaction costs and slippage, a simple long-only time-series momentum rule based on a fixed 168-hour trailing return and a 24-hour confirmation can produce risk-adjusted performance better than cash and materially competitive with buy-and-hold during the Development period.

## Why it might exist

Persistent directional moves can create short-horizon trend continuation. This is a hypothesis, not an established edge.

## Pre-registered model

- Signal at bar close using only information available through that close.
- Enter/hold long when the 168-hour close-to-close return is positive AND the 24-hour return is positive.
- Otherwise target 0% invested.
- Position sizing: 100% of equity when both conditions are true; 0% otherwise.
- No leverage; spot only.
- No stop or target beyond the signal exit.
- Required lookback: 168 bars.

## Parameters

- Momentum lookback: 168h (fixed for initial test)
- Confirmation lookback: 24h (fixed for initial test)
- Search space: none for the initial pre-registered experiment.

## Costs and execution

- Commission: 10 bps per side for the initial stress-case experiment.
- Slippage: 5 bps per side for the initial stress-case experiment.
- Fill timing: next bar OPEN after the signal bar closes; no same-bar execution or intrabar assumptions.
- Liquidity: no unlimited-liquidity claim; sensitivity testing required.

## Research plan

Development: 2017-08-17 to 2022-01-01.
Validation: 2022-01-01 to 2024-01-01 only after promotion.
OOS: LOCKED.

Primary metrics: total return, CAGR where meaningful, maximum drawdown, drawdown duration/recovery, trade count, turnover, volatility, and risk-adjusted return metrics supported by the research engine.

Benchmarks: buy-and-hold on the same eligible asset/segment and cash/no-position.

Robustness: parameter neighborhood, fee sensitivity, slippage sensitivity, execution-timing sensitivity, BTC/ETH transferability, regime segmentation, trade/sample review, drawdown/recovery, and benchmark comparison.

## Invalidation criteria

Reject or do not promote if the development result fails to beat the cash baseline after costs, has inadequate trade/sample support, depends on a narrow parameter choice, or fails material robustness tests.

## Decision

No result has been observed yet. This file registers the hypothesis before the backtest.
