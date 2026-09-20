# AI Crypto Trading Command Center — Research Playbook

Version: 1.2 | Prepared: 2026-09-20 | Source-review queue completed: 2026-09-20

## Purpose and authority

Turn the research shortlist from this conversation into an actionable reference for future assistants working on the Investing project. Use it to select sources, extract evidence, assess applicability, and propose bounded research tasks.

This is a research intake plan, not a completed literature review, trading recommendation, validated strategy, or approved change to the statistical protocol. No repository files, release gates, or workflows were changed in preparing this document. The repository was not inspected for this deliverable.

Repository: https://github.com/jcbones01-glitch/ai-crypto-trading-command-center


## Work-package completion status — 2026-09-20

The named source-review queue in this playbook has now been completed. Completion means that the required literature/data/video review was performed and a companion report was produced; it does **not** mean every proposed empirical use is validated or authorized.

| Package | Status | Companion artifact | Important unresolved boundary |
| --- | --- | --- | --- |
| R01 — Dependent wild bootstrap applicability | **COMPLETE — applicability reviewed** | `R01_Bootstrap_Applicability_Review.md` | Exact-method validity remains unresolved beyond the frozen synthetic evidence; no theorem was stretched to certify the project design |
| R02 — Order flow and liquidity | **COMPLETE — replication/data feasibility reviewed** | `R02_Order_Flow_Replication_and_Data_Feasibility_Review.md` | Contemporaneous OFI is not future-return prediction; exact predictive usefulness remains unresolved |
| R03 — Exchange fragmentation | **COMPLETE — market-fragmentation review** | `R03_Exchange_Fragmentation_Review.md` | Current executable arbitrage remains unproven until synchronized access/cost/depth/transfer data are qualified |
| R04 — Crypto carry and market stress | **COMPLETE — data dictionary/preregistration concept** | `R04_Crypto_Carry_and_Market_Stress_Review.md` | Current incremental predictive value of dated basis remains unresolved |
| R05 — Selection/backtest overfitting | **COMPLETE — experiment-accounting gap review** | `R05_Selection_and_Backtest_Overfitting_Review.md` | Global search/exposure ledger and formal selection-inference compatibility study are not yet implemented |
| D01–D03 — Data-source feasibility | **COMPLETE FOR INITIAL QUALIFICATION** | `D01_D03_Data_Source_Feasibility_Review.md` | Point-in-time, entitlement, licensing, exact coverage, cost, and storage questions remain source-specific |
| Oxford Analytica intake | **COMPLETE AS GOVERNANCE/SCENARIO FRAMEWORK** | `Oxford_Analytica_Intake_Geopolitical_Scenario_Framework.md` | No proprietary Oxford Analytica report was reviewed; no geopolitical alpha claim established |
| V01 — MIT Adaptive Markets | **COMPLETE** | `V01_MIT_Adaptive_Markets_Course_Review.md` | No crypto strategy is validated by the course; some exact video timing remained unavailable |
| V02 — LSE Demystifying Cryptocurrency | **COMPLETE FOR ACCESSIBLE SOURCE EXTRACTION** | `V02_LSE_Demystifying_Cryptocurrency_Review.md` | Exact playbook-video captions/timestamps were unavailable; primary-paper evidence remains controlling |
| V03 — MIT Finance, AI, and Human Behavior | **COMPLETE** | `V03_MIT_Finance_AI_and_Human_Behavior_Review.md` | Source supports decision support/human oversight, not autonomous-trading authorization |

### Current playbook boundary

The **source-review queue is complete**. The next phase is not another literature/video item from this playbook. It is a separate project-integration phase that should begin only under current repository authority and user instruction.

When integration begins:

1. Re-inspect the current repository, branch/head, open PRs/issues/workflows, and machine release gates.
2. Do not assume the repository state recorded in any companion review is still current.
3. Deduplicate proposed governance/data artifacts against the repository before creating anything.
4. Preserve every unresolved qualification above.
5. Do not convert literature support into empirical authorization.
6. Do not access protected Validation/OOS or market results unless the current machine/research gate explicitly authorizes it.
7. Do not expand paper/live trading authority without a separately approved execution phase.


Conversation context indicates that the OHLCV-only Gate 2 program is closed and that AMS-DEP V2 synthetic calibration is the immediate methodological focus. Treat these as context to verify, not a statement of current repository status. Inspect the current repository, applicable instructions, release gate, and active protocol before any implementation. Repository evidence determines implementation state; current user instructions determine authorization.

