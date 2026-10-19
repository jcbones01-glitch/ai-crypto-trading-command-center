# Institutional Research Appendix Expansion — 2026-09-19

Status: **RESEARCH CONTEXT / NO NEW AUTHORIZATION**

This document extends the project's existing institutional quantitative-trading research with additional evidence gathered through Deep Research on 2026-09-19.

It is documentation only. It does **not** authorize:
- changes to frozen AMS-DEP specifications or thresholds;
- new market-data execution;
- Validation/OOS access;
- protected holdout access;
- strategy P&L;
- paper trading;
- broker/exchange connectivity;
- live trading;
- autonomous strategy deployment.

Existing machine-readable release gates remain controlling.

## Executive gap analysis

The project's prior institutional research already covered:
- US / UK / China / India quantitative and algorithmic trading;
- machine learning, deep learning, reinforcement learning and LLMs;
- agentic quantitative-research workflows;
- market microstructure;
- institutional firms and public research culture;
- regulators and central banks;
- overfitting, data leakage and multiple testing;
- feature, alpha and research-object registries;
- execution realism;
- edge-health monitoring.

The 2026-09-19 Deep Research extension identified the most important remaining gaps as:

1. **Research reproducibility and auditability**
2. **Complete search-budget and exposure accounting**
3. **Point-in-time data and feature provenance**
4. **Statistically valid false-discovery control**
5. **Agent capability separation enforced technically**
6. **Crypto-specific execution and microstructure realism**
7. **Regime-change and edge-decay monitoring**
8. **Economic-significance testing net of all costs**
9. **Systemic risks from interacting AI agents**
10. **Operational resilience and security controls**

The central design conclusion is:

> Add auditability now. Add research automation next. Add execution realism later. Do not expand trading authority.

## Key new findings

### 1. AI should automate research faster than capital allocation

Current public evidence from central banks and regulators supports a cautious interpretation of AI in markets.

The Federal Reserve's 2025 Financial Stability Report describes present AI use in trading primarily as an extension of established machine-learning, statistical and data-analysis practices rather than a complete replacement of the trading process.

The Bank of England has highlighted both potential efficiency gains and risks from:
- correlated positioning;
- model opacity;
- autonomous behavior;
- common model/provider dependence;
- third-party concentration.

BIS Project Logos is explicitly studying populations of LLM-based portfolio-manager agents in simulated financial markets, indicating that regulators are concerned with **collective behavior**, not only individual model performance.

Project implication:

[
oxed{	ext{Research autonomy should increase faster than capital authority.}}
]

Primary sources:
- Federal Reserve Financial Stability Report, Nov. 2025:
  https://www.federalreserve.gov/publications/files/financial-stability-report-20251107.pdf
- Bank of England, AI in the Financial System:
  https://www.bankofengland.co.uk/financial-stability-in-focus/2025/april-2025
- Bank of England Financial Stability Report, July 2026:
  https://www.bankofengland.co.uk/financial-stability-report/2026/july-2026
- BIS Project Logos:
  https://www.bis.org/project/logos

### 2. Reproducibility is a larger bottleneck than model sophistication

A 2026 audit of LLM/agentic trading research reviewed 77 studies and examined 19 primary empirical studies in more detail. Its most important contribution is methodological rather than promotional: reported trading studies often lacked enough information for independent reproduction.

Reported weaknesses included sparse documentation of:
- time-consistent train/test splits;
- transaction costs;
- survivorship/universe handling;
- leakage controls;
- execution assumptions;
- reproducible artifact chains.

Project implication:

Before adding powerful research agents, the project should make it impossible for an experiment to exist without:
- a registered research object;
- a frozen specification hash;
- a code SHA;
- dataset identity;
- search-family identity;
- exposure history;
- exact run artifact lineage.

Reference:
- *Agentic Trading: When LLM Agents Meet Financial Markets* (2026):
  https://arxiv.org/abs/2605.19337

