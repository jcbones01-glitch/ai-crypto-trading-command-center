# Gate 2 FOMC Descriptive Event Study — Preregistration V1

## Status

**PREREGISTERED BEFORE MARKET-RETURN ANALYSIS**

This document freezes the first descriptive use of the certified FOMC event dataset. It is not a strategy specification and has no promotion rule.

## Purpose

Describe how BTCUSDT and ETHUSDT behaved immediately after official Federal Reserve FOMC statement releases during the already-defined Development period.

The study answers only:

> Are the signed and absolute forward returns around certified FOMC statement release times visibly different from deterministic prior same-time controls in Development data?

Any trading hypothesis inspired by the result must be written as a new hypothesis and preregistered before strategy backtesting.

## Frozen inputs

### FOMC event dataset

- Manifest path: `research/experiments/fomc_development_manifest_v1.json`
- Protocol: `event-dataset-v1`
- Dataset ID: `fd5021aa2ff2f01ceaa2f5e060d08db8e0825cc27e1bde147e8eb5948ee14e11`
- Event count: `37`
- Event window: `2017-09-20T18:00:00Z` through `2021-12-15T19:00:00Z`
- Source class: Federal Reserve Board FOMC statements
- Validation/OOS access: prohibited

### Market datasets

Use the already certified Binance Spot 1-hour Development datasets only.

- BTCUSDT dataset identity: `1590cf8e69ed757eeb6701a218d561448beb2eb6ea09dcd0ae31d15a8f5197cf`
- ETHUSDT dataset identity: `d35bf21e309820abc88090bad29601adc1d1ea6b31dcddf0b80d510af4cf542f`
- Development boundary: `[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`

No Validation or locked OOS market bars may be fetched or inspected.

## Event alignment

Every certified FOMC event currently falls on an exact UTC hourly boundary. The event timestamp is its certified `first_market_available_at`.

For an event at hour-open timestamp `t`:

- `P0` is the market-bar **open** at timestamp `t`.
- The h-hour forward price is the market-bar **open** at timestamp `t + h hours`.
- The h-hour forward return is:

`R_h = open(t + h) / open(t) - 1`

This is a descriptive market response, not an executable trade simulation.

The frozen horizons are:

- `1h`
- `6h`
- `24h`

No other horizon may be introduced into V1 after results are observed.

## Continuity and eligibility

For a specific asset, event, and horizon:

1. `t` must exist as an exact certified hourly bar-open timestamp.
2. `t + h` must exist.
3. Both endpoints and every intervening hour must belong to the same certified continuous segment.
4. The full interval must remain inside Development.
5. No missing interval may be filled or inferred.

An ineligible observation is reported with its reason and is not replaced.

## Deterministic control observations

Each FOMC event receives up to four **prior** same-weekday/same-UTC-hour controls at:

- `t - 7 days`
- `t - 14 days`
- `t - 21 days`
- `t - 28 days`

A control is eligible only when:

1. its timestamp is inside Development;
2. it is more than 24 hours away from every certified FOMC event timestamp;
3. it and its h-hour endpoint are in the same certified continuous segment;
4. no missing interval is crossed.

Controls are never selected based on their returns.

No future control timestamp relative to its associated event is used.

## Frozen summary metrics

For each asset and each of the three horizons, separately for event observations and control observations, report:

- eligible observation count;
- mean signed return;
- median signed return;
- positive-return fraction;
- mean absolute return;
- median absolute return.

Also report:

- event mean signed return minus control mean signed return;
- event mean absolute return minus control mean absolute return;
- event mean absolute return divided by control mean absolute return when the control mean is nonzero.

The report must also include every event-level and control-level return with timestamps and eligibility status.

## No inferential significance claim

V1 will not calculate or select among:
- p-values;
- significance thresholds;
- optimized confidence intervals;
- best-performing horizons;
- best-performing event subgroups;
- best-performing years;
- best-performing assets.

The study is deliberately descriptive.

## No subgroup selection

Scheduled and emergency statements remain in the single frozen event set. V1 will not split, rank, remove, or reclassify events after seeing returns.

No policy-stance, hawkish/dovish, sentiment, surprise, or LLM-derived classification is permitted in this study.

## No transaction-cost model

Because V1 measures raw market response rather than simulating a strategy, commissions, slippage, position sizing, and P&L are not applied.

A later trading hypothesis must specify those items independently before testing.

## Evidence and reproducibility requirements

The output must record:

- this preregistration path and SHA-256;
- code commit SHA;
- frozen FOMC dataset ID;
- certified BTCUSDT and ETHUSDT dataset identities;
- Development boundaries;
- `validation_or_oos_accessed: false`;
- the frozen horizons;
- the frozen control lags;
- all exclusions and reasons;
- all event/control returns used in summaries.

Expected output path:

`event_intelligence_results/fomc_event_study_v1.json`

## Interpretation boundary

The output may support statements such as:

- `OBSERVATION: FOMC-event 24h absolute returns were larger/smaller than the frozen controls in Development.`

It may not support:

- `EDGE PROVEN`;
- `BUY after FOMC`;
- `SELL after FOMC`;
- promotion to Validation;
- paper trading;
- live trading.

## Next decision

After the descriptive evidence is generated and audited, one of two things happens:

1. no sufficiently interesting structured observation is found, so this source remains contextual/risk intelligence; or
2. an observation motivates one or more **new falsifiable Development hypotheses**, each of which must be preregistered before any strategy backtest.

Validation and locked OOS remain inaccessible either way.
