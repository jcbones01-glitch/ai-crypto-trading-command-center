# Strategy Specification

Every strategy must be specified before it is evaluated.

## Current required fields

The current Python `StrategySpecification` contract requires:

- strategy_id
- version
- hypothesis_id
- market
- asset_universe
- timeframe
- entry_rules
- exit_rules
- stop_rules
- target_rules
- position_sizing
- transaction_cost_assumptions
- slippage_assumptions
- applicable_market_regimes
- assumptions
- invalidation_criteria
- research_status

These fields remain authoritative for the current Gate 2 implementation.

## Adaptive research extensions

Adaptive-market fields are additional research requirements when a candidate makes a regime-dependent claim or advances toward later paper/live gates. They are not silently added to the current Python dataclass.

For a regime-dependent candidate, the research record must define before protected evaluation:

- hypothesis_mechanism
- market_state_variables
- state_definition_version
- state_definition_source
- state_lookback
- state_thresholds or classification rules
- state_assignment_timing
- regime_hypothesis
- regime_invalidation_criteria

State assignment must be causal: no variable may use information that was unavailable at the strategy decision timestamp.

A regime definition may not be retrofitted after protected validation or OOS results are observed in order to rescue a failed strategy. A materially changed regime definition creates a new strategy/hypothesis version.

## Degradation contract

Before paper trading, the strategy research record must be extended with:

- expected validated behavior
- monitoring horizon
- minimum monitoring sample
- degradation metrics
- warning threshold
- quarantine threshold
- retirement criteria
- permitted responses

Automatic parameter retuning is not a default permitted response to degradation.

A specification describes rules and assumptions. It does not imply profitability.

See `docs/ADAPTIVE_MARKETS_FRAMEWORK.md`.