### 3. Cheap AI experimentation creates a search-budget problem

If a research system can create hundreds or thousands of strategy variants, then the experiment count itself becomes part of the statistical model.

For (m) independent null tests at nominal significance level (alpha), the expected number of false positives is:

[
E[V] = malpha
]

so 1,000 null tests at 5% nominal significance imply approximately 50 expected nominal positives before correction.

Real research families are dependent, so naive arithmetic is not sufficient; however, the core point remains:

**AI-generated research volume is not independent evidence.**

The project should account for:
- all hypotheses generated;
- all tested variants;
- failed ideas;
- parameter searches;
- correlated variants;
- aborted experiments;
- protected-sample exposures;
- result-informed redesigns.

Recommended controls:
- Holm or other FWER procedures for confirmatory finite families;
- Benjamini-Hochberg/FDR reporting for exploratory families;
- Deflated Sharpe Ratio where applicable;
- Probability of Backtest Overfitting / selection diagnostics;
- independent replication;
- frozen holdouts;
- synthetic-null calibration of the research process itself.

### 4. A null-strategy battery should test the research process

A high-value future control is a deterministic synthetic-null battery.

The project should generate strategies known to have no edge and submit them to the same:
- feature-selection;
- parameter-search;
- model-selection;
- ranking;
- promotion;
- multiple-testing;
- review

pipeline used for real research.

If the platform promotes too many nulls relative to its declared statistical error budget, the **research process itself** fails.

This turns false-discovery control into a testable software/governance property.

### 5. Point-in-time correctness must become a first-class data property

Future crypto research should explicitly preserve:

- source timestamp;
- exchange/event timestamp;
- ingestion timestamp;
- publication/availability timestamp;
- parser version;
- raw payload hash;
- schema version;
- symbol/contract identity;
- delisting/suspension history;
- missingness and outage records;
- revision history;
- transformation/version lineage.

This is particularly important for:
- funding rates;
- basis;
- liquidation data;
- order books;
- on-chain data;
- exchange announcements;
- social/news text;
- token listings/delistings;
- protocol events.

A feature is not point-in-time safe merely because the raw source is historical.

### 6. Crypto-specific microstructure needs its own research program

Crypto execution differs from simple OHLCV spot simulation because of:

- fragmented venues;
- 24/7 trading;
- perpetual futures;
- variable funding;
- exchange-specific fees/rebates;
- liquidation cascades;
- cross-venue lead/lag;
- order-book fragmentation;
- latency asymmetry;
- maker/taker economics;
- exchange outages;
- wash trading/manipulation risk;
- stablecoin and collateral effects;
- venue-specific margin rules;
- contract specification changes.

Future execution research should model economic value as:

[
	ext{Net Value}
=
	ext{Gross Alpha}
-
	ext{Spread}
-
	ext{Fees}
-
	ext{Slippage}
-
	ext{Impact}
-
	ext{Funding/Financing}
-
	ext{Adverse Selection}
]

Prediction accuracy without positive net economic value is not sufficient evidence of a tradable edge.

### 7. RL should be treated primarily as a control problem

Current evidence does not justify treating reinforcement learning as a general "discover profitable trades" shortcut.

Its more defensible research uses include:
- execution;
- inventory control;
- market making;
- allocation;
- hedging;
- constrained decision problems.

Major risks include:
- simulator exploitation;
- reward hacking;
- unrealistic fills;
- unrealistic market impact;
- distribution shift;
- poor offline-policy coverage;
- unstable regime transfer.

Project implication:

No RL experiment should be accepted unless the simulator and reward model are themselves separately validated.

Representative sources:
- Systematic review of RL for automated portfolio management (2026):
  https://link.springer.com/article/10.1007/s10791-026-10336-1
- Parallel Market Environments for FinRL Contests:
  https://www.arxiv.org/pdf/2504.02281v2

### 8. LLM financial-agent backtests require leakage controls specific to foundation models

A modern foundation model may have been pretrained on data that post-dates the simulated trading period.

