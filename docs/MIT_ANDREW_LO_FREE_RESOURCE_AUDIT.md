# MIT / Andrew Lo Free Resource Audit

## Status

**VERIFIED FREE PRIMARY-RESOURCE ROADMAP**

This document records official MIT / Andrew W. Lo materials that are freely
available and identifies how they should be used in the Adaptive Markets
research phase.

The goal is not to copy a trading strategy from course slides. The goal is to
extract research methods, statistical cautions, economic mechanisms, and
governance principles from primary teaching/research sources.

## Official free course

### MIT 15.481x — Adaptive Markets: Financial Market Dynamics and Human Behavior

Instructor: Andrew W. Lo, MIT Sloan School of Management.

Official MIT OpenCourseWare / Open Learning Library materials include lecture
videos, tutorial videos, problem sets, problem-set solutions, slides, and
course transcripts. The archived course remains reviewable.

The course sequence is directly relevant to this repository:

1. Introduction and Financial Orthodoxy
2. Rejecting the Random Walk and Efficient Markets
3. Psychology and Behavioral Biases
4. Neuroscience and Decision-Making
5. Evolution and the Origin of Behavior
6. The Adaptive Markets Hypothesis
7. Hedge Funds — The Galapagos Islands of Finance
8. Applications of Adaptive Markets
9. The Financial Crisis
10. Ethics and Adaptive Markets
11. The Future of Finance and the Finance of the Future

## Priority extraction for this project

### Priority A — Unit 2: Rejecting the Random Walk and Efficient Markets

Verified course components:
- The Random Walk Hypothesis
- Contemporary Tests of the Random Walk
- Tutorial: Random Walks and Variance Ratio Tests

Repository use:
- review the exact conceptual distinction between random-walk rejection,
  return dependence, and market inefficiency;
- compare the course treatment of variance-ratio testing with
  `AMS_DEP_NUMERICAL_CONTRACT_V1.md`;
- use the tutorial as an educational cross-check for the Lo–MacKinlay
  implementation and interpretation;
- preserve the rule that rejecting a random walk does not itself imply an
  executable or profitable trading rule;
- use finite-sample calibration before market-data release.

Immediate relevance:
**Issue #43 / AMS-DEP V2 is the highest-priority application of Unit 2.**

### Priority B — Unit 6: The Adaptive Markets Hypothesis

Verified course components:
- The Origin of Behavior
- Human and Artificial Intelligence
- The Adaptive Markets Hypothesis
- Binary Choice Model tutorial

Repository use:
- refine the distinction between static efficiency and adaptive/time-varying
  opportunity sets;
- explicitly model adaptation, competition, environmental change and strategy
  decay as hypotheses rather than assumptions;
- keep AI as an adaptive research proposer, not an unconstrained execution
  authority;
- improve edge-lifecycle / retirement rules.

Immediate relevance:
- `ADAPTIVE_MARKETS_FRAMEWORK.md`
- `EDGE_LIFECYCLE_PROTOCOL.md`
- future AI-research-agent authority design.

### Priority C — Unit 7: Hedge Funds — The Galapagos Islands of Finance

Verified course components:
- What is a Hedge Fund?
- Alpha, Beta and Hedge Fund Replication
- Implication for the Current Financial Landscape
- Linear Regression tutorial
- regression tutorial using spreadsheet tools

Repository use:
- distinguish genuine alpha from replicable systematic exposures;
- require candidate crypto strategies to demonstrate that apparent alpha is
  not merely exposure to BTC/ETH beta, volatility, trend, liquidity or other
  common factors;
- improve benchmark/factor attribution before strategy promotion;
- use the ecological analogy to motivate crowding, competition and strategy
  lifecycle monitoring.

Future requirement:
Before calling a strategy "edge", add an **exposure attribution layer** that
tests whether returns can be explained by registered common crypto factors.

### Priority D — Unit 8: Applications of Adaptive Markets

Verified course components:
- Hedge Fund Risk and Illiquidity
- Hedge Funds and Systemic Risk
- The Confluence of Technology with Human Behavior
- supplemental adaptive-markets application material

Repository use:
- treat liquidity as a state variable and risk mechanism, not merely a
  transaction-cost constant;
