# R05 — Selection and Backtest Overfitting: Applicability and Gap Assessment

**Project:** AI Crypto Trading Command Center  
**Review date:** 2026-09-20  
**Playbook source:** `AI_Trading_Research_Playbook(1).md`, R05  
**Repository inspected:** `jcbones01-glitch/ai-crypto-trading-command-center`  
**Default-branch head inspected:** `7aa2da44f19474978854905caff1ea78e05ff540`  
**Closed Gate 2 merge commit:** `06b10145688cd8baca470e4bf0dc5bff8f40702d`  
**Primary R05 source version used for method extraction:** David H. Bailey, Jonathan M. Borwein, Marcos López de Prado, Qiji Jim Zhu, *The Probability of Backtest Overfitting*, author-hosted manuscript, revised February 2015.  
**Final publication metadata checked separately:** *Journal of Computational Finance* 20(4), April 2017, DOI `10.21314/JCF.2016.322`.

---

## 1. Required playbook task

The playbook defines R05 as an audit of whether the project records the full search history and accounts for strategy selection. The deliverable is a **gap assessment for experiment accounting and selection inference**. It explicitly warns not to automatically replace chronological evaluation or protected holdouts with combinatorially symmetric cross-validation (CSCV); dependence, overlapping observations, selection history, and method compatibility must be assessed first.

This review therefore does **not** authorize:

- reopening failed Gate 2 hypotheses;
- accessing Validation or locked OOS;
- retuning parameters;
- calculating new strategy P&L on protected partitions;
- paper trading or live trading;
- replacing the current chronological research protocol with CSCV/PBO;
- selecting a strategy because it produces a low estimated PBO.

---

## 2. Decision summary

### Overall R05 status

**R05 COMPLETE — STRONG PROCEDURAL ANTI-OVERFITTING CONTROLS ALREADY EXIST, BUT PROJECT-WIDE SELECTION ACCOUNTING IS INCOMPLETE AND DIRECT CSCV/PBO COMPATIBILITY IS UNRESOLVED.**

The existing Gate 2 architecture already addresses many of the practical causes of backtest overfitting better than a conventional trading-research workflow:

- immutable Development / Validation / locked-OOS partitions;
- Development-only discovery and model selection;
- prospective preregistration before evidence generation;
- deterministic strategy definitions and execution timing;
- explicit parameter grids;
- mandatory recording of attempted/error cells;
- no post-result parameter additions or removals;
- frozen cost/slippage and timing stress;
- parameter-neighborhood robustness rather than choosing the best cell;
- explicit rejection rules and prohibition on rescuing failed hypotheses with Validation/OOS;
- new hypothesis IDs/versions for materially changed strategies;
- no candidate promoted from the closed OHLCV-only Gate 2 program.

However, those controls are mostly **cycle-local and procedural**. They do not yet constitute a complete project-wide statistical treatment of strategy selection. The principal gaps are:

1. no single immutable, machine-readable **global search ledger** consolidating every evidence-generating strategy trial across cycles;
2. no explicit project-level **selection family / effective trial-count model** that captures the fact that later cycles were chosen after observing earlier Development failures;
3. no formal project-wide implementation of PBO/CSCV, Deflated Sharpe Ratio, White Reality Check, Hansen SPA, false-discovery control, or another registered selection-inference method;
4. no established compatibility mapping from the project’s heterogeneous event-driven strategies to the synchronous `T × N` performance matrix required by the Bailey et al. CSCV implementation;
5. one documented preregistration-count inconsistency in Cycle 2 that should remain visible as an erratum rather than being silently rewritten.

Because Gate 2 ended with **no candidate promoted**, these gaps did not create a currently promoted strategy that now needs to be invalidated. They matter before any future large strategy search is allowed to claim statistically credible selection evidence.

---

## 3. Primary-source findings: what PBO/CSCV actually measures

Bailey et al. define backtest overfitting in the context of **strategy selection**, not merely parameter estimation inside one forecasting model. In their framework, a selection process overfits when the strategy that ranks best in-sample tends to rank below the median of the tested alternatives out-of-sample.

Their probability of backtest overfitting (PBO) is therefore about the reliability of the **selection process among N alternatives**. It is not simply a p-value for one strategy and is not a generic proof that a backtest is valid.

### CSCV implementation