## Instructions for the next assistant

1. Read this playbook and establish which task the user has requested: literature review, data feasibility, proposed protocol, or implementation.
2. Before project integration, inspect the current repository and deduplicate these sources against its bibliography and completed work. Verify the relevant branch and full head SHA. The historically relevant branch was `adaptive-markets-research`; do not assume it remains current.
3. If present, start methodological context with `docs/AMS_DEP_V2_RATIFICATION_PACKET.md` and follow its required reading. Do not access embargoed results as part of orientation.
4. The R01–R05, D01–D03, Oxford-intake, and V01–V03 review packages are complete; read their companion artifacts instead of repeating them.
5. Treat unresolved gaps in those companion artifacts as still unresolved. Completion of a review does not authorize an experiment, dataset, release-gate change, or trading action.
6. Report source evidence separately from your proposed application. Use exact page, section, theorem, table, or video timestamps after actually inspecting them.
7. Retain failures, incompatible assumptions, inaccessible sources, and negative evidence. Do not silently replace a failed idea with a better-looking variant.

### Persistent project constraints from the conversation

- Preserve the closed Gate 2 findings. Do not rescue failed hypotheses by retuning them.
- Preserve Validation/OOS embargoes and any restrictions on actual BTC/ETH AMS-DEP results.
- Do not weaken thresholds, change frozen calibration rules, or select methods based on desirable market outcomes.
- No live trading authorization; retain the project's spot-only, no-leverage scope unless explicitly changed.
- A derivatives data source can inform a spot-market research question without authorizing derivatives execution.
- Maintain causal timing, realistic costs, deterministic reproducibility, and a complete experiment ledger.
- Literature review can proceed alongside calibration; changes affecting calibration require the existing protocol's review/version process.

## Evidence status

The initial playbook was created from discovery-level source checks. Since then, the named R01–R05, D01–D03, Oxford-intake, and V01–V03 packages have been reviewed and documented in companion artifacts. Those reviews remain bounded: they do not constitute exhaustive replication, universal theorem certification, current commercial-data entitlement, strategy validation, or trading authorization.

Use these states: `candidate → full-text reviewed → applicability assessed → protocol proposed → approved for specified experiment → evaluated → retained/rejected`.

A source's academic reputation does not advance its status. A published result is not evidence that its effect exists in our dataset, survives execution costs, or remains available today. Mark unreported details as unknown.

## Prioritized source register

### R01 — Bootstrap validity: first priority

**Source:** Xiaofeng Shao, *The Dependent Wild Bootstrap*, Journal of the American Statistical Association, 105(489), 218–235 (2010).

**DOI:** https://doi.org/10.1198/jasa.2009.tm08744

**Institutional record:** https://experts.illinois.edu/en/publications/the-dependent-wild-bootstrap/

**Evidence already identified:** The paper develops dependent wild bootstrap methods for stationary time series, with results for a smooth-function framework and specified irregular-sampling settings. Institutional abstract and bibliographic information reviewed; detailed theorem applicability remains unverified.

**Project question:** Which results, if any, justify our exact statistic, regressors, multiplier process, bandwidth choices, null construction, and sampling structure?

**Required extraction:** theorem assumptions; dependence and moment conditions; stationarity scope; centering; tuning conditions; studentization; finite-sample evidence; treatment of estimated quantities. Explicitly distinguish what the paper proves from any extension we would need.

**Deliverable:** assumption-to-implementation matrix, linked to exact code and contract locations after repository inspection; inventory of existing synthetic checks; gap proposals.

**Do not advance if:** applicability rests only on the method's name, required assumptions are unverified, or the desired extension lacks justification. Synthetic calibration is necessary evidence but does not supply a missing theorem by itself.

### R02 — Order flow and liquidity: second priority

**Source:** Rama Cont, Arseniy Kukanov, Sasha Stoikov, *The Price Impact of Order Book Events*, Journal of Financial Econometrics, 12(1), 47–88 (2014).

**Paper:** https://arxiv.org/abs/1011.6402

**DOI:** https://doi.org/10.1093/jjfinec/nbt003

**Evidence already identified:** The abstract reports a relationship between order-flow imbalance, market depth, and short-interval price changes using 50 US stocks. Abstract and publication metadata reviewed.

