# Hypothesis Registration Template

## Hypothesis

**ID:** `HYP-XXXX`

**Statement:**

State one falsifiable claim about market behavior or a potential source of edge.

**Why it might exist:**

Document the economic/market rationale without presenting it as established fact.

## Classification

- Evidence status: HYPOTHESIS
- Research stage: DEVELOPMENT
- Asset(s): BTCUSDT / ETHUSDT / other pre-approved assets
- Timeframe: 1h
- Market: Spot

## Pre-registered model

**Entry:**

**Exit:**

**Stop:**

**Target:**

**Position sizing:**

**Regime conditions:**

**Required lookback:**

## Parameters

List every parameter, fixed value, and permitted search range. Do not add a parameter after seeing results without recording the change as a new experiment/version.

## Costs and execution

- Commission assumption:
- Slippage assumption:
- Fill timing:
- Liquidity assumptions:

## Research plan

- Development window: 2017-08-17 to 2022-01-01
- Validation window: 2022-01-01 to 2024-01-01
- OOS: LOCKED; do not access for development or selection

**Primary metrics:**

**Benchmarks:**

**Robustness tests:**

### Prospective validation eligibility rule

The following thresholds must be defined and frozen **before any Validation data is accessed**. They must not be backfilled from Development results and must not be changed after viewing Validation results without registering a new strategy/hypothesis version.

A candidate is eligible to enter Validation only if all applicable conditions below are satisfied:

1. **Development reproducibility:** exact registered code, dataset identity, parameters, costs, slippage, and execution model reproduce the recorded Development result; no leakage or continuity violation is present.
2. **Cash hurdle:** net compound return is strictly greater than the cash/no-position baseline on the same eligible segments.
3. **Economic significance:** net compound return is at least **+10%** over the Development window and the strategy has positive mean eligible-segment return.
4. **Sample support:** at least **20 eligible strategy segments** and at least **300 completed trades** across the BTCUSDT/ETHUSDT Development universe, unless a new preregistered rationale explicitly justifies a different threshold.
5. **Cross-asset support:** the strategy must be net profitable after costs on **both BTCUSDT and ETHUSDT**, or the preregistration must explicitly designate a single-asset hypothesis before Development evidence is reviewed.
6. **Drawdown constraint:** maximum drawdown must be **< 70%** on every evaluated asset and the combined Development result must not exhibit a single-segment loss worse than **-50%**.
7. **Benchmark context:** buy-and-hold and cash results must be reported on the same eligible segments. A candidate is not eligible solely because it has lower drawdown; it must satisfy the cash/economic-support criteria above.
8. **Robustness gate:** before Validation, parameter-neighborhood, fee/slippage, execution-timing, regime, concentration, and sample-size checks must show no material collapse under the preregistered stress tests. Exact robustness pass/fail thresholds must be recorded in the strategy-specific registration before those tests are run.

**Promotion decision:**

- `PROMOTE_TO_VALIDATION` only if every mandatory criterion passes.
- Otherwise `REJECT` or `ITERATE_WITH_NEW_VERSION`; no Validation data may be used to rescue a failed candidate.

## Invalidation criteria

Define conditions that would cause the hypothesis to be rejected before reviewing results.

## Experiment log

Record experiment IDs, commits, parameters, results, and decisions. Do not overwrite failed experiments.

## Decision

- [ ] Reject
- [ ] Iterate with a new registered hypothesis/model version
- [ ] Promote to validation

**Conclusion:**

Separate observations and backtest results from interpretation. Never state that an unvalidated result is a proven edge.
