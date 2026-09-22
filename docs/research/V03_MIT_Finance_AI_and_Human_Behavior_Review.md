# V03 — MIT “Finance, AI, and Human Behavior” / Andrew Lo Review

**Project:** AI Crypto Trading Command Center  
**Playbook item:** V03  
**Review date:** 2026-09-20  
**Primary source:** MIT OpenCourseWare / Chalk Radio — *MIT Economist Andrew W. Lo on Finance, AI, and Human Behavior*  
**Speaker:** Andrew W. Lo  
**Host:** Sarah Hansen  
**MIT publication date:** 2025-04-16  
**Video length:** approximately 38:49  
**Playbook URL:** https://www.youtube.com/watch?v=8kFFg5jAoQc  
**Official MIT page:** https://ocw.mit.edu/courses/15-481x-adaptive-markets-financial-market-dynamics-and-human-behavior-fall-2022/resources/mit-economist-andrew-w-lo-on-finance-ai-and-human-behavior/  
**Official MIT transcript:** https://ocw.mit.edu/courses/15-481x-adaptive-markets-financial-market-dynamics-and-human-behavior-fall-2022/8kFFg5jAoQc_transcript.pdf  
**Status:** COMPLETE FOR PLAYBOOK EXTRACTION OBJECTIVE

## Decision memo

**V03 strongly supports a decision-support-first architecture for the AI Crypto Trading Command Center.**

The interview's most relevant distinction is between:

- **AI assisting humans with analysis, education, scenario generation, and information gathering**, and
- **AI being delegated authority to make consequential financial decisions.**

Lo explicitly says current large language models are not yet ready for delegated financial decision-making in the context discussed. He nevertheless sees value in using them to help people think through problems, generate questions and scenarios, and become better informed.

For this project, the source supports:

```text
AI research automation: HIGH
AI scenario generation: HIGH
AI evidence extraction: HIGH
AI second-opinion / review support: HIGH
AI independent capital-allocation authority: NOT ESTABLISHED BY THIS SOURCE
```

This is a governance implication, not a claim that no future AI system can ever trade autonomously.

V03 does not establish a profitable trading strategy, does not authorize paper/live trading, and does not override the project's existing release gates.

---

# 1. Source-verification note

The official MIT transcript was reviewed directly.

MIT also publishes a caption-file resource, but the actual WebVTT download was not retrievable through the available interface. Therefore exact timestamps below were taken from independent transcript indexes and checked against the wording/order of the official MIT transcript.

Timestamp confidence:

- transcript wording/context: **HIGH — official MIT transcript**
- timestamp location: **MODERATE/HIGH — third-party subtitle indexes cross-checked against official transcript**
- no timestamp is presented as having been extracted directly from the inaccessible MIT WebVTT file.

This preserves the playbook rule not to fabricate timing.

---

# 2. Evidence cards

## V03-C01 — Current LLMs are not ready for delegated financial decisions

```yaml
claim_id: V03-C01
source_id: MIT-LO-FINANCE-AI-HUMAN-2025
source_version: MIT OCW official transcript / 2025-04-16 release
review_status: reviewed
reviewed_at: 2026-09-20
source_locator:
  official_transcript_pages: 1-2
  official_transcript_lines: 75-100
  timestamp_range: approximately 05:23-07:55
  timestamp_source: third-party subtitle index, wording verified against MIT transcript
claim_paraphrase: >
  Lo says large language models are not yet ready to take delegated authority
  for consequential financial decisions, while still being useful for helping
  people think through financial issues and gather information.
evidence_type: expert opinion / research-program statement
market_and_sample: personal financial decision-making; not a trading experiment
data_requirements: []
method_and_assumptions:
  - current-model capability assessment
  - distinction between advice/support and delegated decision authority
reported_effect_and_uncertainty: >
  No quantitative error rate or trading-performance estimate is given.
limitations_and_contradictions:
  - retirement advice is not identical to algorithmic trading
  - statement is time-sensitive because AI capabilities change
  - source does not prove that all autonomous financial AI is unsafe or impossible
replication_assets: []
proposed_project_application: >
  Keep research/analysis automation separate from capital-allocation authority.
  Treat execution permissions as a separate gated capability.
existing_repo_overlap:
  - docs/GATE2_RESEARCH_PROTOCOL.md autonomy boundary
  - docs/GATE2_EXECUTION_CONTRACT.md
  - current paper/live-trading locks
causal_timing_requirements: []
cost_and_execution_requirements: []
falsification_or_rejection_condition: >
  Reassess only through explicit evidence that a future system satisfies the
  project's research, validation, risk, execution, and monitoring requirements;
  do not change authority because a newer model appears more capable in conversation.
next_action: retain as governance principle
decision: retain
decision_reason: directly relevant to AI-agent authority design
```