The manuscript’s CSCV implementation starts from a performance matrix `M`:

- rows = `T` synchronous performance observations;
- columns = `N` strategy configurations/trials;
- every column must have the same number of rows;
- each row must refer to synchronous observations across all strategies;
- if strategies trade at different frequencies, performance must be aggregated to a common time index;
- the performance metric must be estimable on subsamples.

The matrix is partitioned into an even number `S` of row blocks. Half-block combinations are used as in-sample sets and their complements as out-of-sample sets. For each combination, CSCV finds the in-sample winner and records that winner’s relative out-of-sample rank. PBO is estimated from the frequency with which the in-sample winner falls below the median of the alternatives out-of-sample.

### What the primary source warns about

The manuscript contains several limits directly relevant to this project:

- CSCV is not one-size-fits-all.
- Strong autocorrelation can make symmetric partitioning inappropriate or distort characterization, especially with large `S`.
- The test is only as good as the **completeness of the actual trial history**. Hidden trials underestimate overfitting.
- Conversely, padding the comparison set with obviously doomed alternatives can bias the assessment in the other direction.
- For guided searches, the paper says the relevant columns should represent the final outcome of each guided search rather than every internal optimizer iteration.
- CSCV does not detect incorrect transaction costs, look-ahead, unavailable data, or other flawed backtest assumptions.
- It only reflects structural breaks represented inside the available dataset; future unseen regimes remain a separate problem.
- A high PBO does not prove that every strategy in the set lacks skill.
- CSCV/PBO should **not be used as an optimization objective to guide the search for a winning strategy**.

These limits are why this R05 review does not recommend replacing the current protected chronological holdouts with CSCV.

---

## 4. Existing repository controls: overlap with R05

### 4.1 Immutable chronological partitions — strong control

`docs/GATE2_RESEARCH_PROTOCOL.md` fixes:

- Development: `[2017-08-17, 2022-01-01)`
- Validation: `[2022-01-01, 2024-01-01)`
- locked OOS: `[2024-01-01, 2026-01-01)`

Development/model selection may use Development only. Validation is reserved for preregistered candidates that survive earlier gates. OOS is embargoed from strategy development, parameter selection, hypothesis selection, ranking, tuning, and decision-making.

**Assessment:** strong and worth preserving. R05 does not justify weakening it.

### 4.2 Prospective experiment registration — strong control

The protocol requires an experiment record before a backtest is treated as evidence, including hypothesis/version, dataset and partition, parameters/search space, costs, code/commit, benchmark, metrics, robustness tests, and decision rule.

Subsequent Gate 2 cycles are explicitly labeled prospective registrations before evidence generation.

**Assessment:** strong procedural defense against post-hoc relabeling and silent threshold changes.

### 4.3 Full grid retention within cycles — strong control

The robustness preregistration requires every attempted cell, including failed/error cells, to be retained. Later cycle preregistrations repeatedly prohibit parameter additions/removals after evidence and require all frozen cells to be attempted.

**Assessment:** directly aligned with Bailey et al.’s warning about the file-drawer problem at the within-cycle level.

### 4.4 No “best-cell wins” promotion — strong control

The initial robustness battery uses distributional/stability criteria (for example, a fraction of perturbation cells and median behavior) rather than selecting only the top-performing parameter cell. Cycle 7 explicitly prohibits choosing only the best observed cell for promotion.

**Assessment:** materially reduces parameter-optimization selection bias.

### 4.5 Versioning and no rescue — strong control

Failed hypotheses cannot be repaired by changing thresholds after evidence. Material strategy changes require a new hypothesis/strategy version and preregistration. Earlier hypothesis families remain closed for promotion purposes.

**Assessment:** strong auditability and prevents retrospective mutation of failed tests.

### 4.6 Current Gate 2 outcome — important context

The default branch contains merge commit `06b10145688cd8baca470e4bf0dc5bff8f40702d`, whose message closes the OHLCV-only Gate 2 Development program with **no candidate promoted to Validation**, while preserving locked Validation/OOS boundaries and no paper/live authorization.

**Assessment:** selection-bias risk has not been converted into a promoted trading claim in the closed Gate 2 program.

---

## 5. Scale of the recorded search

The repository documents a large enough research search that selection accounting is not optional.

### Prospectively registered parameter cells after HYP-0001–0004

