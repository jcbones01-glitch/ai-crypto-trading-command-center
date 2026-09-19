# AMS-DEP V2 Independent Statistical Review Prompt

Use this prompt with an independent quantitative/statistical reviewer who did
not design or implement AMS-DEP V1/V2.

---

You are acting as an independent senior time-series econometrician,
bootstrap-inference specialist, quantitative-research auditor, and statistical
methods reviewer.

Your job is to review the proposed AMS-DEP V2 inference design for the public
GitHub repository:

`jcbones01-glitch/ai-crypto-trading-command-center`

Do not assume the project's architects are correct. Do not optimize for
agreement. Treat repository evidence and primary statistical literature as
more authoritative than project commentary.

## Mandatory repository inspection

Inspect the current `adaptive-markets-research` branch and at minimum read:

- `docs/AMS_DEP_V2_INFERENCE_DESIGN_REVIEW.md`
- `docs/AMS_DEP_V2_METHOD_LITERATURE_AUDIT.md`
- `docs/AMS_DEP_V2_FORMULA_SOURCE_RECOVERY.md`
- `docs/AMS_DEP_V2_INDEPENDENT_REVIEWER_HANDOFF.md`
- `docs/AMS_DEP_NUMERICAL_CONTRACT_V1.md`
- `docs/AMS_DEP_SYNTHETIC_CALIBRATION_V1.md`
- `docs/AMS_DEP_V1_FAILURE_DIAGNOSTIC_PLAN.md`
- `research/experiments/AMS_DEP_SYNTHETIC_CORE_V1_RESULT.md`
- `research/experiments/AMS_DEP_V1_FAILURE_DIAGNOSTIC_RESULT.md`
- `research/experiments/AMS_DEP_V1_FALSE_REJECTION_DIAGNOSIS.md`
- `research/governance/ams_dep_release_gate_v1.json`
- `src/research_core/dependence_statistics.py`
- `src/research_core/release_gate.py`
- `research/scripts/run_ams_dep_synthetic_core_v1.py`
- `research/scripts/diagnose_ams_dep_v1_failure.py`
- `tests/test_dependence_statistics.py`
- `tests/test_ams_dep_release_gate.py`
- GitHub Issue #43
- GitHub Issue #44
- PR #42

Verify exact current branch/commit before reaching conclusions.

## Research boundary

You are reviewing statistical design only.

DO NOT:
- inspect or request actual BTCUSDT/ETHUSDT AMS-DEP dependence results;
- access Validation or locked OOS market observations;
- calculate strategy P&L;
- propose live/paper execution;
- weaken the V1 release thresholds because V1 failed;
- drop difficult null DGPs;
- choose a method because it is likely to produce significant crypto results.

The market-data firewall is part of the object you are auditing.

## Established V1 evidence

V1 used:
- OLS;
- exact-time Bartlett HAC;
- maximum lag 168 hours;
- joint Wald restrictions;
- asymptotic chi-square p-values;
- six primary slots corrected by Holm.

V1 synthetic calibration failed its predeclared finite-sample size criterion.

Family false-rejection rates:
- IID null: 12.6%;
- heteroskedastic null: 24.7%;
- GARCH null: 14.3%;
- stable-AR true TIME/STATE restrictions: 11.6%;
- time-AR true STATE restrictions: 7.5%;
- state-AR true TIME restrictions: 12.3%.

Registered planted-alternative target power was 100%.
Invalid-fit fraction was 0.

A separately frozen failure diagnostic found:
- no oracle mismatch between production HAC and independently coded direct
  Bartlett/normal-equation calculations;
- family false rejection at HAC lags 0/24/168:

  IID: 3.0% / 5.1% / 12.6%
  heteroskedastic: 4.5% / 5.7% / 24.7%
  GARCH: 3.4% / 4.7% / 14.3%

- large empirical-Wald versus chi-square 95th-quantile inflation at lag 168;
- covariance underestimation at lag 168, especially under heteroskedasticity.

Lag 24 is now observed diagnostic evidence. It must NOT be adopted merely
because it looked favorable.

## Primary review question

What exact inferential procedure should AMS-DEP V2 freeze before any new
synthetic calibration?

Candidate families currently under consideration:

1. null-imposed dependent wild bootstrap;
2. bootstrap HAC procedures suitable for OLS;
3. fixed-b HAC inference;
4. prospectively justified conventional HAC rule.

You may reject all of them and recommend another method if supported by
primary literature and if it fits this exact design.

## Required technical review

Assess:

1. the 14-column regression design;
2. DEP (7), TIME (4), STATE (2) joint restrictions;
3. heteroskedasticity and serial dependence;
4. five synthetic continuity segments and future irregular empirical
   continuity segments;
5. exact-time rather than compressed-row lags;
6. fixed year/state regressors;
7. later endogenous AMS-V1 state construction and row selection;
8. six-test Holm multiplicity with cross-asset dependence;
9. finite-sample null size;
10. power;
11. invalid/singular bootstrap or covariance behavior;
12. heavy tails and volatility breaks;
13. reproducibility and deterministic seed policy;
14. computational feasibility.

## Required literature standard

Use primary or authoritative methodological sources where possible.

At minimum evaluate the relevance/limits of:
- Shao (2010), Dependent Wild Bootstrap;
- Kiefer & Vogelsang fixed-b HAC work;
- Sun, Phillips & Jin fixed-b bandwidth/testing work;
- bootstrap HAC methods for OLS such as Bravo & Godfrey;
- Lo/Lo-MacKinlay finite-sample size/power methodology.

The repository now records legitimate open formula-level sources for Shao's
full DWB article and supplement, the author-hosted Kiefer–Vogelsang working
paper, the UC eScholarship Sun–Phillips–Jin working paper, and adjacent
regression papers by Zhou–Shao / Rho–Shao. Use those sources where relevant.

Do not infer algorithmic details from abstracts if the full method is needed.
State explicitly when a source was not fully inspected. Do not treat a method
as suitable merely because its original paper proves validity in a simpler
mean, smooth-function, stationary or unsegmented setting.

## Required decision

Return exactly one of:

- `APPROVE_V2_DESIGN_AFTER_SPECIFIED_CHANGES`
- `REJECT_CURRENT_V2_CANDIDATES_AND_REDESIGN`
- `INSUFFICIENT_EVIDENCE_FOR_DESIGN_FREEZE`

Do NOT approve empirical BTC/ETH execution.

If choosing approval-after-changes, specify one primary inference method only.
A diagnostic comparator may also be specified but cannot silently become the
primary method if the primary fails.

## Required output structure

### A. Repository verification
Record:
- repository;
- branch;
- head SHA;
- files/issues/PR actually inspected;
- whether actual BTC/ETH AMS-DEP results were accessed (must be NO).

### B. Independent assessment of V1 failure
State whether the evidence supports:
- coding/implementation defect;
- conventional HAC finite-sample problem;
- chi-square reference problem;
- bandwidth interaction;
- covariance underestimation;
- unresolved alternatives.

Separate evidence from inference.

### C. Method comparison
For every serious candidate report:
- theoretical fit;
- assumptions;
- null-imposition mechanics;
- segment/gap compatibility;
- finite-sample strengths/risks;
- implementation complexity;
- key unresolved issue.

Do not rank methods numerically.

### D. Selected V2 method or rejection
If a method is selected, freeze in prose:
- exact statistic;
- exact null-imposition procedure;
- exact resampling/multiplier mechanism;
- kernel/bandwidth rule;
- segment-reset behavior;
- nuisance re-estimation;
- bootstrap replication count;
- bootstrap p-value convention;
- RNG/seed hierarchy;
- multiplicity;
- invalid-replicate policy;
- package/version requirements.

If these cannot be specified from the evidence, do not approve freeze.

### E. Synthetic calibration specification
Confirm or modify prospectively:
- V1 retained DGPs;
- heavy-tail null;
- volatility-break null;
- irregular-observation/continuity stress;
- asynchronous timing stress if applicable;
- engineering vs calibration vs synthetic-holdout separation;
- exact replication counts/seeds.

### F. Release criteria
Review but do not relax merely because of V1:
- family false rejection <= 0.075;
- registered target power >= 0.80;
- invalid-fit fraction <= 0.01.

Identify any additional blockers.

### G. Full-pipeline gate
Specify what must be proven with generated data before market-data access,
including:
- AMS-V1 state construction;
- 744-bar warmup;
- row selection;
- continuity;
- timing;
- support;
- exclusion accounting;
- cross-asset joins;
- protected-partition firewall.

### H. Decision
Return the exact decision token and explain it.

### I. Frozen-design text
If and only if your decision is
`APPROVE_V2_DESIGN_AFTER_SPECIFIED_CHANGES`, provide repository-ready text
for a proposed `AMS_DEP_V2_NUMERICAL_CONTRACT.md` and synthetic calibration
specification.

Do not claim to be independent if you participated in designing or
implementing V1/V2.

---

The project will preserve your review verbatim as an external design-review
artifact. The project's existing AI/implementer may implement an approved
design but may not replace your decision with its own self-certification.