- add liquidity/market-impact stress to later execution research;
- distinguish mark-to-market performance from liquidity-adjusted realizable
  performance;
- treat leverage, crowding and forced deleveraging as market-ecology variables;
- connect future liquidation/open-interest/basis/order-book work to explicit
  mechanisms rather than feature mining.

Immediate relevance:
- `MARKET_ECOLOGY_DATA_PLAN.md`
- future derivatives/open-interest/liquidation research;
- later paper/live risk-governor design.

## Andrew Lo publication archive

Andrew Lo's official MIT site provides a publication archive with abstracts
and, for some papers, downloadable versions.

High-priority papers already mapped into this repository:
- Adaptive Markets Hypothesis;
- Stock Market Prices Do Not Follow Random Walks;
- Size and Power of the Variance Ratio Test in Finite Samples;
- Foundations of Technical Analysis;
- Data-Snooping Biases in Tests of Financial Asset Pricing Models;
- An Econometric Analysis of Nonsynchronous Trading;
- The Statistics of Sharpe Ratios;
- Maximizing Predictability in the Stock and Bond Markets.

The archive should remain the preferred discovery source for Lo-authored
material before using secondary summaries.

## New project requirements derived from the free MIT material

### 1. Statistical-test calibration ledger

For every important inferential procedure, record:
- null DGPs;
- alternative DGPs;
- empirical size;
- power;
- sample size;
- dependence/heteroskedasticity assumptions;
- failure modes;
- whether release to empirical data is authorized.

This is already being applied to AMS-DEP.

### 2. Alpha-versus-exposure attribution

Before strategy promotion, require a preregistered test of whether candidate
returns are explainable by common exposures such as:
- BTC market beta;
- ETH/alt beta where appropriate;
- trend/momentum;
- realized volatility;
- liquidity/activity;
- carry/funding/basis when certified.

A strategy does not receive an "alpha" label merely because raw backtest
returns are positive.

### 3. Liquidity-adjusted strategy evaluation

Later strategy/paper/live evaluation should distinguish:
- theoretical signal return;
- estimated executable return;
- turnover;
- spread/slippage;
- market impact;
- liquidity state;
- capacity/crowding;
- forced-exit stress.

### 4. Adaptive edge lifecycle

Every promoted edge should eventually have:
- environment/state assumptions;
- expected half-life/monitoring horizon where estimable;
- degradation indicators;
- quarantine rules;
- retirement rules;
- challenger process;
- no silent parameter self-repair.

### 5. AI behavior boundary

The Unit 6 human/artificial-intelligence material reinforces the existing
architecture:

AI may propose, summarize, simulate, diagnose and generate challenger
hypotheses.

AI may not silently:
- redefine the null;
- alter thresholds after failure;
- access protected OOS;
- change live risk limits;
- authorize leverage;
- deploy itself;
- override kill switches.

## Resource-mining order

Use the free material in this order:

1. Unit 2 + Lo–MacKinlay finite-sample papers — resolve Issue #43.
2. Unit 6 + AMH papers — refine market-state / adaptive-agent design.
3. Unit 7 — build alpha-versus-beta/factor-attribution requirements.
4. Unit 8 — build liquidity/systemic-risk/market-ecology requirements.
5. Relevant problem sets/tutorials — use as conceptual and numerical
   cross-checks where they map to repository methods.
6. Broader publication archive — expand only when a concrete research question
   requires it.

## Research-integrity boundary

MIT teaching examples and U.S.-equity empirical results are not evidence that
the same effects exist in cryptocurrency.

Course materials can:
- motivate hypotheses;
- clarify statistical methods;
- identify failure modes;
- guide economic mechanisms.

They cannot:
- substitute for crypto-specific evidence;
- authorize Validation/OOS access;
- reopen rejected HYP-0001–HYP-0025;
- authorize a strategy;
- authorize paper/live trading.

## Current action

The highest-value free MIT resource for the current blocker is Unit 2,
especially the random-walk / variance-ratio tutorial and Lo–MacKinlay
finite-sample testing work.

Use those resources to guide the independent design review of AMS-DEP V2.
Do not inspect actual BTC/ETH dependence results until a prospectively frozen
V2 passes synthetic calibration and receives the required release approval.