- HYP-0005–0007: 45 cells
- HYP-0008–0010: executable grid totals 45 cells
- HYP-0011–0013: 33 cells
- HYP-0014–0016: 26 cells
- HYP-0017–0019: 28 cells
- HYP-0020–0022: 40 cells
- HYP-0023–0025: 28 cells

Total across HYP-0005–0025: **245 prospectively registered parameter cells**, before counting asset replication, cost/timing stress, regimes, leave-one-segment-out variants, concentration tests, drawdown/recovery tests, or other diagnostics.

### HYP-0001–0004 robustness neighborhood

The first robustness preregistration defines:

- HYP-0001: `3 × 3 = 9` parameter-neighborhood cells
- HYP-0002: `3 × 3 × 3 = 27`
- HYP-0003: `3 × 3 × 3 = 27`
- HYP-0004: `3 × 3 × 3 = 27`

Total parameter-neighborhood perturbations: **90 cells**, again before other robustness dimensions.

Therefore the repository visibly contains at least **335 registered parameter variants** across the closed Gate 2 strategy search before adding baselines, asset duplication, execution-cost/timing stress and other robustness variants.

This count is **not** asserted to equal the correct statistical `N` for PBO. It demonstrates only that the search is large enough that a global selection-accounting layer is warranted.

---

## 6. Important audit finding: Cycle 2 cell-count inconsistency

`docs/GATE2_CYCLE2_PREREGISTRATION_V1.md` describes HYP-0009 as:

- compression ratio: 3 choices
- breakout lookback: 2 choices
- breakout threshold: 3 choices

The Cartesian grid is therefore `3 × 2 × 3 = 18` cells, but the prose says **27 cells**.

The repository’s integrity test explicitly acknowledges this inconsistency and enforces:

- HYP-0008 = 18
- HYP-0009 = 18
- HYP-0010 = 9
- cycle total = 45

### R05 treatment

This is not evidence of hidden backtests; the executable grid and test make the actual intended enumeration visible. But it is an experiment-accounting defect.

**Required handling:**

- do not silently edit history to make the original preregistration appear internally perfect;
- preserve the original document/hash;
- create an explicit erratum/ledger annotation recording the mismatch and executable interpretation;
- use the actual executed grid in trial accounting, with provenance to the integrity test.

---

## 7. Main gap: cycle-local accounting is not the same as project-wide selection accounting

The project’s individual cycles are preregistered, but the **sequence of cycles is adaptive**.

For example, Cycle 7 states that its design change was motivated by repeated failures of the earlier ultra-short one-bar candidates. This is scientifically reasonable, but it means the broader research program learns from Development evidence and chooses what to test next.

That creates a second level of selection:

1. **within-cycle selection risk** — parameter/configuration alternatives tested together;
2. **across-cycle/meta-selection risk** — which mechanisms, holding periods, features and hypothesis families are pursued next after earlier outcomes are observed.

The current protocol recognizes repeated experimentation conceptually, but no single machine-readable object appears to consolidate the complete adaptive lineage into one global search history.

### Why this matters

A future strategy that finally passes after many failed research cycles should not be evaluated as though it were the first and only hypothesis ever tried. Preregistration protects each cycle from hindsight changes; it does not erase the statistical fact that the Development dataset has been repeatedly consulted across a growing research program.

This is the most important R05 gap.

---

## 8. Direct CSCV/PBO compatibility with the current project

### 8.1 What fits

A future CSCV implementation could in principle work with strategy configurations if the project can reconstruct for every trial:

- a common synchronous performance index;
- one return/P&L observation per common time row;
- identical row count across candidate columns;
- a registered selection metric estimable on subsamples;
- the complete comparison set actually involved in the selection process.

Hourly zero-return observations while a strategy is flat could potentially create a common clock for some strategy families, subject to a separately reviewed specification.

### 8.2 What does not fit automatically

The closed Gate 2 universe contains material heterogeneity:

- event-driven strategies with different signal frequencies;
- different lookback/warm-up requirements;
- explicit continuity breaks and eligibility differences;
- BTC/ETH strategies and one cross-asset predictor/target design;
- one-bar and later multi-hour holding periods;
- non-overlap rules;
- different regimes and sparse event sets;
- potentially autocorrelated strategy return streams, especially for multi-hour holding periods;
- sequential/adaptive hypothesis families created after prior Development outcomes.

