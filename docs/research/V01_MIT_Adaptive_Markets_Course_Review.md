# V01 — MIT Adaptive Markets Course Review

**Project:** AI Crypto Trading Command Center  
**Playbook item:** V01  
**Source:** MIT 15.481x — *Adaptive Markets: Financial Market Dynamics and Human Behavior*  
**Instructor:** Andrew W. Lo  
**Institution:** MIT Sloan School of Management / MIT Open Learning Library  
**Course year created:** 2022  
**Review date:** 2026-09-20  
**Status:** COMPLETE FOR THE PLAYBOOK EXTRACTION OBJECTIVE

## Decision memo

**V01 supports the project's existing Adaptive Markets research direction, but it does not validate a crypto trading strategy or justify adaptive parameter fitting after results are observed.**

The strongest course-consistent project implications are:

1. market efficiency should be treated as **context-dependent and dynamic**, not as permanently present or permanently absent;
2. participants learn, adapt, compete, enter, and exit, so the population producing market prices can change;
3. risk/reward relations can change through time;
4. investment strategies may perform well in some environments and poorly in others;
5. measured predictability should therefore be studied prospectively across predeclared environments, while guarding against data snooping and microstructure artifacts;
6. a strategy's historical success is not evidence that its edge is permanent.

These points already overlap substantially with `docs/ANDREW_LO_RESEARCH_INTEGRATION.md` on the repository's `adaptive-markets-research` branch. V01 therefore functions primarily as **source verification and evidence extraction**, not as a new architecture proposal.

No repository file, release gate, frozen statistical specification, or protected dataset was modified or accessed by this review.

---

# 1. Source availability and review method

## Course

Primary course pages:

- MIT OpenCourseWare course page:  
  https://ocw.mit.edu/courses/15-481x-adaptive-markets-financial-market-dynamics-and-human-behavior-fall-2022/
- MIT Open Learning Library course:  
  https://openlearninglibrary.mit.edu/courses/course-v1:MITx+15.481x+1T2021/course/
- Course syllabus/course schedule:  
  https://openlearninglibrary.mit.edu/courses/course-v1:MITx+15.481x+1T2021/courseware/9c7ec9ae47ac4e27bba545060018364d/a52c027f8bf947c6a6c3c6c07a3dc3f6/

The archived course contains eleven substantive units, including:

- Unit 1 — Introduction and Financial Orthodoxy
- Unit 2 — Rejecting the Random Walk and Efficient Markets
- Unit 3 — Psychology and Behavioral Biases
- Unit 4 — Neuroscience and Decision-Making
- Unit 5 — Evolution and the Origin of Behavior
- Unit 6 — The Adaptive Markets Hypothesis
- Unit 7 — Hedge Funds: The Galapagos Islands of Finance
- Unit 8 — Applications of Adaptive Markets
- Unit 9 — The Financial Crisis
- Unit 10 — Ethics and Adaptive Markets
- Unit 11 — The Future of Finance and the Finance of the Future

## Transcript/timestamp limitation

The Open Learning Library exposes searchable English transcripts for multiple lecture segments and gives video durations in page metadata.

However, the publicly indexed transcript rendering used in this review does **not expose trustworthy per-line time codes**.

Therefore:

- exact transcript wording was reviewed where accessible;
- course segment titles and transcript line locators are recorded;
- slide numbers are recorded where applicable;
- `timestamp_range` is marked `UNAVAILABLE_IN_ACCESSIBLE_TRANSCRIPT_RENDERING`;
- no timestamps were estimated or invented.

This follows the playbook rule that missing timestamps must remain explicit.

---

# 2. Repository deduplication

Existing repository source:

`docs/ANDREW_LO_RESEARCH_INTEGRATION.md`  
Branch: `adaptive-markets-research`

That document already maps Lo's published work to:

- time-varying efficiency/predictability;
- variance-ratio/random-walk diagnostics;
- systematic technical-pattern testing;
- data-snooping controls;
- nonsynchronous trading/microstructure;
- serial-correlation-aware risk measurement;
- predictability that changes by asset, horizon, and environment.

