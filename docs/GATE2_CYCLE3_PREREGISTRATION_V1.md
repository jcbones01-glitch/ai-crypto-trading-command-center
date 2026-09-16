# Gate 2 Cycle 3 — Preregistration V1

## Status

**FROZEN PROSPECTIVE REGISTRATION — BEFORE EVIDENCE GENERATION**

This cycle is new research. It does not modify, rescue, or retune HYP-0001 through HYP-0010. Development evidence is generated only inside the existing Gate 2 firewall.

## Firewall

- Assets: BTCUSDT and ETHUSDT, Binance Spot, 1-hour bars.
- Development: `[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`.
- Validation: `[2022-01-01T00:00:00Z, 2024-01-01T00:00:00Z)` inaccessible.
- Locked OOS: `[2024-01-01T00:00:00Z, 2026-01-01T00:00:00Z)` inaccessible.
- Gate 1A-certified observations only; continuity breaks are never bridged.
- Signal information ends at close of t; delay 1/2 enters at open t+1/t+2.
- Baseline commission 10 bps/side and slippage 5 bps/side; registered stress cases are unchanged.
- Long-only spot, one active position, one-bar hold, no intrabar fills.
- Every registered cell is evaluated; no post-result parameter selection.

## HYP-0011 — Close-Location Reversal

Mechanism: after a materially negative completed bar, a strong recovery close within the same current bar may contain short-horizon reversal information.

At signal t:
- return[t-1] <= -R;
- close[t] > open[t];
- `(close[t]-low[t])/(high[t]-low[t]) >= L` (close location);
- signal uses no future data.

Grid: R = 0.5%, 1%, 1.5% × L = 0.75, 0.85, 0.95 = 9 cells.
Baseline: R=1%, L=0.85.

Entry: next eligible open; exit: close of that same eligible bar.

## HYP-0012 — Range-Expansion Continuation

Mechanism: an unusually large current range with a strong upside close may indicate directional information not captured by close-to-close momentum alone.

At signal t:
- current true range `(high-low)/close[t-1]` >= K times the median of the previous N completed hourly ranges;
- close location >= L;
- no lookahead.

Grid: N = 24, 48 × K = 2, 3, 4 × L = 0.75, 0.85 = 12 cells.
Baseline: N=24, K=3, L=0.85.

## HYP-0013 — Trend-Filter Pullback Recovery

Mechanism: a positive medium-horizon trend followed by a downside pullback bar and recovery close may contain short-horizon continuation information.

At signal t:
- close[t-24] < close[t-1] (positive 24-hour trend);
- return[t-1] <= -P (the completed pullback is the prior bar);
- close[t] > open[t];
- close[t] remains above close[t-24];
- current close location `(close[t]-low[t])/(high[t]-low[t]) >= L`.

Grid: P = 0.5%, 1%, 1.5% × trend lookback = 24, 48 × recovery close-location L = 0.5, 0.7 = 12 cells, where the trend anchor is the selected lookback before the pullback.
Baseline: P=1%, trend lookback=24, L=0.7.

## Robustness

For each candidate: parameter neighborhood, fee/slippage stress, 1/2-bar timing, fixed bull/neutral/bear regime segmentation, BTC/ETH reporting, leave-one-segment-out, concentration, drawdown/recovery, and cash/buy-and-hold benchmarks.

Errors are recorded, not omitted. A candidate cannot enter Validation unless every frozen Gate 2 Development promotion criterion passes. Validation cannot rescue failed Development.

## Logical-integrity rule

All signal predicates must be jointly satisfiable on the same bar. A zero-event result caused by contradictory predicates is classified as registration/implementation invalidity, not economic evidence.

## Closure

Any material change to a hypothesis requires a new hypothesis ID/version and a new prospective registration.