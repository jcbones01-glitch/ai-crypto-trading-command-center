# Andrew Lo Research Integration Plan

## Status

**ACTIVE METHODOLOGICAL BACKBONE — DOES NOT AUTHORIZE EMPIRICAL RELEASE OR TRADING**

This document defines how Andrew W. Lo's published research should guide the Adaptive Markets phase of the AI Crypto Trading Command Center.

The objective is not to copy a single trading strategy. The objective is to adopt a research program: test whether predictability changes through time and market state; distinguish true dependence from microstructure artifacts; control data-snooping; evaluate finite-sample behavior before empirical release; and separate statistical predictability from economic tradability.

All existing Development → Validation → locked OOS controls, preregistration, causal timing, continuity, provenance, cost/slippage, robustness, and execution-authority boundaries remain in force.

## Primary Lo methods mapped to this repository

### 1. Adaptive Markets Hypothesis

Primary source:
- Andrew W. Lo (2004), "The Adaptive Markets Hypothesis: Market Efficiency from an Evolutionary Perspective."

Project use:
- Treat market efficiency and exploitable predictability as potentially time-varying rather than permanently present or permanently absent.
- Test whether return dependence changes across predeclared calendar periods and frozen AMS-V1 states.
- Treat strategies as ecological competitors whose profitability may appear, decay, disappear, and possibly re-emerge.
- Build edge-lifecycle rules so an approved strategy can later be reduced, suspended, or retired when evidence changes.

Project limitation:
- AMH is a framework that motivates falsifiable questions. It does not prove that BTC or ETH contain a profitable edge.

### 2. Variance-ratio / random-walk diagnostics

Primary sources:
- Lo and MacKinlay (1987/1988), "Stock Market Prices Do Not Follow Random Walks: Evidence From a Simple Specification Test."
- Lo and MacKinlay (1988/1989), "The Size and Power of the Variance Ratio Test in Finite Samples: A Monte Carlo Investigation."

Project use:
- Use preregistered variance-ratio diagnostics at fixed horizons to measure departures from random-walk behavior.
- Preserve finite-sample Monte Carlo calibration as a mandatory gate before using inference on BTC/ETH.
- Report variance-ratio point estimates separately from claims of profitability.
- Never treat random-walk rejection as proof of mean reversion, momentum, or an executable strategy.

Direct implication for Issue #43:
- The current AMS-DEP V1 failure is consistent with Lo and MacKinlay's emphasis on studying test size and power in finite samples before trusting empirical significance.
- A V2 inference design must be prospectively calibrated on synthetic nulls before empirical release.

### 3. Systematic technical-pattern testing

Primary source:
- Lo, Mamaysky, and Wang (2000), "Foundations of Technical Analysis: Computational Algorithms, Statistical Inference, and Empirical Implementation."

Project use:
- Replace subjective chart-reading with deterministic, machine-readable pattern definitions.
- Compare conditional return distributions after a registered pattern/event against appropriate unconditional/control distributions.
- Use Monte Carlo/bootstrap methods where appropriate and preregister all pattern-recognition parameters before evidence.
- Evaluate whether a feature contains incremental information before converting it into a trading strategy.

Project limitation:
- Their empirical results are from U.S. equities and do not transfer automatically to crypto.
- The completed HYP-0001–HYP-0025 OHLCV family remains closed. Their method can inform new research design but cannot retroactively rescue those hypotheses.

### 4. Data-snooping control

Primary source:
- Lo and MacKinlay (1990), "Data-Snooping Biases in Tests of Financial Asset Pricing Models."

Project use:
- Keep a complete hypothesis/search ledger.
- Count repeated parameter, feature, horizon, state, and model searches as part of the effective research family.
- Require prospective registration before new Development evidence.
- Preserve failed/null results.
- Never select favorable states, thresholds, lags, or assets after viewing results and then present them as independent evidence.

This strengthens the project's existing multiple-testing and OOS firewall rather than replacing them.

### 5. Nonsynchronous trading and microstructure effects

Primary source:
- Lo and MacKinlay (1989/1990), "An Econometric Analysis of Nonsynchronous Trading."

Project use:
- Treat measured autocorrelation as potentially arising from timestamp mismatch, stale observations, bid/ask bounce, venue mechanics, or asynchronous information arrival.
- Require exact-time joins and continuity-safe lag calculations.
- Do not compress gaps or treat irregular observations as adjacent hourly data.
- Add certified finer-frequency trades/quotes or derivatives-market data before attributing dependence to market ecology.

This is especially important for crypto, where exchange mechanics, perpetual futures, fragmented venues, stablecoin quoting, and 24/7 trading can create measurement effects.

### 6. Serial correlation and risk measurement

Primary source:
- Andrew W. Lo (2002), "The Statistics of Sharpe Ratios."

Project use:
- Do not assume IID returns when evaluating strategy performance.
- Do not mechanically annualize Sharpe ratios with square-root-of-time scaling when serial correlation makes that invalid.
- Report uncertainty around performance statistics.
- Preserve serial-correlation-aware risk diagnostics in later paper/live evaluation.

### 7. Predictability that changes by asset, horizon, and environment