V01 does **not** replace that document.

### V01's contribution

- verifies that the MIT course is consistent with the repository's current AMH framing;
- extracts specific lecture/course claims;
- ties them to Lo's primary publications;
- distinguishes conceptual/evidence status;
- identifies what is useful for future crypto research and what is not authorized.

---

# 3. Evidence cards

## V01-C01 — Efficiency is not simply "true" or "false"

```yaml
claim_id: V01-C01
source_id: MIT-15.481x-U1
source_version: archived course / created 2022
review_status: reviewed
reviewed_at: 2026-09-20
source_locator:
  lecture: "A Taste of Adaptive Markets"
  segment: "Introduction: Efficient Markets and Human Irrationality"
  transcript_locator: "definition/discussion of efficiency; indexed transcript lines 20-38 and 62-80"
  timestamp_range: UNAVAILABLE_IN_ACCESSIBLE_TRANSCRIPT_RENDERING
claim_paraphrase: >
  The course begins with the standard efficient-market idea that available
  information is reflected in prices, then immediately frames efficiency as
  potentially varying by market conditions rather than as a binary universal state.
evidence_type: lecture explanation
market_and_sample: conceptual; no crypto sample
data_requirements: []
method_and_assumptions:
  - distinction between idealized EMH and observed human/market behavior
reported_effect_and_uncertainty: not a quantitative effect estimate
limitations_and_contradictions:
  - lecture framing is not an empirical test
  - does not imply active trading is profitable
replication_assets: []
proposed_project_application: >
  Continue treating efficiency/predictability as an empirical question that may
  vary by asset, horizon, and environment.
existing_repo_overlap:
  - docs/ANDREW_LO_RESEARCH_INTEGRATION.md
causal_timing_requirements: []
cost_and_execution_requirements: []
falsification_or_rejection_condition: >
  Any proposed state-dependent predictability claim must fail if the preregistered
  empirical test does not show it under valid inference.
next_action: none; conceptual mapping already present
decision: retain
decision_reason: course corroborates existing project framing
```

### Primary research cross-reference

Lo (2004), *The Adaptive Markets Hypothesis: Market Efficiency from an Evolutionary Perspective*.

The paper explicitly describes market efficiency as dependent on environmental conditions and the number/nature of participant populations rather than something evaluable in a vacuum.

Primary source:
https://www.mit.edu/~alo/Papers/JPM2004.pdf

---

## V01-C02 — The AMH is built around adaptation and competition

```yaml
claim_id: V01-C02
source_id: MIT-15.481x-U1-U6-U7
source_version: archived course / slides copyright 2020 / course created 2022
review_status: reviewed
reviewed_at: 2026-09-20
source_locator:
  slide: "Unit 1 Part 1, Slide 13; repeated in Unit 7 Part 1, Slide 14"
  timestamp_range: UNAVAILABLE_IN_ACCESSIBLE_TRANSCRIPT_RENDERING
claim_paraphrase: >
  The course summarizes AMH using five ideas: self-interested participants,
  mistakes/satisficing, learning and adaptation through heuristics, competition
  driving adaptation/innovation, and evolution determining market dynamics.
evidence_type: conceptual framework / lecture summary
market_and_sample: conceptual
data_requirements: []
method_and_assumptions:
  - evolutionary analogy applied to financial interactions
reported_effect_and_uncertainty: qualitative framework, not a quantitative estimate
limitations_and_contradictions:
  - these principles do not uniquely identify a forecastable trading signal
  - "evolution" is a framework, not a license for unconstrained regime fitting
replication_assets: []
proposed_project_application: >
  Treat strategy populations, participant composition, and market structure as
  potentially changing; require any resulting state variable to be observable
  and prospectively specified.
existing_repo_overlap:
  - docs/ANDREW_LO_RESEARCH_INTEGRATION.md
causal_timing_requirements:
  - any ecology variable must be known at decision time
cost_and_execution_requirements: []
falsification_or_rejection_condition: >
  Reject any mechanism-specific hypothesis that fails preregistered empirical testing.
next_action: none at framework level
decision: retain
decision_reason: directly aligned with existing Adaptive Markets phase
```

