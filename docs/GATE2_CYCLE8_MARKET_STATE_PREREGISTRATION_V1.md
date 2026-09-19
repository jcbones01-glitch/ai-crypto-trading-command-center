# Gate 2 Cycle 8 — Causal Market-State Layer Preregistration V1

## Status

**FROZEN PROSPECTIVE REGISTRATION — BEFORE CYCLE 8 STATE EVIDENCE GENERATION**

Cycle 8 does not test a trading strategy. It creates a causal, versioned market-state vocabulary that later hypotheses may reference prospectively.

This cycle follows the Adaptive Markets research framework. It is specifically designed to prevent future strategies from inventing favorable "regimes" after observing performance.

HYP-0001 through HYP-0025 remain closed according to their recorded outcomes. Cycle 8 does not rescue, retune, relabel, or re-evaluate any rejected strategy.

## Purpose

The project currently has repeated Development failures across price-only, volume-conditioned, cross-asset, candlestick, and multi-hour hypotheses. Rather than continue adding trading rules to the same OHLCV data without a stable environmental vocabulary, Cycle 8 first defines market state causally.

The state layer will answer descriptive questions only:

- How often does each state occur?
- How persistent are the states?
- How frequently do states transition?
- How often do BTC and ETH occupy the same state?
- How much data is unavailable because causal warm-up is incomplete?

Cycle 8 will **not** calculate strategy P&L, Sharpe ratio, buy/sell signals, strategy promotion scores, or Validation/OOS performance.

## Research firewall

- Market: Binance Spot
- Assets: BTCUSDT and ETHUSDT
- Timeframe: 1 hour
- Development: `[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`
- Validation: `[2022-01-01T00:00:00Z, 2024-01-01T00:00:00Z)` — inaccessible
- Locked OOS: `[2024-01-01T00:00:00Z, 2026-01-01T00:00:00Z)` — inaccessible
- Data: Gate 1A-certified observations only
- Continuity breaks: never bridged
- State-definition version: `AMS-V1`

The existing Gate 2 research protocol and `docs/ADAPTIVE_MARKETS_FRAMEWORK.md` remain controlling.

## Causality rule

For state assigned at close of bar `t`, every input and every reference observation must be available no later than the close of `t`.

No future bar, Validation observation, OOS observation, centered window, forward-filled observation, interpolated value, or future-derived threshold may contribute to a state assignment.

## State Axis 1 — Volatility

### Current volatility statistic

At close `t`, compute the trailing 24-hour realized-volatility statistic using the previous 24 hourly close-to-close log returns ending at `t`:

`RV24[t] = sqrt(sum(r_i^2))`

where `r_i = ln(close[i] / close[i-1])`.

### Causal reference distribution

Compare `RV24[t]` with the **720 immediately preceding completed RV24 observations**, ending at `t-1`.

The current observation is excluded from its own reference distribution.

### Labels

- `VOL_LOW`: percentile rank <= 20%
- `VOL_NORMAL`: percentile rank >20% and <80%
- `VOL_HIGH`: percentile rank >=80%

If the full 720-observation reference history is not available within the same certified continuous segment, volatility state is unavailable.

## State Axis 2 — Trading Activity

### Current activity statistic

At close `t`, compute trailing 24-hour aggregate base-asset volume:

`VOLUME24[t] = sum(volume[t-23:t])`

### Causal reference distribution

Compare `VOLUME24[t]` with the **720 immediately preceding completed VOLUME24 observations**, ending at `t-1`.

The current observation is excluded from its own reference distribution.

### Labels

- `ACTIVITY_LOW`: percentile rank <= 20%
- `ACTIVITY_NORMAL`: percentile rank >20% and <80%
- `ACTIVITY_HIGH`: percentile rank >=80%

If the full 720-observation reference history is not available within the same certified continuous segment, activity state is unavailable.

## State Axis 3 — Trend

At close `t`, compute the trailing 168-hour close-to-close return:

`TREND168[t] = close[t] / close[t-168] - 1`

Labels are frozen as:

- `TREND_BULL`: return > +10%
- `TREND_BEAR`: return < -10%
- `TREND_NEUTRAL`: otherwise

This threshold definition is inherited from the already preregistered Gate 2 regime robustness convention and is not selected from Cycle 8 results.

If 168 continuous hours are unavailable within the same certified segment, trend state is unavailable.

## Complete market-state vector

A bar receives a complete `AMS-V1` state only when all three axes are available:

`(volatility_state, activity_state, trend_state)`

There are at most 27 possible composite states.

Cycle 8 does not require every composite state to occur.

## Registered descriptive outputs

For each asset separately, the artifact must report:

1. count of total certified bars
2. count and fraction of bars with complete AMS-V1 state
3. occupancy count/fraction for every volatility label
4. occupancy count/fraction for every activity label
5. occupancy count/fraction for every trend label
6. occupancy count/fraction for every observed composite state
7. one-hour transition counts/probabilities for each axis
8. one-hour transition counts/probabilities for composite states
9. dwell-length distribution summary for each axis label:
   - number of runs
   - median run length
   - 90th-percentile run length
   - maximum run length
10. first and last timestamp with complete state
11. unavailable-state counts caused by warm-up / continuity boundaries

For synchronized BTC/ETH timestamps where both have complete states, report:

12. volatility-state agreement fraction
13. activity-state agreement fraction
14. trend-state agreement fraction
15. full composite-state agreement fraction
16. synchronized complete-state observation count

## Integrity tests

Cycle 8 implementation must prove:

1. changing any future bar after signal time does not change a previously assigned state
2. the current observation is excluded from its percentile reference sample
3. exactly 720 prior completed observations are required for percentile axes
4. state computation never crosses a continuity break
5. percentile boundaries implement the registered <=20% / >=80% rules exactly
6. trend thresholds implement strict >+10% and <-10% boundaries exactly
7. composite state is unavailable if any axis is unavailable
8. BTC/ETH agreement is calculated only on exact synchronized timestamps where both states are complete
9. Validation and OOS are not accessed

## Multiple-testing boundary

Cycle 8 performs **no parameter search**.

The following are fixed and may not be changed after state evidence is generated:

- RV window = 24 hours
- activity window = 24 hours
- percentile reference count = 720 completed observations
- low/high percentile boundaries = 20% / 80%
- trend window = 168 hours
- bull/bear thresholds = +10% / -10%
- composite axes = volatility, activity, trend

Alternative state definitions require a new version and new preregistration.

## Interpretation boundary

Cycle 8 state occupancy, persistence, or transitions are **OBSERVATIONS**, not evidence of a tradable edge.

The project must not:

- call a state profitable
- select a state because a prior strategy performed well there
- attach a trading rule after seeing Cycle 8 state frequencies and then claim the combined rule was preregistered
- use Validation or OOS to refine AMS-V1
- modify HYP-0001 through HYP-0025
- begin paper or live trading

A later trading hypothesis may reference AMS-V1 only through a new prospective preregistration that defines the state condition before that hypothesis is evaluated.

## Cycle 8 completion rule

Cycle 8 passes as infrastructure only if:

- all integrity tests pass
- both assets produce nonzero complete-state observations
- exact state-definition version and preregistration hash are recorded
- no Validation/OOS data is accessed
- the output artifact contains every registered descriptive field

The only allowed cycle-level statuses are:

- `STATE_LAYER_READY`
- `STATE_LAYER_INVALID`

Neither status is a strategy-promotion decision.

## Primary research rationale

This design is motivated by Andrew W. Lo's Adaptive Markets Hypothesis, which treats market efficiency as dependent on changing market ecology and adaptation rather than as a fixed property. The state layer is an engineering mechanism for describing changing environments without granting the model permission to invent regimes after observing strategy performance.

Primary references are already recorded in `docs/ADAPTIVE_MARKETS_FRAMEWORK.md`.

## Final status

**FROZEN REGISTRATION. IMPLEMENTATION MAY NOW PROCEED, BUT STATE EVIDENCE MUST CONFORM TO THIS EXACT COMMITTED SPECIFICATION.**