Primary source:
- Lo and MacKinlay (1995/1997), "Maximizing Predictability in the Stock and Bond Markets."

Project use:
- Treat predictability as conditional on asset, horizon, and observable information set.
- Require genuine out-of-sample evaluation before calling predictability economically meaningful.
- Separate a statistical forecast signal from position sizing, costs, risk, and execution.

## Lo-guided research sequence for this project

The intended sequence is:

`MARKET ECOLOGY → MEASURABLE DEPENDENCE → MECHANISM → PROSPECTIVE HYPOTHESIS → SYNTHETIC CALIBRATION → DEVELOPMENT TEST → ROBUSTNESS → VALIDATION → LOCKED OOS → PAPER TRADING → CONTROLLED LIVE → EDGE MONITORING`

### Phase A — Measurement and dependence

Current active work.

Questions:
- Does signed-return dependence exist?
- Does it vary through time?
- Does it vary across frozen AMS-V1 states?
- Is measured dependence robust to finite-sample inference?
- Could it be explained by microstructure or measurement artifacts?

No strategy P&L is authorized in this phase.

### Phase B — Market ecology data

Certify variables that represent market ecology more directly than spot candles alone, including where source quality permits:

- perpetual-futures funding;
- futures-vs-spot basis;
- open interest;
- volume/liquidity measures;
- spreads/order-book information;
- liquidation activity;
- options/implied-volatility information;
- macro/event variables;
- regulatory/institutional events.

Every source requires its own point-in-time certification before use.

### Phase C — Mechanism-specific hypotheses

Only after Phase A/B evidence supports a plausible mechanism may the project preregister a new strategy hypothesis.

Examples of acceptable mechanism questions:
- Does short-horizon dependence change when derivatives positioning is extreme?
- Does predictability decay as market participation/liquidity changes?
- Are apparent price patterns confined to environments with particular volatility/liquidity characteristics?
- Are event-driven effects distinct from endogenous price-pattern effects?

These are research questions, not assumed trading edges.

### Phase D — Economic translation

Statistical predictability must be converted into a deterministic StrategySpecification with:

- exact observable inputs;
- causal timing;
- entry/exit;
- sizing;
- fees/slippage;
- turnover;
- drawdown and concentration controls;
- regime conditions;
- invalidation and retirement rules.

Only then can a strategy enter the existing evidence gates.

## Current gate after AMS-DEP V1 failure

AMS-DEP V1 produced excessive false rejections in synthetic nulls.

Therefore:

**DO NOT inspect actual BTC/ETH dependence results with V1.**

The next Lo-consistent action is to diagnose and redesign finite-sample inference using synthetic data only. This follows the spirit of Lo and MacKinlay's finite-sample size/power work.

V2 must be specified before results and must not:
- raise the false-rejection ceiling because V1 failed;
- remove difficult null cases;
- reroll seeds;
- choose an inference method based on BTC/ETH significance;
- weaken multiplicity;
- use Validation/OOS.

Candidate methods may include a properly designed null-imposed bootstrap/resampling approach, but the exact method must be justified and frozen before V2 execution.

## Interpretation rules

The project must keep these distinctions explicit:

- Random-walk rejection ≠ profitable strategy.
- Serial dependence ≠ causal mechanism.
- Statistical significance ≠ economic significance.
- Technical-pattern information ≠ execution-ready edge.
- High Sharpe estimate ≠ precisely measured risk-adjusted performance.
- Market-state dependence ≠ proof of AMH.
- AMH ≠ permission to fit flexible regimes after seeing outcomes.

Andrew Lo's research should make the project harder to fool, not easier to promote a strategy.

## Primary references

- Lo, Andrew W. (2004), "The Adaptive Markets Hypothesis: Market Efficiency from an Evolutionary Perspective," Journal of Portfolio Management 30(5), 15–29.
- Lo, Andrew W., and A. Craig MacKinlay (1988), "Stock Market Prices Do Not Follow Random Walks: Evidence From a Simple Specification Test," Review of Financial Studies 1(1), 41–66.
- Lo, Andrew W., and A. Craig MacKinlay (1989), "The Size and Power of the Variance Ratio Test in Finite Samples: A Monte Carlo Investigation," Journal of Econometrics 40, 203–238.
- Lo, Andrew W., Harry Mamaysky, and Jiang Wang (2000), "Foundations of Technical Analysis: Computational Algorithms, Statistical Inference, and Empirical Implementation," Journal of Finance 55(4), 1705–1765.
- Lo, Andrew W., and A. Craig MacKinlay (1990), "Data-Snooping Biases in Tests of Financial Asset Pricing Models," Review of Financial Studies 3(3), 431–467.
- Lo, Andrew W., and A. Craig MacKinlay (1990), "An Econometric Analysis of Nonsynchronous Trading," Journal of Econometrics 45, 181–211.
- Lo, Andrew W. (2002), "The Statistics of Sharpe Ratios," Financial Analysts Journal 58(4), 36–52.
- Lo, Andrew W., and A. Craig MacKinlay (1997), "Maximizing Predictability in the Stock and Bond Markets," Macroeconomic Dynamics 1(1), 102–134.
