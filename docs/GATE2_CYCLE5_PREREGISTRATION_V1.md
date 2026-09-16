# Gate 2 Cycle 5 — Preregistration V1

## Status

**FROZEN PROSPECTIVE REGISTRATION — BEFORE EVIDENCE GENERATION**

Cycle 5 is new research. It does not modify, rescue, or retune HYP-0001 through HYP-0016.

## Firewall

- Assets: BTCUSDT and ETHUSDT, Binance Spot, 1-hour bars.
- Development: `[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`.
- Validation: `[2022-01-01T00:00:00Z, 2024-01-01T00:00:00Z)` inaccessible.
- Locked OOS: `[2024-01-01T00:00:00Z, 2026-01-01T00:00:00Z)` inaccessible.
- Gate 1A-certified observations only; continuity breaks are never bridged.
- Signal information ends at close t; delay 1/2 enters at open t+1/t+2.
- Baseline commission 10 bps/side and slippage 5 bps/side; registered stress cases are unchanged.
- Long-only spot, one active position, one-bar hold, no intrabar fills.
- Every registered cell is evaluated; no post-result parameter selection.

## HYP-0017 — Gap-Adjusted Bullish Continuation

Mechanism: a positive open-to-prior-close gap followed by a bullish, high-close-location bar may contain short-horizon continuation information.

At signal t:
- `open[t] / close[t-1] - 1 >= G`;
- `close[t] > open[t]`;
- current close-location `(close[t]-low[t])/(high[t]-low[t]) >= L`;
- no future information.

Grid: G = 0.25%, 0.5%, 1% × L = 0.75, 0.90 = **6 cells**.
Baseline: G=0.5%, L=0.90.

Entry: next eligible open; exit: close of that same eligible bar.

## HYP-0018 — Three-Bar Directional Persistence

Mechanism: three consecutive positive completed hourly returns with sufficient cumulative displacement and a strong current close may contain short-horizon continuation information.

At signal t:
- `close[t-3] < close[t-2] < close[t-1] < close[t]`;
- `close[t]/close[t-3] - 1 >= T`;
- current close-location >= L;
- no future information.

Grid: T = 0.5%, 1%, 2% × L = 0.75, 0.90 = **6 cells**.
Baseline: T=1%, L=0.90.

Entry: next eligible open; exit: close of that same eligible bar.

## HYP-0019 — Low-Volume Breakout

Mechanism: a breakout from a recent high while current volume is not elevated may distinguish price expansion that does not require a volume shock from prior volume-confirmed continuation hypotheses.

At signal t:
- `close[t] >= max(close[t-N] ... close[t-1]) * (1+B)`;
- `volume[t] <= V * median(volume[t-N] ... volume[t-1])`;
- current close-location >= L;
- no future information.

Grid: N = 12, 24 × B = 0%, 0.25% × V = 0.75, 1.0 × L = 0.75, 0.90 = **16 cells**.
Baseline: N=24, B=0.25%, V=0.75, L=0.90.

Entry: next eligible open; exit: close of that same eligible bar.

## Registered scope

Total unique parameter cells: **28** (6 + 6 + 16). Every cell is frozen before evidence generation.

## Costs and timing

Every registered parameter cell is evaluated at baseline cost and across the frozen fee/slippage stress cases. Baseline 1-bar and 2-bar-delay timing are evaluated. Signal-to-entry timing is causal; zero-delay is prohibited.

## Robustness

For any candidate that satisfies mandatory Development economics, the fixed battery is required: parameter neighborhood, fee/slippage stress, 1/2-bar timing, fixed bull/neutral/bear regime segmentation, BTC/ETH transferability, leave-one-segment-out, concentration, drawdown/recovery, and cash/buy-and-hold benchmarks.

No robustness dimension may be added or removed after seeing results. A candidate cannot enter Validation unless every frozen Gate 2 Development promotion criterion passes.

## Logical-integrity rule

All signal predicates must be jointly satisfiable. A zero-event result caused by contradictory predicates is implementation/registration invalidity, not economic evidence.

## Closure

Any material change to a hypothesis requires a new hypothesis ID/version and a new prospective registration. Validation and locked OOS remain inaccessible during Cycle 5 Development research.