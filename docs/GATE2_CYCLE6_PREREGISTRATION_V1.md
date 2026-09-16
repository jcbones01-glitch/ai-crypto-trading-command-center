# Gate 2 Cycle 6 — Prospective Preregistration V1

## Firewall
Development only: `[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`.
Validation `[2022-01-01T00:00:00Z, 2024-01-01T00:00:00Z)` and locked OOS `[2024-01-01T00:00:00Z, 2026-01-01T00:00:00Z)` are inaccessible.
BTCUSDT and ETHUSDT Binance Spot 1-hour Gate 1A-certified data only.
Signal uses information through close t; entry is delayed by 1 or 2 bars. Zero-delay is prohibited. Long-only spot, one active position, one-bar hold, explicit fees/slippage, no intrabar fills, and no continuity-gap bridging.

## Frozen hypotheses

### HYP-0020 — UTC-Hour Conditional Continuation
At signal bar t: UTC hour is one of `{00,08,12,16,20}`; current candle is positive (`close[t] > open[t]`); current return from prior close is at least R; current close-location is at least L.
Grid: hour = 5 values × R = `{0.5%,1.0%}` × L = `{0.75,0.90}` = **20 cells**. Baseline: hour 00, R 0.5%, L 0.90.

### HYP-0021 — Directional Streak Exhaustion
At signal bar t: the previous K completed hourly returns are all positive; their cumulative return is at least R; current close-location is at most U.
Grid: K = `{3,4}` × R = `{0.5%,1.0%}` × U = `{0.25,0.50}` = **8 cells**. Baseline: K=3, R=0.5%, U=0.50.

### HYP-0022 — Body-Dominance Continuation
At signal bar t: current candle is positive; body/range is at least B; range divided by previous close is at least X; current body return `(close-open)/previous_close` is at least R.
Grid: B = `{0.60,0.80}` × X = `{0.5%,1.0%,2.0%}` × R = `{0.25%,0.5%}` = **12 cells**. Baseline: B=0.60, X=0.5%, R=0.25%.

## Execution and evidence rules
All 40 registered cells must be evaluated on both assets. Baseline costs are 10 bps commission per side and 5 bps directional slippage per side; registered stress cases and 1/2-bar delays are mandatory. No parameter additions/removals or post-result selection. Errors must be recorded, not silently omitted. A candidate must satisfy every frozen Gate 2 Development promotion criterion and then the complete robustness battery before Validation. Development success is not validation and does not authorize paper or live trading.