**Proposed application:** Assess whether adequately recorded crypto order-book events permit comparable descriptive analysis, followed only later by an independently specified predictive test.

**Required data:** time-stamped quote updates, additions/cancellations where available, trades, depth, sequence identifiers, venue rules, and outage records. Determine exactly which observations the paper's definitions require.

**Critical distinction:** Explaining a price change over the same interval does not demonstrate prediction of a subsequent return. Signal availability and execution time must be explicit.

**Deliverable:** replication specification and data feasibility assessment; no claim that equity findings transfer to crypto.

**Do not advance if:** event ordering cannot be reconstructed, data omit essential events, timing leaks future information, or costs make the proposed application infeasible.

### R03 — Exchange fragmentation

**Source:** Igor Makarov and Antoinette Schoar, *Trading and Arbitrage in Cryptocurrency Markets*, Journal of Financial Economics, 135(2), 293–319 (2020).

**Journal:** https://www.sciencedirect.com/science/article/pii/S0304405X19301746

**DOI:** https://doi.org/10.1016/j.jfineco.2019.07.001

**Evidence already identified:** Discovery results and author-uploaded abstract describe recurring exchange price differences and barriers associated with capital movement. Direct full-text retrieval was not completed.

**Proposed application:** Identify exchange-specific effects, inaccessible prices, currency differences, and transfer constraints that could make an apparent signal misleading.

**Required extraction:** sample dates, venues, price synchronization, currency conversion, fees, transfer/withdrawal constraints, and limits to execution.

**Deliverable:** market fragmentation checklist and a bounded diagnostic proposal, subject to current data permissions.

**Do not advance if:** apparent discrepancies depend on stale quotes, inaccessible venues, omitted costs, or impossible transfers.

### R04 — Crypto carry and market stress: third priority

**Source:** Maik Schmeling, Andreas Schrimpf, Karamfil Todorov, *Crypto Carry*, BIS Working Paper 1087 (2023).

**Source page:** https://www.bis.org/publ/work1087.htm

**Evidence already identified:** The BIS summary connects futures–spot differences with speculative demand, limited arbitrage capital, and crash risk. Summary reviewed; full empirical specification and replication materials remain to be assessed.

**Proposed application:** Evaluate whether lagged futures basis provides incremental information about spot-market stress. This is an untested project proposal.

**Required extraction:** futures maturity and annualization conventions, contracts and venues, sample coverage, crash definition, controls, timing, and robustness results.

**Data distinction:** Dated-futures basis and perpetual funding are different quantities. Do not substitute one for the other without a separate rationale and specification.

**Deliverable:** data dictionary and preregistration proposal, including a simple baseline and conditions for rejecting incremental predictive usefulness.

**Do not advance if:** information was unavailable at the decision time, the effect depends on retrospective event selection, or it disappears under the approved robustness assessment.

### R05 — Selection and backtest overfitting

**Source:** David H. Bailey, Jonathan M. Borwein, Marcos López de Prado, Qiji Jim Zhu, *The Probability of Backtest Overfitting*.

**Author-hosted manuscript:** https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf

**Version observed:** February 2015 manuscript; do not confuse manuscript date with final journal publication date.

**Evidence already identified:** Abstract and introductory text discuss repeated strategy selection and propose a probability-of-overfitting framework using combinatorially symmetric cross-validation.

**Proposed application:** Audit whether the project records the full search history and accounts for strategy selection. First check whether equivalent controls already exist.

**Deliverable:** gap assessment for experiment accounting and selection inference.

**Limit:** Do not automatically replace chronological evaluation or existing protected holdouts with this procedure. Assess dependence, overlapping observations, selection history, and method compatibility first.

## Data-source feasibility register