A naive matrix that drops all non-common rows could destroy the actual information structure. A naive matrix that inserts zeros or aggregates returns could change the selection metric. Bailey et al. explicitly require synchronous rows and caution about strong autocorrelation.

### Decision

**Direct project-wide CSCV/PBO is UNRESOLVED, not approved.**

It requires a separately reviewed compatibility specification before any numerical PBO estimate is treated as evidence.

---

## 9. Selection-inference methods: roles and non-substitutability

R05’s primary source is PBO/CSCV, but nearby literature clarifies that different methods answer different questions.

### PBO / CSCV

Question: does the strategy-selection process tend to pick an in-sample winner that ranks poorly out-of-sample among the tested alternatives?

Best used only after a complete comparison set and compatible synchronous performance matrix are established.

### Deflated Sharpe Ratio

Bailey and López de Prado’s Deflated Sharpe Ratio adjusts Sharpe-ratio inference for selection bias/multiple testing and non-normality. It is relevant when Sharpe is a key selected performance statistic, but it is not a substitute for causal timing, costs, robustness or protected holdouts.

### White Reality Check

White’s Reality Check addresses data snooping by testing whether the best model encountered in a specification search has predictive superiority over a benchmark while accounting for the search. This is particularly relevant when comparing many rules against a common benchmark.

### Hansen SPA

Hansen’s Superior Predictive Ability test modifies the Reality Check to reduce sensitivity to poor/irrelevant alternatives and uses studentization and a sample-dependent null.

### Harvey–Liu–Zhu multiple-testing perspective

Their asset-pricing work shows why ordinary single-test significance thresholds become inadequate after extensive factor/hypothesis search. It supports the project-level principle that the number and dependence of attempted ideas cannot be ignored.

### R05 implication

No single method should be installed by name and treated as a universal “overfitting solved” switch. The future selection-inference method must match the project’s outcome metric, dependence structure, overlapping observations, benchmark, trial universe and sequential research design.

---

## 10. Proposed R05-A: Global Research Search Ledger

Before future large-scale strategy discovery, create a durable machine-readable ledger that is append-only in research meaning.

### Suggested fields

```yaml
trial_record_id: null
research_program: null
cycle_id: null
search_family_id: null
guided_search_id: null
parent_trial_ids: []
hypothesis_id: null
strategy_id: null
strategy_version: null
status: planned # planned/executed/error/rejected/promoted/abandoned
classification: preregistered # exploratory/preregistered/diagnostic
created_before_evidence: null
preregistration_path: null
preregistration_hash: null
code_commit: null
dataset_identity: null
partition: null
asset_universe: []
parameter_cell_id: null
parameter_hash: null
cost_model_id: null
execution_model_id: null
benchmark_id: null
selection_metric: null
selection_rule: null
result_artifact: null
result_hash: null
error_recorded: null
validation_accessed: false
oos_accessed: false
information_used_to_generate_trial: []
prior_result_dependencies: []
selection_family_membership: []
notes: null
```

### Rules

1. Never delete failed/error evidence-generating trials from the ledger.
2. Do not count mere brainstormed ideas as executed trials, but record the research lineage for ideas selected after prior evidence.
3. Record the final outcome of an adaptive/guided optimizer as the trial unit when that is the relevant selection alternative, consistent with Bailey et al.’s guidance; retain optimizer provenance separately.
4. Record exactly which prior Development findings influenced creation of a later hypothesis family.
5. Preserve original preregistrations and add errata rather than rewriting history.
6. Persist result hashes; do not rely solely on short-lived CI artifacts as the durable research record.
7. Freeze the comparison/selection family before applying any formal selection-inference procedure to it.

---

## 11. Proposed R05-B: Selection-Inference Compatibility Study

This should be **design-only first**.

### Phase 1 — trial reconstruction

- reconstruct all evidence-generating strategy/configuration trials from HYP-0001 onward;
- reconcile preregistered counts with executable grids and retained artifacts;
- document missing artifacts or ambiguities;
- identify adaptive/guided search lineages.

### Phase 2 — performance alignment study

Without using Validation/OOS:

- determine whether strategies can be represented on a common causal hourly return index;
- specify treatment of flat periods, warm-ups, continuity breaks and unavailable rows;
- quantify autocorrelation and overlap induced by holding periods;
- determine whether one project-wide matrix is defensible or whether family-specific matrices are required.

### Phase 3 — candidate inference methods

Compare, without cherry-picking from outcomes:

- CSCV/PBO;
- DSR where Sharpe-based selection is relevant;
- White Reality Check / Hansen SPA where a common benchmark and loss/performance differential are appropriate;
- familywise/FDR controls for hypothesis-level inference where formal p-values exist.

### Phase 4 — freeze before execution

Freeze:

- comparison set;
- performance metric;
- row alignment;
- block/partition design;
- dependence treatment;
- bootstrap method if any;
- missing/error rules;
- thresholds;
- interpretation rules.

Only then run selection inference.

---

## 12. Recommended governance changes

### Keep unchanged

- chronological Development / Validation / locked-OOS architecture;
- OOS embargo;
- prospective preregistration;
- causal execution contract;
- explicit costs/slippage;
- no rescue after failure;
- full registered-grid retention;
- binary promotion gates;
- no paper/live authorization from Development evidence alone.

### Add

- global search ledger;
- explicit search-lineage / parent-trial relationships;
- durable artifact hashes;
- preregistration errata mechanism;
- selection-family declaration;
- formal selection-inference compatibility review before use;
- project-level record of the cumulative number and nature of tested hypotheses/configurations.

### Do not add yet

- a numerical PBO threshold as a new promotion gate;
- CSCV as a replacement for chronological Validation/OOS;
- PBO-based optimization or strategy selection;
- a retroactive best-effort PBO estimate from incomplete or non-synchronous trial histories;
- a method chosen after inspecting which correction gives the most favorable result.

---

## 13. Falsification / stop conditions for formal PBO adoption

Do **not** advance to a numerical project-wide PBO estimate if any of the following remain unresolved:

1. material evidence-generating trials cannot be reconstructed;
2. the comparison set excludes failed trials or includes padding alternatives only to improve the result;
3. strategy returns cannot be placed on a defensible synchronous index without materially changing the research question;
4. strong autocorrelation/overlap makes the chosen CSCV partition design inappropriate;
5. different strategy families use incompatible performance metrics or eligibility universes without a justified mapping;
6. the search lineage is adaptive but the trial universe is treated as if fixed and independent of prior results;
7. the method or its tuning choices are selected after seeing which gives the lowest PBO;
8. PBO is proposed as a replacement for causal correctness, transaction-cost realism, robustness, Validation or locked OOS;
9. PBO is used as the objective function for choosing the next strategy.

---

## 14. Evidence cards

### R05-C01 — repeated selection inflates false-discovery risk

```yaml
claim_id: R05-C01
source_id: R05-primary
source_version: February-2015-manuscript
review_status: reviewed
source_locator: Introduction, pp. 3-7
claim_paraphrase: Repeated strategy/configuration testing on the same finite data creates selection-driven false-positive risk that single-test thresholds or a simple holdout do not account for.
evidence_type: methodological argument and formal framework
market_and_sample: generic investment backtests
data_requirements: [complete trial history]
method_and_assumptions: [strategy selection among multiple alternatives]
reported_effect_and_uncertainty: method-level claim; no project-specific magnitude inferred
limitations_and_contradictions: [method does not repair flawed backtests]
proposed_project_application: account for cumulative strategy search rather than only the surviving candidate
existing_repo_overlap: strong procedural multiple-testing controls, no global selection inference identified
causal_timing_requirements: []
cost_and_execution_requirements: []
falsification_or_rejection_condition: reject project-wide use if trial history is materially incomplete
next_action: build global search ledger
decision: supported
decision_reason: directly applicable methodological concern
```

### R05-C02 — CSCV requires synchronous comparable trial performance