Course slide source:
https://openlearninglibrary.mit.edu/assets/courseware/v1/d207dd3dbf4f2b49b4efba0184a81545/asset-v1%3AMITx%2B15.481x%2B1T2021%2Btype%40asset%2Bblock/Unit_1_Part_1.pdf

---

## V01-C03 — Adaptability is treated as a form of functional intelligence

```yaml
claim_id: V01-C03
source_id: MIT-15.481x-U6
source_version: archived course
review_status: reviewed
reviewed_at: 2026-09-20
source_locator:
  lecture: "The Adaptive Markets Hypothesis"
  segment: "Towards an Evolutionary Definition of Intelligence"
  transcript_locator: "indexed transcript around lines 52-62 and 150-155"
  video_duration_seconds: 1517.082
  timestamp_range: UNAVAILABLE_IN_ACCESSIBLE_TRANSCRIPT_RENDERING
claim_paraphrase: >
  The lecture links intelligence to adaptability and ultimately defines useful
  behavior in evolutionary terms: behavior is intelligent when it confers a
  survival advantage.
evidence_type: conceptual lecture claim
market_and_sample: conceptual
data_requirements: []
method_and_assumptions:
  - evolutionary definition of adaptive behavior
reported_effect_and_uncertainty: no quantitative market estimate
limitations_and_contradictions:
  - survival analogy does not imply maximizing short-run P&L
  - not a direct statistical proposition about BTC/ETH
replication_assets: []
proposed_project_application: >
  Maintain explicit retirement/suspension rules for any future validated edge;
  do not assume a once-profitable strategy remains valid indefinitely.
existing_repo_overlap:
  - edge-lifecycle language in docs/ANDREW_LO_RESEARCH_INTEGRATION.md
causal_timing_requirements: []
cost_and_execution_requirements:
  - future lifecycle monitoring must include costs and drawdown
falsification_or_rejection_condition: >
  A future live/paper strategy must be suspended under prospectively defined
  deterioration rules rather than protected by narrative explanations.
next_action: carry into future edge-monitoring design only after a strategy qualifies
decision: retain_as_governance_principle
decision_reason: useful for lifecycle control, not signal generation
```

Course transcript source:
https://openlearninglibrary.mit.edu/courses/course-v1%3AMITx%2B15.481x%2B1T2021/jump_to/block-v1%3AMITx%2B15.481x%2B1T2021%2Btype%40sequential%2Bblock%40dab69fdc9c21481fa15cbe32ced363a5

---

## V01-C04 — Market ecology makes efficiency context-dependent

```yaml
claim_id: V01-C04
source_id: LO-2004-AMH
source_version: 2004 author PDF
review_status: reviewed
reviewed_at: 2026-09-20
source_locator:
  paper: "Lo (2004), AMH"
  pages: "18-20 in author manuscript; market ecology discussion"
  timestamp_range: not_applicable
claim_paraphrase: >
  Market efficiency depends on environmental conditions and on the number and
  nature of competing participant populations. Profit opportunities and
  participant populations can change together.
evidence_type: theoretical/conceptual framework with market examples
market_and_sample: broad financial markets; examples include Treasuries and relative-value markets
data_requirements: []
method_and_assumptions:
  - bounded rationality/satisficing
  - evolutionary competition and adaptation
reported_effect_and_uncertainty: qualitative; no universal effect size
limitations_and_contradictions:
  - does not establish that any chosen ecology variable forecasts returns
  - participant "species" require operational definitions before empirical use
replication_assets: []
proposed_project_application: >
  Prefer direct market-ecology variables such as liquidity, order flow, funding,
  basis, open interest, liquidations, and access constraints over hindsight regime labels.
existing_repo_overlap:
  - Phase B market ecology plan
  - R02/R03/R04 reviews
  - D01-D03 data qualification
causal_timing_requirements:
  - exact observation and availability times
cost_and_execution_requirements:
  - venue access, costs, liquidity, transfer constraints where applicable
falsification_or_rejection_condition: >
  An ecology variable is rejected as predictive if it adds no preregistered
  incremental information after appropriate controls.
next_action: source-specific preregistration only after data certification
decision: retain
decision_reason: strong conceptual bridge from AMH to project data-expansion program
```