That creates a leakage channel not captured by ordinary train/test splits.

Future LLM-based trading research should record:
- model name/version;
- model release date;
- known pretraining cutoff where available;
- prompt templates;
- retrieval corpus;
- retrieval timestamps;
- model temperature/settings;
- tool calls;
- external search permissions;
- whether the model could have memorized target-period events.

Reference:
- *Revisiting Information Leakage in LLM-based Financial Agents* (2025):
  https://arxiv.org/html/2510.07920v1

### 9. Multi-agent finance introduces systemic behavior not visible at single-agent level

Emerging evidence and regulator attention suggest future agent research must test:
- correlated decision making;
- common-model herding;
- shared-data dependence;
- feedback loops;
- collusive or manipulation-like behavior;
- collective liquidity withdrawal;
- simultaneous de-risking;
- concentration in the same infrastructure/provider.

This means future agent simulation should measure both:

[
	ext{individual-agent performance}
]

and

[
	ext{population-level market behavior}.
]

Relevant sources:
- BIS Project Logos:
  https://www.bis.org/project/logos
- AI-Powered Trading, Algorithmic Collusion, and Price Efficiency:
  https://www.nber.org/
- Spoofing and Manipulating Order Books with Learning Algorithms:
  https://papers.ssrn.com/

### 10. Regulation is converging on traceability, testing and accountability

Across jurisdictions, a common direction is visible even though legal regimes differ.

#### United States
Current official material emphasizes:
- financial-stability implications of AI;
- conflicts and misleading AI claims;
- conventional market-risk and manipulation obligations continuing to apply.

The SEC's 2023 predictive-data-analytics proposal was withdrawn in June 2025 and should be treated as regulatory history, not current law.

#### United Kingdom
The FCA has emphasized:
- development controls;
- testing;
- deployment governance;
- monitoring;
- risk controls.

The Bank of England is studying AI-related financial-stability risks and collective agent behavior.

#### China
Program-trading rules emphasize:
- report-before-trade;
- strategy/system metadata;
- software versions;
- order-rate information;
- high-frequency oversight;
- test artifacts;
- operational controls.

#### India
SEBI/NSE frameworks increasingly formalize:
- retail algo access;
- broker/API accountability;
- algo-provider controls;
- exchange-facing testing/identification.

Project implication:

Future automated components should have:
- immutable identities;
- software/model versions;
- deployment approval;
- explicit permissions;
- operational limits;
- incident records;
- kill/revoke capability.

## Updated evidence categories

Every external claim used in project research should be assigned one of four evidence classes.

### A. Established / high-confidence evidence
Examples:
- official regulator rules;
- exchange rulebooks;
- central-bank reports;
- well-established statistical methodology;
- peer-reviewed methodological results.

### B. Promising but uncertain research
Examples:
- recent agentic-trading systems;
- LLM+RL architectures;
- novel multimodal models;
- multi-agent finance experiments.

### C. Practitioner claim / implementation intelligence
Examples:
- firm blog architecture;
- YouTube workflows;
- conference talks;
- community implementation discussion.

These can inform engineering but do not prove alpha.

### D. Project-specific empirical evidence
Only results generated under this repository's frozen governance process qualify.

External profitability claims never substitute for project evidence.

## Representative academic / technical sources

### Reviews and surveys

- Machine learning in stock market forecasting: a comprehensive review (2026):
  https://link.springer.com/article/10.1007/s10791-026-10491-5
- Deep learning for algorithmic trading: systematic review (2025):
  https://www.sciencedirect.com/science/article/pii/S2590005625000177
- LLM-enhanced reinforcement learning in financial markets (2026):
  https://link.springer.com/article/10.1007/s44163-026-02018-0
- Systematic review of RL for automated portfolio management (2026):
  https://link.springer.com/article/10.1007/s10791-026-10336-1
- Agentic quantitative trading survey (2026):
  https://arxiv.org/html/2608.31041v1
