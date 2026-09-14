# Gate 2 — Strategy Research Protocol

## Purpose

Gate 2 determines whether formally specified strategy hypotheses show credible, reproducible, and robust evidence of an edge. Gate 2 does **not** authorize paper or live trading.

The governing research loop is:

`OBSERVATION → HYPOTHESIS → MODEL → DEVELOPMENT → VALIDATION → ROBUSTNESS → DECISION`

A profitable backtest is evidence, not proof of future profitability.

## Immutable data partitions

The V1 research window and boundaries are fixed:

- Development: `[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`
- Validation: `[2022-01-01T00:00:00Z, 2024-01-01T00:00:00Z)`
- Locked OOS: `[2024-01-01T00:00:00Z, 2026-01-01T00:00:00Z)`

Gate 2 development and model selection may consume Development only. Validation may be used only for pre-registered validation of candidates that have completed development. OOS results are embargoed from all strategy development, parameter selection, hypothesis selection, ranking, tuning, and decision-making.

No later partition may initialize an earlier partition. No partition boundary may move without a new research-data protocol and new dataset identity.

## Strategy specification requirements

Every candidate must have a versioned `StrategySpecification` containing, at minimum:

- unique strategy ID and version
- falsifiable hypothesis ID
- market and asset universe
- timeframe
- unambiguous entry rules
- unambiguous exit rules
- stop/target rules where applicable
- deterministic position sizing
- transaction-cost assumptions
- slippage assumptions
- applicable regimes
- assumptions
- invalidation criteria

A strategy may not be evaluated if its rules require discretionary interpretation that cannot be reproduced from the recorded inputs.

## Experiment registration

Before a backtest is treated as evidence, record:

1. hypothesis ID and exact statement
2. strategy ID/version
3. dataset ID and partition
4. date range
5. timeframe
6. all parameters
7. parameter search space, if any
8. transaction costs and slippage
9. code/commit identifier
10. benchmark definition
11. metrics to be evaluated
12. planned robustness tests
13. decision rule

Exploratory experiments may discover observations, but they must not be relabeled as pre-registered evidence after seeing the result.

## Anti-leakage controls

The research engine must explicitly guard against:

- look-ahead bias
- future-data leakage
- use of OOS data
- survivor-selection bias
- overlapping-window leakage where applicable
- indicator warm-up crossing research-continuity breaks
- execution at prices unavailable at decision time
- impossible fills
- hidden zero-cost assumptions

Signals may only use information available at the signal timestamp and only certified continuous history. A continuity break invalidates any lookback-dependent observation crossing the break.

## Execution model

Backtests must use the deterministic execution model already established in V0. Costs and slippage are explicit inputs. No result may silently assume zero costs, zero slippage, perfect fills, or unlimited liquidity.

Initial Gate 2 research remains spot-only.

## Baselines

Every strategy family should be evaluated against appropriate simple baselines before claiming an edge. At minimum, the research record should distinguish strategy performance from:

- buy-and-hold for the same asset and eligible period
- cash/no-position baseline
- simple rule-based benchmark where appropriate

Benchmark definitions must obey the same research-continuity boundaries and must not bridge excluded regions.

## Multiple testing and overfitting

The research record must track the number and nature of hypotheses, parameter searches, and candidate variants explored. Repeated experimentation is itself research information and must not be hidden.

Selection must not be based solely on the best observed metric. Robustness should favor stable performance across reasonable parameter perturbations and materially different market conditions.

## Robustness battery

A serious candidate should be subjected to, as applicable:

- parameter perturbation / neighborhood stability
- fee sensitivity
- slippage sensitivity
- execution-timing sensitivity
- regime segmentation
- asset transferability between BTC and ETH
- trade-count and sample-size review
- drawdown and recovery analysis
- concentration analysis
- walk-forward or rolling validation where appropriate
- benchmark comparison

A strategy that fails a material robustness test is not promoted merely because its headline backtest is profitable.

## Evidence classification

All research outputs must preserve the distinction:

- FACT
- OBSERVATION
- HYPOTHESIS
- MODEL
- BACKTEST RESULT
- LIVE RESULT
- OPINION

No hypothesis, backtest result, or model output may be presented as a proven edge.

## Gate 2 promotion rule

A candidate can be promoted from development to validation only when:

- the hypothesis and rules are recorded
- the implementation is deterministic
- the development result is reproducible
- leakage controls pass
- costs/slippage are explicit
- the candidate meets the pre-registered development decision rule

A candidate can be promoted beyond validation only when validation evidence and robustness evidence satisfy the pre-registered decision rule without using locked OOS results.

Gate 2 may legitimately conclude **NO QUALIFIED EDGE FOUND**. This is preferable to selecting a fragile or overfit strategy.

## OOS embargo

The OOS partition is a final evidence set, not a tuning set. Until a strategy has passed all earlier gates, no OOS performance, ranking, chart, metric, or observation may be used to alter its rules, parameters, or selection.

If OOS data is accessed accidentally, the event must be recorded and the affected experiment treated as contaminated rather than silently continuing.

## Autonomy boundary

Gate 2 authorizes historical research only. It does not authorize exchange credentials, order placement, paper execution, live execution, leverage, or autonomous capital deployment.
