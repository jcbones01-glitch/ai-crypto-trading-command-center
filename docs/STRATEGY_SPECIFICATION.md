# Strategy Specification

Every strategy must be specified before it is evaluated.

## Required fields

- strategy_id
- version
- hypothesis_id
- hypothesis_mechanism
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
- market_state_variables
- state_definition_version
- state_assignment_timing
- assumptions
- invalidation_criteria
- research_status

## Regime-aware strategies

If a strategy claims different behavior across market regimes, the specification must also define the regime construction before protected evaluation, including:

- regime_hypothesis
- state lookback windows
- thresholds or classification rules
- data sources
- timestamp/availability rules
- minimum sample requirements
- regime-specific invalidation criteria

State assignment must be causal: no variable may use information that was unavailable at the strategy decision timestamp.

A regime definition may not be retrofitted after protected validation or OOS results are observed in order to rescue a failed strategy. A materially changed regime definition creates a new strategy/hypothesis version.

## Degradation contract

Before paper trading, the strategy specification must be extended with:

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