```yaml
claim_id: R05-C02
source_id: R05-primary
source_version: February-2015-manuscript
review_status: reviewed
source_locator: Algorithm 2.3, Section 2.2
claim_paraphrase: CSCV uses a T-by-N performance matrix with synchronous rows across all trial columns; different frequencies must be mapped to a common index.
evidence_type: method definition
market_and_sample: generic investment backtests
data_requirements: [per-trial performance time series, synchronous index]
method_and_assumptions: [common row count, common observation index, subsample-estimable performance metric]
reported_effect_and_uncertainty: not applicable
limitations_and_contradictions: [current project has heterogeneous event frequency, warmups, holding periods and continuity boundaries]
proposed_project_application: compatibility study before any PBO computation
existing_repo_overlap: no project-wide PBO implementation identified
causal_timing_requirements: [preserve causal performance accounting]
cost_and_execution_requirements: [preserve registered costs]
falsification_or_rejection_condition: do not use if defensible common index cannot be specified prospectively
next_action: R05-B design review
decision: unresolved
decision_reason: method prerequisites not yet demonstrated
```

### R05-C03 — complete trial history is mandatory

```yaml
claim_id: R05-C03
source_id: R05-primary
source_version: February-2015-manuscript
review_status: reviewed
source_locator: Section 5.2, limitation in application
claim_paraphrase: Hidden actual trials bias PBO downward; the procedure depends on complete reporting of the actual search history.
evidence_type: stated method limitation
market_and_sample: generic investment backtests
data_requirements: [complete actual trial set]
method_and_assumptions: [selection alternatives are represented faithfully]
reported_effect_and_uncertainty: qualitative direction of bias stated by authors
limitations_and_contradictions: [adding doomed alternatives can also bias assessment]
proposed_project_application: global append-only research search ledger
existing_repo_overlap: every registered cell is retained within cycles, but no single global ledger identified
causal_timing_requirements: []
cost_and_execution_requirements: []
falsification_or_rejection_condition: block formal PBO if material trials cannot be reconstructed
next_action: trial-history reconciliation
decision: supported with gap
decision_reason: local accounting strong; project-wide completeness unproven
```

---

## 15. Source/version notes

### Primary

- Bailey, D. H.; Borwein, J. M.; López de Prado, M.; Zhu, Q. J. *The Probability of Backtest Overfitting*. Author-hosted manuscript, revised February 2015.  
  https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf

### Final publication metadata

- Bailey, D. H.; Borwein, J. M.; López de Prado, M.; Zhu, Q. J. *The Probability of Backtest Overfitting*. *Journal of Computational Finance*, 20(4), April 2017. DOI `10.21314/JCF.2016.322`.

The February 2015 manuscript date is retained as the R05 source version specified by the playbook; the later journal publication is recorded separately and is not backdated into the manuscript.

### Related methodological context

- Bailey, D. H.; López de Prado, M. *The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality*. *Journal of Portfolio Management* 40(5), 2014.
- White, H. *A Reality Check for Data Snooping*. *Econometrica* 68(5), 2000, 1097–1126.
- Hansen, P. R. *A Test for Superior Predictive Ability*. *Journal of Business & Economic Statistics* 23(4), 2005, 365–380.
- Harvey, C. R.; Liu, Y.; Zhu, H. *… and the Cross-Section of Expected Returns*. *Review of Financial Studies* 29(1), 2016, 5–68.

These related papers provide context for alternative selection/multiple-testing questions; they do not by themselves authorize a method for this project.

---

## 16. Final R05 determination

### Supported

- The project correctly treats repeated experimentation as research information.
- Prospective preregistration, complete within-cycle grids, explicit errors, robustness neighborhoods, immutable partitions and the OOS embargo are materially aligned with anti-overfitting principles.
- Future positive results must be interpreted in light of the cumulative search, not as isolated first attempts.

### Unsupported

- Any claim that the project has already “solved” selection bias merely because each cycle was preregistered.
- Any claim that ordinary protected holdouts alone quantify the probability of backtest overfitting after a large adaptive search.
- Any immediate project-wide PBO number computed without reconstructing a compatible complete trial matrix.

### Unresolved

- Whether one project-wide CSCV/PBO analysis is mathematically and economically compatible with the heterogeneous strategy universe.
- Whether family-specific PBO plus another project-level multiplicity method is preferable.
- The exact effective comparison set after accounting for adaptive cycle-to-cycle research decisions.

### Required next action

**Do not change the trading rules or protected partitions.** First create and independently review the **global search-ledger specification and selection-inference compatibility plan**. Only after the trial history and matrix construction rules are frozen should any new selection-inference computation be run.

**R05 classification:** COMPLETE REVIEW / FOLLOW-UP GOVERNANCE WORK REQUIRED / NO STRATEGY OR TRADING AUTHORIZATION.