Primary source:
https://www.mit.edu/~alo/Papers/JPM2004.pdf

---

## V01-C05 — Risk/reward relationships can be time-varying

```yaml
claim_id: V01-C05
source_id: MIT-15.481x-U7 / LO-2004-AMH
source_version: archived course plus 2004 paper
review_status: reviewed
reviewed_at: 2026-09-20
source_locator:
  course_segment: "Time-Varying Risk-Reward Tradeoff"
  course_unit: "Unit 7 — Implication for the Current Financial Landscape"
  course_video_duration_seconds: 957.589
  course_slide: "Unit 7 Part 3, Slide 27"
  paper_pages: "21-24 in author manuscript, Practical Implications"
  timestamp_range: UNAVAILABLE_IN_ACCESSIBLE_TRANSCRIPT_RENDERING
claim_paraphrase: >
  The course and paper argue that the relation between risk and expected reward
  need not be stable over time because participant composition, preferences,
  institutions, regulation, and market conditions change.
evidence_type: AMH implication
market_and_sample: conceptual; historical market illustrations
data_requirements:
  - time-indexed risk measures
  - observable environment/state variables for any empirical test
method_and_assumptions:
  - market ecology changes through time
reported_effect_and_uncertainty: no fixed universal coefficient
limitations_and_contradictions:
  - time variation must be demonstrated, not assumed
  - flexible state definitions can create severe overfitting
replication_assets:
  - BTC
  - ETH
proposed_project_application: >
  Test state-dependent relationships only through predeclared state definitions
  and calibrated inference; do not use ex-post "bull/bear/crisis" labels.
existing_repo_overlap:
  - AMS-DEP state interactions
  - R05 selection-bias safeguards
  - Oxford scenario anti-hindsight rules
causal_timing_requirements:
  - state must be observable before target return
cost_and_execution_requirements: []
falsification_or_rejection_condition: >
  No state-dependence claim if interactions fail the frozen inferential gate or
  are unstable under preregistered robustness checks.
next_action: none until current inferential gates permit empirical use
decision: retain
decision_reason: directly relevant but already governed by existing protocol
```

Course source:
https://openlearninglibrary.mit.edu/courses/course-v1%3AMITx%2B15.481x%2B1T2021/jump_to/block-v1%3AMITx%2B15.481x%2B1T2021%2Btype%40sequential%2Bblock%4053c7e5763c6d4c93badcfe296b297ceb

Primary paper:
https://www.mit.edu/~alo/Papers/JPM2004.pdf

---

## V01-C06 — Strategies can wax and wane