---

## V03-C02 — LLMs can be useful for research questions and decision support even when they should not make the final decision

```yaml
claim_id: V03-C02
source_id: MIT-LO-FINANCE-AI-HUMAN-2025
source_version: official MIT transcript
review_status: reviewed
reviewed_at: 2026-09-20
source_locator:
  official_transcript_pages: 2
  official_transcript_lines: 92-100
  timestamp_range: approximately 07:00-07:55
claim_paraphrase: >
  Lo distinguishes using an LLM to surface important issues, ideas, products,
  services, and information sources from allowing it to make the user's final
  financial decisions.
evidence_type: expert opinion / practical guidance
market_and_sample: personal finance
data_requirements: []
method_and_assumptions: []
reported_effect_and_uncertainty: no quantitative estimate
limitations_and_contradictions:
  - not an empirical test of trading-research productivity
  - does not establish accuracy for any specific financial task
replication_assets: []
proposed_project_application: >
  Use AI aggressively for literature review, source discovery, hypothesis
  formulation, coding assistance, test generation, scenario enumeration,
  anomaly detection, and adversarial review — while preserving explicit gates
  before capital-affecting actions.
existing_repo_overlap:
  - research-first project progression
  - institutional research appendix principle: automate research more aggressively than capital allocation
causal_timing_requirements: []
cost_and_execution_requirements: []
falsification_or_rejection_condition: >
  AI-generated research output remains provisional until source-verified,
  reproducible, and passed through the project's evidence gates.
next_action: retain
decision: retain
decision_reason: directly maps to command-center research-agent role
```

---

## V03-C03 — Human support, cross-checking, and multiple opinions are safeguards against AI errors

```yaml
claim_id: V03-C03
source_id: MIT-LO-FINANCE-AI-HUMAN-2025
source_version: official MIT transcript
review_status: reviewed
reviewed_at: 2026-09-20
source_locator:
  official_transcript_page: 2
  official_transcript_lines: 103-118
  timestamp_range: approximately 07:55-09:18
claim_paraphrase: >
  Lo argues that LLM output should be checked with human support and additional
  opinions because both humans and AI systems can make mistakes; informed users
  should verify accuracy rather than rely on a single source.
evidence_type: expert opinion / risk-control principle
market_and_sample: personal financial advice
data_requirements: []
method_and_assumptions:
  - verification reduces dependence on a single fallible source
reported_effect_and_uncertainty: no quantified reduction in error
limitations_and_contradictions:
  - multiple opinions can share the same underlying error or data source
  - human review does not guarantee correctness
  - a second AI model is not automatically independent
replication_assets: []
proposed_project_application: >
  Preserve independent-review stages, source verification, reproducibility,
  adversarial statistical review, and separation between implementation and approval.
existing_repo_overlap:
  - independent AMS-DEP review workflow
  - source-verification requirements
  - external/second-opinion research practice
causal_timing_requirements: []
cost_and_execution_requirements: []
falsification_or_rejection_condition: >
  Never classify agreement among agents/models as independent evidence unless
  the underlying data, method, and review pathway are actually independent enough
  for the stated purpose.
next_action: retain
decision: retain_with_independence_caveat
decision_reason: important oversight principle, but model consensus alone is weak evidence
```

---

## V03-C04 — AI financial systems should be designed around the user's interests, not merely capability

