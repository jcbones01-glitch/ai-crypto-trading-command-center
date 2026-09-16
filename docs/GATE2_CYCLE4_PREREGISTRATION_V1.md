# Gate 2 Cycle 4 — Preregistration V1

## Status

**FROZEN PROSPECTIVE REGISTRATION — BEFORE EVIDENCE GENERATION**

Cycle 4 is new research. It does not modify, rescue, or retune HYP-0001 through HYP-0013.

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

## HYP-0014 — Inside-Bar Breakout Continuation

Mechanism: a compressed inside-bar structure followed by an upside close beyond the prior inside-bar high may contain short-horizon continuation information.

At signal t:
- `high[t-1] <= high[t-2]`;
- `low[t-1] >= low[t-2]`;
- `close[t] >= high[t-1] * (1+B)`;
- current close-location `(close[t]-low[t])/(high[t]-low[t]) >= L`;
- no future information.

Grid: B = 0%, 0.25%, 0.5% × L = 0.75, 0.85 = **6 cells**.
Baseline: B=0.25%, L=0.85.

Entry: next eligible open; exit: close of that same eligible bar.

## HYP-0015 — Volume-Confirmed Directional Continuation

Mechanism: a positive completed 4-hour move accompanied by an unusually high current-volume participation and a strong current close may contain continuation information.

At signal t:
- `close[t-4] < close[t-1]`;
- `close[t] > open[t]`;
- `volume[t] >= V * median(volume[t-N] ... volume[t-1])`;
- current close-location >= L;
- no future information.

Grid: N = 24, 48 × V = 1.5, 2.5, 4 × L = 0.75, 0.90 = **12 cells**.
Baseline: N=24, V=2.5, L=0.90.

Entry: next eligible open; exit: close of that same eligible bar.

## HYP-0016 — Weekend Directional Persistence

Mechanism: a fixed UTC weekend day combined with a positive completed 4-hour move and strong current close may exhibit a repeatable short-horizon conditional return.

At signal t:
- UTC weekday equals the registered weekend day;
- `close[t-4]/close[t-8] - 1 >= T`;
- `close[t] > open[t]`;
- current close-location >= L;
- no future information.

Grid: weekend day = Saturday/Sunday × T = 0.5%, 1% × L = 0.75, 0.90 = **8 cells**.
Baseline: Saturday, T=0.5%, L=0.90.

Entry: next eligible open; exit: close of that same eligible bar.

## Costs and timing

Every registered parameter cell is evaluated at baseline cost and across the frozen fee/slippage stress cases. Baseline and 2-bar-delay timing are evaluated. Signal-to-entry timing is causal; zero-delay is prohibited.

## Robustness

For any candidate that satisfies mandatory Development economics, the fixed battery is required: parameter neighborhood, fee/slippage stress, 1/2-bar timing, fixed bull/neutral/bear regime segmentation, BTC/ETH transferability, leave-one-segment-out, concentration, drawdown/recovery, and cash/buy-and-hold benchmarks.

No robustness dimension may be added or removed after seeing results. A candidate cannot enter Validation unless every frozen Gate 2 Development promotion criterion passes.

## Logical-integrity rule

All signal predicates must be jointly satisfiable. A zero-event result caused by contradictory predicates is implementation/registration invalidity, not economic evidence.

## Closure

Any material change to a hypothesis requires a new hypothesis ID/version and a new prospective registration. Validation and locked OOS remain inaccessible during Cycle 4 Development research.