```yaml
claim_id: V01-C06
source_id: LO-2004-AMH / MIT-15.481x
source_version: 2004 paper; archived 2022 course
review_status: reviewed
reviewed_at: 2026-09-20
source_locator:
  paper_pages: "22-23 in author manuscript, Practical Implications"
  course_context: "Units 6-8"
  timestamp_range: UNAVAILABLE_IN_ACCESSIBLE_TRANSCRIPT_RENDERING
claim_paraphrase: >
  AMH predicts that investment strategies may perform well in one environment,
  deteriorate as competition and conditions change, and potentially become useful
  again under different future conditions.
evidence_type: theoretical implication supported by historical examples
market_and_sample: broad financial markets; Lo discusses relative-value/risk-arbitrage examples
data_requirements:
  - strategy returns through time
  - predeclared environment variables
  - participant/liquidity proxies where justified
method_and_assumptions:
  - changing market ecology
  - changing opportunity set
reported_effect_and_uncertainty: no universal cycle length or return magnitude
limitations_and_contradictions:
  - "wax and wane" does not justify reviving a failed strategy after inspecting results
  - recurrence must be prospectively demonstrated
  - no automatic transfer from equities/hedge funds to crypto
replication_assets:
  - future BTC/ETH candidates only after separate preregistration
proposed_project_application: >
  If a strategy eventually reaches paper/live stages, use frozen monitoring and
  retirement/reactivation rules. During research, a failed strategy remains failed
  unless a materially new mechanism is preregistered under a new version/ID.
existing_repo_overlap:
  - closed HYP-0001 through HYP-0025 policy
  - edge-lifecycle proposal in Andrew Lo integration
causal_timing_requirements:
  - environment state known before strategy decision
cost_and_execution_requirements:
  - monitor net performance after realistic costs
falsification_or_rejection_condition: >
  Do not revive a failed candidate because a later window looks favorable unless
  the new test was prospectively specified and protected from prior outcome selection.
next_action: retain as future lifecycle principle
decision: retain_with_strict_anti_snooping_boundary
decision_reason: concept is useful but especially vulnerable to hindsight abuse
```

Primary paper finding:
Lo states that investment strategies may "wax and wane," performing differently as environmental conditions change.

---

## V01-C07 — Random-walk rejection is a diagnostic, not a strategy

```yaml
claim_id: V01-C07
source_id: MIT-15.481x-U2 / LO-MACKINLAY
source_version: archived course plus primary research
review_status: reviewed
reviewed_at: 2026-09-20
source_locator:
  course_unit: "Unit 2 — Rejecting the Random Walk and Efficient Markets"
  lectures:
    - "The Random Walk Hypothesis"
    - "Contemporary Tests of the Random Walk"
    - "Tutorial: Random Walks and Variance Ratio Tests"
  course_slide: "Unit 2 Part 2, Variance Ratio Test"
  timestamp_range: UNAVAILABLE_IN_ACCESSIBLE_TRANSCRIPT_RENDERING
claim_paraphrase: >
  Random-walk/variance-ratio tests ask whether returns exhibit statistical
  departures from a random-walk benchmark. A rejection establishes a property
  of the return process, not an executable profitable strategy.
evidence_type: econometric test framework
market_and_sample: original research primarily U.S. equities
data_requirements:
  - returns at prospectively fixed horizons
method_and_assumptions:
  - variance-ratio test assumptions and finite-sample behavior
reported_effect_and_uncertainty: source-specific; not imported into crypto
limitations_and_contradictions:
  - statistical dependence can arise from microstructure
  - rejection does not identify mechanism or direction
  - significance can be miscalibrated in finite samples
replication_assets:
  - BTC
  - ETH
proposed_project_application: >
  Keep measurable dependence separate from strategy design, exactly as the
  current AMS-DEP architecture does.
existing_repo_overlap:
  - AMS-DEP
  - finite-sample synthetic calibration requirement
causal_timing_requirements:
  - lagged inputs only
cost_and_execution_requirements:
  - none for dependence measurement; mandatory before economic translation
falsification_or_rejection_condition: >
  Do not progress to mechanism/strategy research if calibrated dependence is not
  established or if it is explainable by data/microstructure artifacts.
next_action: current AMS-DEP gates govern
decision: retain
decision_reason: validates separation between dependence testing and strategy P&L
```

Course slide:
https://openlearninglibrary.mit.edu/assets/courseware/v1/dd3a2189f43d7d29718722b2f12acd1e/asset-v1%3AMITx%2B15.481x%2B1T2021%2Btype%40asset%2Bblock/Unit_2_Part_2.pdf

Primary research:
- Lo and MacKinlay (1988), *Stock Market Prices Do Not Follow Random Walks: Evidence From a Simple Specification Test*
- Lo and MacKinlay (1989), *The Size and Power of the Variance Ratio Test in Finite Samples: A Monte Carlo Investigation*

---

# 4. What V01 changes for this project

## Nothing should be loosened

V01 provides **no basis** to:

- reopen HYP-0001–HYP-0025;
- redefine failed strategies as merely "out of regime";
- search many regime definitions and retain favorable ones;
- inspect Validation/OOS;
- lower significance/robustness thresholds;
- treat market-state dependence as proof of AMH;
- infer a trading signal directly from a lecture;
- authorize paper or live trading.

## What V01 reinforces

### A. Market ecology should be measured with direct variables where possible

Potential variables already identified elsewhere in the playbook:

- order flow / top-of-book liquidity;
- spreads and cross-venue fragmentation;
- dated futures basis;
- perpetual funding as a separate quantity;
- open interest;
- liquidations;
- network/on-chain variables after point-in-time certification;
- macro variables after vintage/release-time certification;
- regulatory/market-access events.

### B. State definitions must be prospective

A state is scientifically useful only if:

- observable at the decision timestamp;
- fixed before outcomes;
- economically interpretable;
- not chosen because it produces favorable returns.

### C. Strategy lifecycle belongs after validation, not before

The "wax and wane" implication matters most if the project eventually has a strategy that survives:

`Development -> robustness -> Validation -> locked OOS -> paper`

Only then should lifecycle monitoring determine whether an approved edge is degrading.

It is **not** a rescue mechanism for failed Development research.

---

# 5. Cross-reference to R02–R05

## R02 — Order flow

AMH motivates asking whether predictability changes with participant/liquidity conditions. R02 provides a direct microstructure route for measuring such conditions rather than relying only on candles.

## R03 — Fragmentation

Different venue populations, access constraints, currencies, and arbitrage frictions are concrete examples of different market ecologies.

## R04 — Carry

Futures basis can be treated as a positioning/arbitrage-capital state variable in a separately preregistered study, but the lecture does not establish its predictive effect.

## R05 — Overfitting

This is the most important protection against abusing AMH. A flexible "markets adapt" narrative can explain almost any historical outcome after the fact. Therefore all proposed state variables, interactions, windows, and strategy reactivation rules must enter the global search ledger.

---

# 6. Course versus paper evidence hierarchy

For this project:

1. **Primary published research / technical paper** — strongest source for a specific empirical or theoretical claim.
2. **MIT course lecture/slides** — useful explanation, framing, and source discovery.
3. **Interview/podcast** — useful for interpretation but not strategy validation.

The course should never be cited as if it independently establishes an empirical effect that is only demonstrated in a separate paper.

---

# 7. Unresolved items

### U1 — Exact video timestamps

The accessible transcript renderer did not expose reliable per-line timestamps.

**Status:** unresolved; not fabricated.

If a future tool exposes the official caption cue file with timing, update the evidence cards with exact ranges without changing the claim text.

### U2 — Crypto transfer

Lo's original examples are primarily equities, hedge funds, fixed income, and broad financial markets.

**Status:** no automatic transfer to BTC/ETH.

Every crypto application remains a separate empirical hypothesis.

### U3 — Operational definition of "market ecology"

The AMH concept is broad.

**Status:** source-specific variable definitions are required.

R02–R04 and D01–D03 are the bounded path toward operationalization.

---

# 8. Final V01 classification

**V01: COMPLETE**

**Supported for project use:**

- dynamic/context-dependent efficiency as a research hypothesis;
- time-varying predictability as an empirical question;
- participant/environment changes as possible mechanisms;
- prospective state-dependent testing;
- lifecycle monitoring for future validated strategies;
- separation of dependence from tradability.

**Not supported by V01 alone:**

- any profitable BTC/ETH strategy;
- any specific regime threshold;
- any specific adaptive parameter algorithm;
- strategy resurrection after failure;
- discretionary switching;
- Validation/OOS access;
- paper/live trading.

## Next playbook video

**V02 — LSE / Igor Makarov, "Demystifying Cryptocurrency"**

Objective:

- extract the video's explanations of cryptocurrency market structure;
- cross-reference them against R03;
- preserve timestamps where the source exposes them;
- distinguish educational explanation from the Makarov–Schoar published evidence.