```yaml
claim_id: V03-C04
source_id: MIT-LO-FINANCE-AI-HUMAN-2025
source_version: official MIT transcript
review_status: reviewed
reviewed_at: 2026-09-20
source_locator:
  official_transcript_pages: 1-3
  official_transcript_lines: 82-95 and 133-138
  timestamp_range: approximately 06:07-07:27 and 10:16-10:50
claim_paraphrase: >
  Lo describes work toward an AI financial advisor that would meet a fiduciary-like
  standard: the system should be oriented toward the user's goals and best interests,
  rather than merely producing recommendations.
evidence_type: research-program objective / normative design principle
market_and_sample: financial advice
data_requirements: []
method_and_assumptions: []
reported_effect_and_uncertainty: system goal; not demonstrated in this interview
limitations_and_contradictions:
  - the interview does not define a technical test proving fiduciary behavior
  - trading-agent objectives can conflict with broader user risk preferences
  - maximizing P&L is not equivalent to acting in the user's best interests
replication_assets: []
proposed_project_application: >
  Future trading agents should optimize only within explicitly user-approved
  risk, capital, legal, liquidity, and drawdown constraints.
existing_repo_overlap:
  - capital-preservation priority
  - explicit authorization boundaries
  - prospective risk controls
causal_timing_requirements: []
cost_and_execution_requirements:
  - fees
  - slippage
  - liquidity
  - drawdown
  - capital-at-risk limits
falsification_or_rejection_condition: >
  A system that improves gross returns by violating frozen user/risk constraints
  is a governance failure, not a successful optimization.
next_action: retain for future agent-capability specification
decision: retain
decision_reason: useful objective-alignment principle
```

---

## V03-C05 — AI tools need explicit safeguards against misuse and unintended consequences

```yaml
claim_id: V03-C05
source_id: MIT-LO-FINANCE-AI-HUMAN-2025
source_version: official MIT transcript
review_status: reviewed
reviewed_at: 2026-09-20
source_locator:
  official_transcript_page: 3
  official_transcript_lines: 141-163
  timestamp_range: approximately 10:47-12:20
claim_paraphrase: >
  Lo warns that powerful AI financial tools can be abused and says developers
  should think proactively about ethical safeguards and unintended consequences.
evidence_type: expert opinion / governance warning
market_and_sample: AI-enabled financial advice and broader AI deployment
data_requirements: []
method_and_assumptions: []
reported_effect_and_uncertainty: qualitative; no probability estimate
limitations_and_contradictions:
  - does not specify the exact technical control system needed for trading
  - ethical concerns require translation into enforceable machine policies
replication_assets: []
proposed_project_application: >
  Use capability separation: research agents should not automatically inherit
  credentials, order-placement authority, leverage access, or the ability to
  weaken release gates.
existing_repo_overlap:
  - current Gate 2 autonomy boundary
  - no exchange credentials / autonomous capital deployment
  - proposed future agent-capability contracts
causal_timing_requirements: []
cost_and_execution_requirements: []
falsification_or_rejection_condition: >
  Reject architectures where a research/model-selection agent can unilaterally
  modify risk limits, release protected data, or deploy capital.
next_action: retain for future agent security model
decision: retain
decision_reason: directly relevant to agent permissions
```

---

## V03-C06 — Scenario generation is an appropriate AI role

