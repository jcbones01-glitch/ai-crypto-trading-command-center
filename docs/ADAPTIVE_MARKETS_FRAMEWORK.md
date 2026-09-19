# Adaptive Markets Research Framework

## Purpose

This document translates Andrew W. Lo's Adaptive Markets Hypothesis (AMH) into research controls for this project.

It is a research-governance layer, not a trading strategy and not evidence that any crypto strategy is profitable.

## Core premise

Market efficiency is treated as conditional and time-varying rather than fixed. Strategy performance may depend on competition, participant behavior, liquidity, volatility, technology, regulation, and other features of the market environment.

The project therefore must not assume that a historically profitable rule represents a permanent edge.

## Research implications

### 1. Hypotheses must include an economic or behavioral mechanism

A candidate hypothesis should state why the proposed effect could exist, who or what may create it, and why it might persist long enough to test.

Purely data-mined patterns without a plausible mechanism may be explored, but they must be labeled exploratory and receive stronger multiple-testing controls.

### 2. Market-state variables must be predeclared

Before protected validation or OOS evaluation, any market-state variables used to condition a strategy must be defined in advance.

Examples may include:
- realized volatility
- trend strength
- liquidity proxies
- volume/activity
- cross-asset dispersion
- funding or derivatives variables when a validated dataset exists
- market breadth when a validated universe exists

Regime labels must not be invented after viewing protected results in order to rescue a failed strategy.

### 3. Conditional performance is descriptive until validated

A strategy may appear stronger in some environments than others. Such observations are not automatically evidence of a regime-dependent edge.

Any regime-dependent claim requires:
- a predeclared state definition
- sufficient observations in each state
- transaction costs and slippage
- validation outside the data used to formulate the claim
- controls for repeated testing

### 4. Strategy decay must be expected and monitored

Every strategy promoted beyond research must have predefined degradation criteria.

Monitoring may include:
- realized return versus expected distribution
- hit rate
- drawdown
- turnover and trading costs
- signal frequency
- exposure
- volatility of returns
- parameter sensitivity
- market-state mix
- divergence between paper/live behavior and research assumptions

A degradation alert triggers review. It does not authorize automatic retuning.

### 5. Failed strategies are not automatically repaired

When a strategy fails validation, OOS, paper trading, or live monitoring, the default action is to preserve the failure as evidence.

The system must not:
- tune parameters on protected data
- redefine regimes after seeing failure
- remove inconvenient periods without objective data-quality reasons
- add filters solely because they improve the failed result
- repeatedly search variations without accounting for multiple testing

A materially changed strategy is a new hypothesis/version and must re-enter the research process.

### 6. Competition and crowding are part of the hypothesis

Where measurable, research should consider whether an edge could weaken because participants adapt, capital enters the trade, execution costs increase, or market structure changes.

This project does not assume such effects can always be observed directly. Claims about crowding must be supported by defined proxies or external evidence.

### 7. Adaptation happens through governance, not unrestricted self-modification

Future AI agents may propose:
- new hypotheses
- new market-state definitions
- retirement reviews
- robustness tests
- alternative economic explanations

They may not silently alter a promoted strategy, validation protocol, OOS boundary, or execution rule.

Any proposed change must be versioned, logged, reviewed, and tested as a new research object.

## Adaptive research loop

`Market theory -> Observation -> Falsifiable hypothesis -> Pre-registration -> Data -> Model/strategy specification -> Development test -> Validation -> Locked OOS -> Paper trading -> Controlled deployment -> Edge monitoring -> Continue / quarantine / retire -> New hypothesis`

The loop does not imply that every hypothesis progresses to deployment.

## Strategy-state contract

Any future regime-aware strategy specification should identify:

- `market_state_variables`
- `state_definition_version`
- `state_definition_source`
- `state_lookback`
- `state_thresholds`
- `state_assignment_timing`
- `applicable_market_regimes`
- `regime_hypothesis`
- `regime_invalidation_criteria`

State assignment must use only information available at the decision timestamp.

## Edge-monitoring contract

Before paper trading, a strategy should define:

- expected behavior from validated research
- monitoring horizon
- minimum sample before degradation inference
- degradation metrics
- warning threshold
- quarantine threshold
- retirement criteria
- permitted responses

Permitted responses should default to:
1. continue unchanged,
2. quarantine from new exposure,
3. retire,
4. open a new research hypothesis.

Automatic parameter repair is not a permitted default response.

## Multiple-testing discipline

Adaptive research can easily become data snooping because many environments, thresholds, and strategy variants can be tested.

The project should therefore track:
- total hypotheses attempted
- total parameter variants
- total regime definitions tried
- reused datasets
- researcher/agent decision history
- protected-sample exposures

Where appropriate, later gates should add formal controls such as family-wise error, false-discovery-rate methods, deflated performance statistics, or other methods suited to the experiment design.

## What AMH does not justify

The Adaptive Markets Hypothesis does not justify:
- assuming regime detection is easy
- switching strategies based on hindsight
- using AI as an oracle
- weakening OOS controls
- unlimited parameter search
- assuming every market inefficiency is exploitable after costs
- assuming past regime behavior will repeat

## Project design consequence

The long-term system should optimize the research process, not merely optimize trading parameters.

The AI layer should become better at proposing, testing, rejecting, monitoring, and retiring hypotheses while preserving research integrity.

## Primary source basis

This framework is inspired by Andrew W. Lo's Adaptive Markets Hypothesis and MIT course material on adaptive markets. It is an engineering interpretation for this repository, not a claim that Professor Lo endorses this project or these exact controls.
