# Gate 2 — Robustness Preregistration v1

## Status and scope

This document is a prospective registration for the Gate 2 Development robustness battery. It is created **after completion of the initial Development experiment but before any robustness result is generated**. It does not modify, relabel, or optimize the completed `gate2-dev-v2` experiment.

Scope is Development only:

- BTCUSDT and ETHUSDT
- 1-hour bars
- `[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`
- Gate 1A-certified data with explicit continuity exclusions
- Locked Validation and OOS remain inaccessible

The four already-registered hypotheses are evaluated as fixed strategy versions. No new parameter search is permitted inside this battery.

## Registered candidates

- HYP-0001-v1 — time-series momentum
- HYP-0002-v1 — short-horizon mean reversion
- HYP-0003-v1 — volatility/range breakout
- HYP-0004-v1 — trend pullback

The initial experiment's registered rules remain unchanged. A robustness perturbation is a diagnostic of the registered rule, not permission to select a new rule.

## Common baseline

- Commission: 10 bps per side
- Slippage: 5 bps per side
- Execution: signal at close `t`, fill at open `t+1`
- Spot only, 0–100% target exposure, no leverage
- No intrabar assumptions
- No gap bridging
- Independent continuous-segment accounting
- Benchmarks use the exact same eligible segment universe

## Multiple-testing accounting

The battery is fixed before execution and every attempted cell must be recorded, including failed/error cells. No cell may be added, removed, or redefined after results are observed.

Registered robustness dimensions:

1. parameter neighborhood
2. fee sensitivity
3. slippage sensitivity
4. execution timing
5. regime segmentation
6. asset transferability
7. sample-size stability
8. concentration
9. drawdown/recovery

The number of registered cells and their outcomes must be included in the final evidence artifact. Robustness results are not ranked to choose a winner.

## 1. Parameter-neighborhood stability

For each strategy parameter explicitly named below, evaluate the fixed neighborhood listed. Do not search beyond it.

### HYP-0001
- momentum lookback: 120, 168, 216 hours
- confirmation lookback: 12, 24, 36 hours

### HYP-0002
- mean lookback: 36, 48, 60 hours
- entry deviation: -1.5%, -2.0%, -2.5%
- exit deviation: -0.25%, -0.5%, -0.75%

### HYP-0003
- breakout lookback: 18, 24, 30 hours
- range lookback: 18, 24, 30 hours
- minimum normalized range: 0.75%, 1.00%, 1.25%

### HYP-0004
- trend EMA: 160, 200, 240 hours
- trend slope comparison: 12, 24, 36 hours
- trigger SMA: 18, 24, 30 hours

Parameter cells are Cartesian combinations only within each hypothesis's listed dimensions. No adaptive or metric-driven selection is allowed.

**Parameter pass threshold:** for each asset, at least 60% of valid perturbation cells must have positive mean eligible-segment return, and the median perturbation compound return must be above cash. The registered baseline is reported separately and is not counted as a perturbation cell.

A hypothesis fails this dimension if either asset fails the threshold.

## 2. Fee/slippage sensitivity

Evaluate the fixed execution-cost cells:

| Cell | Commission/side | Slippage/side |
|---|---:|---:|
| Baseline | 10 bps | 5 bps |
| Stress-1 | 15 bps | 10 bps |
| Stress-2 | 25 bps | 15 bps |

**Pass threshold:** at the highest-cost cell, each asset must remain above cash and have positive mean eligible-segment return.

## 3. Execution-timing sensitivity

Evaluate exactly:

- 1-bar delay (registered baseline)
- 2-bar delay

The causal execution contract remains mandatory. Same-bar/zero-delay execution is not a robustness cell and must remain rejected.

**Pass threshold:** each asset at 2 bars must have positive mean eligible-segment return and remain above cash.

## 4. Regime segmentation

Regimes are defined without future information using the 168-hour close-to-close return at each bar:

- Bull: return `> +10%`
- Bear: return `< -10%`
- Neutral: otherwise

Signals and regime labels are calculated only from information available at the signal close. A regime-specific segment is eligible only where the strategy observation itself is valid and continuous.

**Pass threshold:** no hypothesis may have its entire positive Development result attributable to a single regime. Specifically, at least two of the three regimes must contain positive aggregate strategy return on each asset where that regime has at least 100 eligible strategy bars.

## 5. Asset transferability

BTCUSDT and ETHUSDT are evaluated independently; no parameter is selected from one asset and then applied to the other.

**Pass threshold:** positive mean eligible-segment return on both assets and positive compound return on both assets under the baseline cost/execution model.

This is a robustness criterion and does not replace the separate Development promotion criteria.

## 6. Sample-size stability

Two deterministic checks are required:

1. **Leave-one-segment-out:** recompute aggregate compound return after removing each eligible segment in turn.
2. **Trade support:** report completed trades and positive-trade fraction from the unchanged baseline strategy.

**Pass threshold:** at least 75% of leave-one-segment-out variants remain above cash on each asset, and no single omitted segment changes the aggregate classification from positive to negative by itself when the full baseline compound return is positive.

If the full baseline compound return is non-positive, this dimension is automatically failed for promotion purposes; no leave-one-out analysis can rescue the failed baseline.

## 7. Concentration

Measure each eligible segment's contribution using its segment log-return contribution to the total strategy log-return. Also report trade-level P&L concentration.

**Pass threshold:** no single eligible segment may account for more than 50% of total positive log-return contribution, and the top 10% of completed trades may not account for more than 50% of total positive trade P&L. If the denominator is non-positive, the concentration test fails rather than being declared inapplicable.

## 8. Drawdown/recovery

Report maximum drawdown, maximum segment drawdown, longest recovery duration, and the number of segments with loss worse than -50%.

**Pass threshold:** max drawdown <70% on every asset, zero segment losses worse than -50%, and no recovery period may exceed 50% of the eligible historical duration of that asset's evaluated strategy universe.

## 9. Overall robustness decision

For a hypothesis to satisfy the robustness gate, **all nine dimensions must pass on their registered thresholds**. No weighted score, discretionary override, or best-case selection is permitted.

The final classification is one of:

- `ROBUSTNESS_PASS`
- `ROBUSTNESS_FAIL`
- `ROBUSTNESS_INCONCLUSIVE` (only when a registered test cannot be completed because of an implementation/data error; this is not a promotion)

A `ROBUSTNESS_FAIL` result cannot be repaired by changing the thresholds or perturbation grid after observation. Any materially changed strategy requires a new strategy version and a new preregistration.

## Validation/OOS firewall

This registration explicitly forbids access to:

- Validation `[2022-01-01, 2024-01-01)`
- Locked OOS `[2024-01-01, 2026-01-01)`

No result, chart, metric, ranking, or observation from those partitions may be used during this battery.

## Evidence requirements

The eventual artifact must include:

- this registration's SHA-256
- executing code commit
- dataset identities for each asset
- exact cell definitions
- every attempted cell and outcome
- baseline results
- benchmark results on identical eligible segments
- failed/error cells
- multiple-testing counts
- final binary dimension decisions
- explicit `oos_accessed: false`

No robustness artifact may state or imply that a hypothesis is a proven edge.