```yaml
claim_id: V03-C06
source_id: MIT-LO-FINANCE-AI-HUMAN-2025
source_version: official MIT transcript
review_status: reviewed
reviewed_at: 2026-09-20
source_locator:
  official_transcript_pages: 6-7
  official_transcript_lines: 272-290
  timestamp_range: approximately 22:08-23:55
claim_paraphrase: >
  Lo recommends scenario analysis as a way to prepare for adverse financial
  outcomes and says large language models can play a useful role by generating
  a broad range of "what-if" scenarios.
evidence_type: expert opinion / decision-support guidance
market_and_sample: personal financial planning; conceptual
data_requirements: []
method_and_assumptions:
  - scenario enumeration can improve preparedness
reported_effect_and_uncertainty: no measured forecasting advantage
limitations_and_contradictions:
  - generating a scenario does not assign a valid probability to it
  - scenario generation is not return prediction
  - post-hoc scenario selection can create hindsight bias
replication_assets: []
proposed_project_application: >
  Use AI to generate stress scenarios for liquidity, exchange outages,
  regulatory access, slippage, volatility, funding/basis shocks, and model failure.
  Freeze the scenario set before using outcomes to evaluate a strategy.
existing_repo_overlap:
  - Oxford/geopolitical scenario framework
  - robustness/stress testing
  - R03 access/fragmentation stresses
  - R04 market-stress framing
causal_timing_requirements:
  - scenario state variables must be prospectively observable when used empirically
cost_and_execution_requirements:
  - stress assumptions must be explicit and reproducible
falsification_or_rejection_condition: >
  Do not treat AI-generated scenarios as empirical probabilities or alpha signals
  unless separately estimated and validated.
next_action: retain
decision: retain
decision_reason: high-value research/risk use with clear boundary
```

---

## V03-C07 — Human behavior can overwhelm idealized financial logic

```yaml
claim_id: V03-C07
source_id: MIT-LO-FINANCE-AI-HUMAN-2025
source_version: official MIT transcript
review_status: reviewed
reviewed_at: 2026-09-20
source_locator:
  official_transcript_pages: 6-7
  official_transcript_lines: 241-269
  timestamp_range: approximately 20:20-22:08
claim_paraphrase: >
  Lo emphasizes that human reactions and overreactions matter in financial markets,
  and presents the Adaptive Markets Hypothesis as a framework for understanding
  interactions between market logic and human behavior.
evidence_type: conceptual explanation / expert interpretation
market_and_sample: general financial markets
data_requirements: []
method_and_assumptions: []
reported_effect_and_uncertainty: no crypto-specific effect estimate
limitations_and_contradictions:
  - does not establish a measurable crypto behavioral signal
  - human-behavior labels can become retrospective narratives
replication_assets: []
proposed_project_application: >
  Preserve AMH as a hypothesis-generation framework while requiring direct,
  observable variables and preregistered tests for any crypto mechanism.
existing_repo_overlap:
  - V01 Adaptive Markets review
  - docs/ANDREW_LO_RESEARCH_INTEGRATION.md
causal_timing_requirements:
  - behavioral proxy must be available at the decision timestamp
cost_and_execution_requirements: []
falsification_or_rejection_condition: >
  No behavioral mechanism is promoted without independent empirical evidence.
next_action: none; V01 already covers core AMH literature
decision: retain_as_corroboration
decision_reason: confirms but does not expand V01's core AMH conclusions
```

---

# 3. Project architecture implication

V03 supports the following authority ladder:

```text
LEVEL 0 — Read-only research
  Search literature
  Read repository
  Inspect datasets
  Summarize evidence

LEVEL 1 — Research production
  Generate hypotheses
  Write code
  Write tests
  Generate synthetic experiments
  Propose scenarios
  Produce audit artifacts

LEVEL 2 — Controlled evidence execution
  Run prospectively approved Development tests
  Run approved robustness/calibration tasks
  Cannot access protected data without release gate

LEVEL 3 — Protected evaluation
  Validation/OOS only after explicit machine/research authorization
  No automatic retuning from protected results

LEVEL 4 — Paper execution
  Separate authorization
  Realistic execution simulator / broker sandbox
  Risk limits and kill switch
  Full audit logs

LEVEL 5 — Controlled live execution
  Separate future authorization
  Minimal capital initially
  Position/risk/exposure limits
  Exchange credentials isolated from research agents
  Monitoring and deterministic kill controls

LEVEL 6 — Adaptive live parameter changes
  NOT IMPLIED BY V03
  Would require its own governance and validation framework
```

This is a **project interpretation** of V03, not language claimed by Andrew Lo.

---

# 4. Human oversight does not mean manual micromanagement

V03 should not be misread as requiring a human to:

- manually write every line of code;
- manually calculate every indicator;
- manually inspect every market tick;
- manually approve every research query;
- manually place every future order forever.

The useful distinction is:

```text
automation of process != delegation of unrestricted authority
```

A highly automated system can still preserve human agency through:

- prospectively defined permissions;
- machine-enforced limits;
- independent validation;
- immutable logs;
- protected-data gates;
- capital limits;
- kill switches;
- exception escalation;
- periodic human review.

This distinction is especially important for the user's goal of eventually having agents operate while the user is working.

---

# 5. Relationship to the institutional research appendix

The institutional research corpus already argues that current AI-trading research has substantial weaknesses in:

- reproducibility;
- leakage control;
- transaction-cost modeling;
- governance;
- systemic/correlated-agent risk.

V03 is consistent with that corpus but is not independent empirical proof of those claims.

Together, the materials support the working project principle:

```text
AUTOMATE RESEARCH AGGRESSIVELY
GATE EVIDENCE RIGOROUSLY
EXPAND EXECUTION AUTHORITY SLOWLY
```

That principle is a **project synthesis**, not a direct quotation from V03.

---

# 6. What V03 does not authorize

V03 provides no basis to:

- let ChatGPT or another LLM choose and deploy capital autonomously today;
- give research agents exchange API keys;
- let an agent modify its own risk limits;
- let an agent change preregistered parameters after viewing results;
- let AI bypass Validation/OOS gates;
- let AI convert its own scenarios into trading signals without testing;
- claim fiduciary behavior merely because a model says it is acting in the user's interest;
- infer that more capable future models automatically deserve more financial authority.

---

# 7. Source-quality and timestamp record

## Official primary source

MIT OpenCourseWare provides:

- official video page;
- official transcript PDF;
- official caption-resource page.

The official transcript was directly reviewed.

The screenshot endpoint for the PDF failed because the web cache could not fetch the PDF image pages, but the PDF text extraction was available and used. No visual/layout claim is relied upon.

## Timestamp verification

Useful timestamp indexes were found from independent transcript services.

Examples:

- delegated financial decision-making: approximately **05:23 onward**
- fiduciary AI discussion: approximately **06:39-07:27**
- "don't let it make your decisions" context: approximately **07:27-07:55**
- human support / checking / second opinions: approximately **07:55-09:18**
- AI misuse and ethics: approximately **10:47-11:52**
- scenario analysis and AI-generated "what ifs": approximately **22:08-23:55**

The official MIT transcript confirms the ordering and substantive wording. Because the official WebVTT file itself was not retrievable in the current environment, timestamp provenance remains explicitly secondary.

---

# 8. Final classification

**V03: COMPLETE**

## Supported for project use

- AI as research and decision-support infrastructure;
- human/independent verification of consequential AI outputs;
- explicit separation between advice/support and delegated authority;
- scenario-generation as a useful AI role;
- proactive safeguards against misuse;
- user-goal/risk alignment;
- staged expansion of agent permissions.

## Unresolved

- a quantitative threshold at which an AI system should receive trading authority;
- a universal measure of "fiduciary AI";
- whether future LLMs can safely perform autonomous portfolio decisions;
- how much human review is optimal at each later execution stage.

Those require separate technical, statistical, operational, and legal work.

## Not supported by V03

- trading alpha;
- strategy profitability;
- autonomous trading authorization;
- self-modifying live strategies;
- bypassing existing project gates.

---

# 9. Playbook status after V03

The named research/source packages are now:

- R01 — COMPLETE
- R02 — COMPLETE
- R03 — COMPLETE
- R04 — COMPLETE
- R05 — COMPLETE
- D01-D03 — COMPLETE FOR INITIAL FEASIBILITY
- Oxford Analytica intake — COMPLETE AS GOVERNANCE/SCENARIO FRAMEWORK
- V01 — COMPLETE
- V02 — COMPLETE
- V03 — COMPLETE

The next playbook maintenance step is to reconcile these completion states into the master playbook and preserve unresolved gaps without silently marking them solved.
