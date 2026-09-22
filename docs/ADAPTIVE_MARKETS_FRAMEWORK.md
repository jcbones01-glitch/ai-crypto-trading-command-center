# Adaptive Markets Research Framework

## Purpose

This document translates Andrew W. Lo's Adaptive Markets Hypothesis (AMH) into research controls for this project.

It is a research-governance layer, not a trading strategy and not evidence that any crypto strategy is profitable.

## Core premise

Market efficiency may be conditional and time-varying; whether measurable dependence changes is an empirical question, not an assumption this project must confirm. Strategy performance may depend on competition, participant behavior, liquidity, volatility, technology, regulation, and other features of the market environment.

The project therefore must not assume that a historically profitable rule represents a permanent edge.

## Research implications

### 1. Hypotheses must include an economic or behavioral mechanism

A candidate hypothesis should state why the proposed effect could exist, who or what may create it, and why it might persist long enough to test.

Purely data-mined patterns without a plausible mechanism may be explored, but they must be labeled exploratory and receive stronger multiple-testing controls.

### 2. Market-state variables must be predeclared

Before Development evidence for a new experiment is generated, its market-state variables and statistical decision rules must be preregistered. Existing frozen definitions are not changed by this amendment.

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

Primary references:
- Andrew W. Lo (2004), "The Adaptive Markets Hypothesis: Market Efficiency from an Evolutionary Perspective," Journal of Portfolio Management. MIT-hosted copy: https://web.mit.edu/Alo/www/Papers/JPM2004_Pub.pdf
- Andrew W. Lo, "Reconciling Efficient Markets with Behavioral Finance: The Adaptive Markets Hypothesis." MIT-hosted copy: https://web.mit.edu/Alo/www/Papers/JIC2005_Final.pdf
- MIT OpenCourseWare, 15.481x Adaptive Markets: Financial Market Dynamics and Human Behavior: https://ocw.mit.edu/courses/15-481x-adaptive-markets-financial-market-dynamics-and-human-behavior-fall-2022/

## First dependence study and additive protocols

The certified AMS-V1 state vocabulary is retained unchanged. See:

- `MARKET_STATE_RESEARCH_PROTOCOL.md` for the diagnostic research boundary;
- `MARKET_STATE_DEPENDENCE_PREREGISTRATION_V1.md` for the execution-blocked design draft;
- `MARKET_ECOLOGY_DATA_PLAN.md` for selective data certification;
- `EDGE_LIFECYCLE_PROTOCOL.md` for expiring authorization and distinct authorities;
- `ADAPTIVE_MARKETS_RECONCILIATION_2026_09_19.md` for inspected repository state.

The expanded lifecycle is market ecology → mechanism → hypothesis → preregistration → certified data → Development test → regime/robustness analysis → Validation → locked OOS → paper trading → controlled live trading → edge-health monitoring → maintain / reduce / suspend / retire. It does not supersede any existing gate or authorize execution.

## Empirical literature and limits of transfer

These sources motivate methods and cautions; project-specific windows, thresholds and governance are engineering choices, not methods prescribed or endorsed by Lo.

| Primary source | Relevance and limit | Verification in this phase |
| --- | --- | --- |
| [Lo (2004), Adaptive Markets Hypothesis](https://web.mit.edu/Alo/www/Papers/JPM2004_Pub.pdf) | Evolutionary framing motivates changing opportunity sets; does not establish a crypto edge | MIT-hosted full paper available |
| [Lo (2005), Reconciling Efficient Markets with Behavioral Finance](https://web.mit.edu/Alo/www/Papers/JIC2005_Final.pdf) | Market ecology and adaptation motivate falsifiable conditional questions | MIT-hosted full paper available |
| [Lo and MacKinlay (1988), Stock Market Prices Do Not Follow Random Walks](https://doi.org/10.1093/rfs/1.1.41), [NBER working paper 2168](https://www.nber.org/papers/w2168) | Variance-ratio approach; rejection of a specified random walk is not proof of profitable predictability | Primary bibliographic/search record checked; full-text access failed here; equation audit remains blocked |
| [Lo, Mamaysky and Wang (2000), Foundations of Technical Analysis](https://www.cis.upenn.edu/~mkearns/teaching/cis700/lo.pdf) | Algorithmic pattern definitions and conditional-distribution comparisons replace visual assertion; evidence for US stocks does not transfer automatically to BTC/ETH | University-hosted full paper available; no new pattern strategy proposed |
| [Lo and MacKinlay (1990), An Econometric Analysis of Nonsynchronous Trading](https://doi.org/10.1016/0304-4076(90)90098-E), [NBER working paper 2960](https://www.nber.org/papers/w2960) | Asynchronous observations can alter measured dependence; motivates timestamp and staleness controls | Primary bibliographic/search abstract checked; full-text retrieval failed here |
| [Lo (2002), The Statistics of Sharpe Ratios](https://alo.mit.edu/publications/page/18/) | Estimation uncertainty and serial correlation complicate risk-adjusted performance and time scaling; no naive square-root annualization assumption | Author's MIT publication record and abstract checked |
| [MIT 15.481x course](https://ocw.mit.edu/courses/15-481x-adaptive-markets-financial-market-dynamics-and-human-behavior-fall-2022/) | Educational context only, not empirical confirmation | Official course page checked |
| [Newey and West (1987), HAC covariance estimator](https://www.jstor.org/stable/1913610) | Proposed robust uncertainty framework; finite-sample calibration and assumptions still require independent review | Primary journal bibliographic record checked |

No inaccessible source is represented as fully audited. Implementation-specific formulas and inference cannot be certified from titles, citations or search snippets. Null, insufficient-data and microstructure-confounded findings remain legitimate; the objective is not to prove AMH correct.
