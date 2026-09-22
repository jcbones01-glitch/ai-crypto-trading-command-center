# Market-state dependence research protocol

Status: proposed additive governance; historical Gate 2 controls retain authority.

## Question and scope

Does the degree and type of measurable BTC/ETH return dependence and predictability change through time and across objectively defined market environments?

AMH motivates this question; it is not the null hypothesis, an established fact about these assets, or a trading rule. Distinguish linear signed-return dependence, nonlinear dependence, conditional mean predictability, and volatility predictability. Predictable squared returns do not by themselves predict return direction. Random-walk rejection is neither a general rejection of efficient markets nor proof of profitable execution.

The first experiment is a finite Development diagnostic using existing certified spot observations and unchanged AMS-V1. No new candle-pattern or strategy hypotheses are included. The exact analysis is in `MARKET_STATE_DEPENDENCE_PREREGISTRATION_V1.md`; a draft is not a frozen authorization.

## Inherited controls

All Development → Validation → locked OOS boundaries, Gate 1A certification, continuity rules, causal timing, provenance, explicit costs/slippage, hypothesis registry, multiple-testing accounting, and evidence classifications remain mandatory. Strategy promotion still requires the existing economic, sample-support, cross-asset, parameter-neighborhood, timing, fee/slippage, regime, concentration, drawdown and recovery checks. These do not become optional because a diagnostic has a small p-value.

Only Development `[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)` may eventually be read. Reject disallowed partitions before fetching/reading data, not after fitting a model. Reject any endpoint whose close availability reaches the protected boundary if that observation would require a protected bar. Preserve the existing convention that a last Development bar can close at the boundary without consuming a new protected bar.

All return endpoints and predictor histories must lie in one certified continuous segment. State at bar t is known only at that bar's close; repository bar timestamps are open times. Future return labels must begin after that close. Missing observations remain missing. Never compress a gap into an hourly lag.

## Evidence status and design discipline

The Development sample has already supported many hypotheses and published state occupancy summaries. A prospectively registered new computation on it does not make the sample untouched. Report results as **OBSERVATION — preregistered Development diagnostic on reused data**. Model definitions are MODEL; proposed mechanisms are HYPOTHESIS. No BACKTEST RESULT or LIVE RESULT is produced by this phase.

Freeze the estimand, horizons, states, window endpoints, sample-support rules, estimator, uncertainty calculation, multiplicity family, exclusions and interpretation rules before inspecting the new dependence outputs. Log all attempted designs and amendments, including null/invalid results. Freeze all regime definitions before Development outcomes, not merely before Validation.

Use direct coefficient/contrast tests to examine differences. One significant subgroup and one nonsignificant subgroup do not establish a difference. Overlapping rolling estimates are correlated; do not count consecutive significant windows as independent replications. A non-rejection does not establish equivalence or stable predictability. A stability claim requires a separately frozen equivalence margin and adequate power.

At minimum report effect sizes, uncertainty, sample counts, eligible calendar spans, continuity losses, complete-state coverage, state/year support, and segment concentration. Compare unconditional statistics on the same state-eligible observations before attributing differences to conditioning. Do not choose the most favorable state, lag, asset, bandwidth or window after seeing results.

## Confounding and interpretation

AMS-V1 describes volatility, trading activity and trend; it does not measure participant identity, crowding or liquidity directly. Volume is not a bid/ask spread. Changes could reflect volatility, sample composition, stale closes, bid/ask bounce, asynchronous trading, exchange changes, USDT effects or measurement errors. BTC and ETH share a venue and quote currency and are not independent replications.

Hourly closing trade prices cannot by themselves separate efficient-price dependence from microstructure effects. A microstructure explanation remains unresolved without certified quotes/trades or equivalent evidence. No deletion of unfavorable outliers, selected break dates, hindsight regime fitting, HMM state searches or change-point optimization is authorized.

## Release sequence

1. Design draft and source review, with remaining ambiguities explicit.
2. Independent statistical audit and preregistration freeze in Git.
3. Deterministic implementation and synthetic checks; no actual-return previews.
4. Independent implementation review, exact-code/data/hash verification and release record.
5. One Development diagnostic run, all registered outputs retained; audit and classify.
6. If justified, a separately registered mechanism/forecast experiment. No automatic Validation access.

Stage 5 may conclude detectable dependence, detectable heterogeneity, no detected effect, inadequate support, unresolved microstructure effects or invalid inference. Approximate stability requires the separate equivalence design. Economic tradability remains unassessed until an explicitly specified strategy passes all applicable gates.

See `EDGE_LIFECYCLE_PROTOCOL.md` for authority separation; this document creates no agent runtime or execution permission.