| ID | Source | Candidate use | Required checks before adoption |
| --- | --- | --- | --- |
| D01 | [Federal Reserve ALFRED](https://fred.stlouisfed.org/docs/api/fred/alfred.html) | Economic series as originally released and revised | Vintage availability; actual release timestamps; time zones; revisions; source coverage. Vintage dates alone may be insufficient for intraday alignment. |
| D02 | [Coin Metrics community repository](https://github.com/coinmetrics/data) | Network activity and supply-related measures | Available assets/metrics; definitions; point-in-time availability; retrospective recalculation; missingness; licensing. No claim of complete free coverage. |
| D03 | [Coin Metrics market-data documentation](https://docs.coinmetrics.io/market-data/market-data-overview) | Trades, quotes, order books, and derivatives information | Exact product entitlement, historical depth, granularity, venues, cost, storage burden, and permitted use. Documentation is not proof of accessible data. |

For every adopted dataset, record provider, endpoint/product, retrieval time, observation time, publication/availability time, revision policy, schema, units, asset and venue identifiers, coverage, license, missing-data rules, immutable snapshot hash, and cost. Never fill historical gaps silently.

## Oxford Analytica intake

**Discovery reference:** https://foundation.oxan.com/

**Access status:** The previous search could not retrieve the main Oxford Analytica service. No current proprietary Daily Brief report was reviewed. The foundation page describes its geopolitical research/advisory focus; it is not a substitute for specific reports.

**Potential use:** Develop scenarios about regulatory change, capital controls, sanctions, or interruptions to market access. These are proposed uses, not findings attributed to a report.

For any accessible report, record title, author if stated, publication time, jurisdiction, forecast horizon, exact claim, supporting evidence, uncertainty, observable mechanism, and relevant primary official sources. Respect access and licensing restrictions.

Keep geopolitical scenario analysis separate from statistically demonstrated return predictability. Avoid retrospective labels such as “obvious crisis” constructed after seeing returns. An instruction to act as Oxford Analytica confers neither affiliation nor proprietary access.

## Video queue

| ID | Source | Extraction objective | Current status |
| --- | --- | --- | --- |
| V01 | [MIT: Adaptive Markets course, Andrew Lo](https://ocw.mit.edu/courses/15-481x-adaptive-markets-financial-market-dynamics-and-human-behavior-fall-2022/) | Identify concrete claims about adaptation and efficiency; connect each to original research | **COMPLETE** — see `V01_MIT_Adaptive_Markets_Course_Review.md` |
| V02 | [LSE: Demystifying Cryptocurrency, Igor Makarov](https://www.youtube.com/watch?v=CkS9l65ILQI) | Extract research explanations concerning cryptocurrency market structure; cross-reference R03 | **COMPLETE FOR ACCESSIBLE SOURCE EXTRACTION** — see `V02_LSE_Demystifying_Cryptocurrency_Review.md` |
| V03 | [MIT: Finance, AI, and Human Behavior, Andrew Lo](https://www.youtube.com/watch?v=8kFFg5jAoQc) | Extract implications for AI-assisted decision-making and human oversight | **COMPLETE** — see `V03_MIT_Finance_AI_and_Human_Behavior_Review.md` |

For video notes, capture title, channel/institution, speaker, publication date, URL, timestamp range, paraphrased claim, cited paper, evidence type, applicability, and uncertainty. Verify captions against context where necessary. If transcripts are inaccessible, mark the task blocked rather than inventing quotations or timestamps. Educational explanations and interviews are not strategy validation.

## Standard evidence card

Use one card per substantive claim, not just one summary per paper:

```yaml
claim_id: null
source_id: null
source_version: null
review_status: candidate
reviewed_at: null
source_locator: null # page/section/table/theorem or video timestamp
claim_paraphrase: null
evidence_type: null # theorem, empirical result, simulation, expert opinion
market_and_sample: null
data_requirements: []
method_and_assumptions: []
reported_effect_and_uncertainty: null # unknown unless extracted
limitations_and_contradictions: []
replication_assets: []
proposed_project_application: null
existing_repo_overlap: null
causal_timing_requirements: []
cost_and_execution_requirements: []
falsification_or_rejection_condition: null
next_action: null
decision: pending
decision_reason: null
```

## Source-review completion criteria

The playbook's named source-review packages are complete as of 2026-09-20.

Completion means:
- material claims are traceable to inspected sources;
- unknowns and inaccessible material remain explicit;
- companion reports distinguish source evidence from proposed application;
- negative evidence and incompatibilities are retained;
- no profitability, release-readiness, or trading authority is inferred from literature review alone.

The next project phase is integration/implementation planning under the repository's **current** state, not repetition of the completed source reviews.

## Reuse and maintenance

To resume, ask the assistant to read `AI_Trading_Research_Playbook.md` and execute the first incomplete work package within the current project constraints. In a new thread where this file is not available, attach or select it. Saving a document does not guarantee that every future conversation automatically loads it.

Update this document as reviews are completed. Record date, source versions, repository SHA when inspected, decisions, and remaining tasks. Keep it as a research reference; do not treat it as an override of current user instructions or the project's approved protocols.