- Agentic Trading audit (2026):
  https://arxiv.org/abs/2605.19337

### Agentic / LLM systems

- TradingAgents:
  https://arxiv.org/abs/2412.20138
- FinMem:
  https://arxiv.org/abs/2311.13743
- FinAgent:
  https://arxiv.org/abs/2402.18485
- FinGPT:
  https://arxiv.org/abs/2310.04793
- PIXIU:
  https://arxiv.org/abs/2306.05443
- CFGPT:
  https://arxiv.org/abs/2309.10654
- Long-horizon LLM investing benchmark:
  https://arxiv.org/abs/2505.07078
- Leakage-aware financial-agent benchmark:
  https://arxiv.org/html/2510.07920v1

## Practitioner evidence boundary

Practitioner and community sources are useful for:
- engineering patterns;
- failure modes;
- workflow design;
- operational lessons.

They are not evidence of durable alpha.

Useful implementation-oriented sources include:
- Man AHL AlphaTrend / agentic research:
  https://www.man.com/insights/alphatrend-agentic-research-workflows
- Two Sigma AI outlook:
  https://www.twosigma.com/articles/ai-in-investment-management-2026-outlook-part-ii/
- Jane Street real-world ML:
  https://blog.janestreet.com/
- QuantInsti / Tucker Balch:
  https://www.youtube.com/watch?v=62pfbky3KPQ
- Ernest Chan / Jared Broad / Jiri Pik:
  https://www.youtube.com/watch?v=dHlBxjbzrtU
- QuantInsti agentic research demo:
  https://www.youtube.com/watch?v=-TObBHDcINw
- Reddit r/algotrading:
  https://www.reddit.com/r/algotrading/
- Reddit r/quant:
  https://www.reddit.com/r/quant/

## New project priorities from this research

### Add now
- Research Object Registry specification
- Search / Exposure Ledger specification
- Feature Registry specification
- Multiple-testing policy
- Agent capability/security model
- evidence ledger for external research
- null-strategy governance battery design

### Add later
- registry validators;
- append-only exposure events;
- statistical multiplicity module;
- edge-health engine;
- execution simulator specification;
- agentic research orchestrator;
- alpha correlation registry;
- controlled portfolio/risk layer.

### Do not add yet
- unrestricted autonomous trader;
- live broker connectivity;
- self-modifying strategy agent;
- production RL trader;
- live leverage controller;
- large multi-agent trading swarm;
- unrestricted protected-data access;
- production order-book execution engine.

## Research questions still unresolved

1. Can crypto market-state dependence survive microstructure controls?
2. Which apparent edges survive exact point-in-time data reconstruction?
3. How much predictive performance disappears after realistic spread, slippage, funding and impact?
4. How should correlated AI-generated hypotheses be grouped into statistical families?
5. What null-calibration procedure best measures false-discovery inflation for agentic research?
6. Which regime-change detectors provide useful warning without creating excessive false alarms?
7. How much value do LLM-derived features add after controlling for simpler text and tabular baselines?
8. Can RL execution improvements survive simulator-to-live distribution shift?
9. How should the project quantify edge decay after deployment without contaminating future OOS evidence?
10. What minimum operational-resilience controls are required before any paper/live execution is considered?

## Final project principle

The additional research strengthens, rather than changes, the existing project philosophy:

[
oxed{
	ext{ECOLOGY}
ightarrow
	ext{MECHANISM}
ightarrow
	ext{HYPOTHESIS}
ightarrow
	ext{DATA}
ightarrow
	ext{TEST}
ightarrow
	ext{REPLICATE}
ightarrow
	ext{VALIDATE}
ightarrow
	ext{PAPER}
ightarrow
	ext{EXECUTE}
ightarrow
	ext{MONITOR}
}
]

with

[
oxed{	ext{GOVERNANCE + RISK}}
]

surrounding the full lifecycle.

No conclusion in this appendix overrides the current AMS-DEP release-gate state.
