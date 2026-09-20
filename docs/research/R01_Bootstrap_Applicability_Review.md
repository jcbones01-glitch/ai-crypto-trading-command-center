# R01 — Bootstrap applicability review

Completed: 2026-09-20. Scope: literature applicability, repository reconciliation, and synthetic-coverage inventory. This is a completed review with unresolved applicability findings, not a proof, ratification, calibration result, or execution authorization.

## Decision memo

**Retain the frozen V2 experiment and its existing release gates. The literature supports investigating dependent wild bootstrap, but does not establish the validity of the exact AMS-DEP implementation.**

The first playbook work package is complete: repository state was checked; prior literature work was deduplicated; Shao's full article and supplement were retrieved and reviewed for applicability; assumptions were mapped to the implementation; existing synthetic coverage was inventoried; and bounded follow-ups are specified below. Unresolved theory is a review result, not something silently counted as verified.

Three findings matter most:

1. The repository has advanced beyond its older review packet. Its current machine gate authorizes **frozen synthetic calibration only**. Holdout, actual-market inference, Validation/OOS, P&L, and trading remain blocked. The older PR description and several documents still describe the pre-ratification stage.
2. Heavy tails, variance changes, irregular hours, and asynchronous observations are already in the frozen suite. Adding those same categories again would duplicate existing work. The material remaining coverage questions concern combinations of stresses, empirical-style segment geometry, and states/eligibility generated from the return history.
3. A cited follow-up paper contains negative evidence that deserves explicit treatment: Brüggemann–Jentsch–Trenkler distinguish slope inference from variance-parameter inference and demonstrate failure of certain ordinary wild-bootstrap procedures. That is a limit on citation transfer, not a demonstrated failure of AMS-DEP's dependent multipliers.

**Recommended action:** preserve V2 unchanged; assess its eventual complete calibration artifact under its registered rules; keep theoretical and full-pipeline questions open. Any additional result-affecting experiment requires its own prospective specification and review. Do not use this review to unlock anything.

## 1. Repository evidence and current scope

Repository: [ai-crypto-trading-command-center](https://github.com/jcbones01-glitch/ai-crypto-trading-command-center).

| Item | Verified snapshot |
| --- | --- |
| Research branch | `adaptive-markets-research` |
| Full reviewed head | `6431e9995ed3c904b673603b662506692d370539` |
| Default branch and head | `main`, `7aa2da44f19474978854905caff1ea78e05ff540` |
| PR #42 | Open draft; head is the research branch; base is `gate2-research-foundation`, not `main` |
| Current machine gate | `V2_SYNTHETIC_CALIBRATION_AUTHORIZED`; calibration-passed flag false |
| Frozen source identity | All 10 Git blob IDs in the freeze manifest match the reviewed branch tree |
| Latest listed release-gate workflow | Run `35466242754`, success, at reviewed head |
| Latest listed engineering workflow | Run `35458812083`, success, at `e348f2f2eb0ce3b5da243bea0d9bed4a2bbd4a18` |
| Calibration workflow observed | Run `35460656875`, queued, at `e348f2f2eb0ce3b5da243bea0d9bed4a2bbd4a18`; status is a retrieval-time snapshot |
| Applicable repository instructions | No `AGENTS.md` appeared in the recursive tree returned for the reviewed head |

Primary state evidence: [release gate](https://github.com/jcbones01-glitch/ai-crypto-trading-command-center/blob/6431e9995ed3c904b673603b662506692d370539/research/governance/ams_dep_release_gate_v1.json), [ratification record](https://github.com/jcbones01-glitch/ai-crypto-trading-command-center/blob/6431e9995ed3c904b673603b662506692d370539/docs/AMS_DEP_V2_INDEPENDENT_RATIFICATION_RESULT.md), [freeze manifest](https://github.com/jcbones01-glitch/ai-crypto-trading-command-center/blob/6431e9995ed3c904b673603b662506692d370539/research/governance/ams_dep_v2_freeze_manifest.json), [PR #42](https://github.com/jcbones01-glitch/ai-crypto-trading-command-center/pull/42), [Issue #43](https://github.com/jcbones01-glitch/ai-crypto-trading-command-center/issues/43), [Issue #44](https://github.com/jcbones01-glitch/ai-crypto-trading-command-center/issues/44), and [calibration run](https://github.com/jcbones01-glitch/ai-crypto-trading-command-center/actions/runs/35460656875).

The false calibration-passed flag is **not evidence of V2 failure**. The ratification record preserves a user-supplied review with self-attested independence; this review does not authenticate that person's identity. Historical V1 synthetic failures remain retained. Workflow success is engineering evidence, not statistical validity.

No actual BTC/ETH AMS-DEP outcomes, protected partitions, or strategy P&L were accessed. No simulation was launched, queued run altered, code edited, repository commit created, or gate changed. This review is not a new independent-release approval. Tests were inspected, not rerun; no new test-count claim is made.

## 2. Deduplication and source evidence

Existing overlap is substantial:

| Existing repository document | Work already present | This review's contribution |
| --- | --- | --- |
| `AMS_DEP_V2_METHOD_LITERATURE_AUDIT.md` | DWB, regression bootstrap, fixed-b comparators, source-access limitations | Updated source assessment, without repeating method selection |
| `AMS_DEP_V2_FORMULA_SOURCE_RECOVERY.md` | Shao article/supplement recovery; irregular-time and bandwidth caveats; Rho–Shao 2015 | Exact source locators linked to frozen code |
| `AMS_DEP_V2_THEORY_GAP_MATRIX.md` | Earlier design and transfer gaps | Separates subsequently resolved specification choices from still-unresolved validity |
| `AMS_DEP_V2_STOCHASTIC_REGRESSOR_REVIEW.md` | Gonçalves–Kilian, Godfrey, Hafner–Herwartz, Brüggemann–Jentsch–Trenkler | Qualifies the last citation using its negative results |
| Numerical contract, frozen JSON, tests | Exact algorithm and eleven synthetic cases | Coverage inventory and proposals limited to missing dimensions |

These documents are under `docs/` at the reviewed SHA. Rho–Shao's 2019 unit-root paper is an additional targeted nonstationarity reference relative to the method documents inspected here. This is not a claim of exhaustive deduplication across every historical branch or external bibliography.

### Primary evidence cards

**S1 — Shao (2010), published article, JASA 105, 218–235.** Full text reviewed for applicability, including the theorem statements and relevant proof material; no independent proof reconstruction or replication claimed. [Author-hosted article](https://publish.illinois.edu/xshao/files/2012/11/JASA-DWB.pdf).

Traceable extraction: §2, Assumptions 2.1–2.2 (pp. 219–220): data-independent, centered, unit-variance multipliers; admissible covariance kernel. §3, Assumptions 3.1–3.2 and Theorem 3.1 (p. 221): stationary smooth-function framework, strong-mixing summability, finite `2+δ` moments (`δ≥2`), summable fourth cumulants, nonsingular long-run covariance, nonzero derivative, Lipschitz derivatives, and `ell→∞`, `ell=o(n^(δ/(2+2δ)))`. §4, Assumptions 4.1–4.2 and Theorems 4.1–4.2 (p. 222): actual-time lattice geometry, bounded boundary complexity, stronger smoothness/moment conditions. Corollary 4.1 concerns variance-estimation MSE, not an AMS-DEP testing optimum. §5, Theorems 5.1–5.2 (pp. 223–224): stochastic nonlattice sampling, mean inference. §4 (p. 223): Gaussian multipliers lack general second-order correctness. §6, Table 2 (p. 230): finite-sample undercoverage can remain substantial.

Decision: **supported building blocks; unresolved exact regression transfer**. No claim that every theorem assumption holds for the project.

**S2 — Shao (2010), supplementary material.** [Author-hosted supplement](https://publish.illinois.edu/xshao/files/2012/11/dwb-final-supp.pdf), §0.1 pp. 1–7; §0.2 pp. 7–8; §0.3 Tables 1–2 pp. 9–10. The proof of Theorem 4.1 controls Taylor remainders and boundary contributions; Theorem 4.2's proof is abbreviated by reference to the preceding argument; Theorem 5.2 treats the mean under its stated sampling design. The supplement does not supply the project's restricted-regression proof. Its simulation tables concern Gaussian processes with spherical covariance, not crypto returns. Decision: **useful proof detail, no closure of AMS-DEP gaps**.

**S3 — Rho and Shao (2015), regression with weak dependence and heteroscedasticity.** [Author-hosted accepted manuscript](https://publish.illinois.edu/xshao/files/2015/05/JBES.pdf), model in §2; §3, (R1)–(R2), (B1), Theorems 3.1–3.2 and Remarks 3.3–3.4, manuscript pp. 10–14. Relevant sections reviewed. Its nonrandom regressors, recursive self-normalizer and iid wild multipliers differ from V2. Remark 3.3 explains why removing the normalization generally breaks the bootstrap distributional match. Joint linear restrictions appear in Remark 3.4, but with that paper's normalization. Decision: **adjacent precedent; importing its theorem as certification of Parzen-HAC Wald is unsupported**. The technical supplement was not independently reviewed, and its proofs are not relied on to certify V2.

**S4 — Rho and Shao (2019), unit roots with piecewise locally stationary errors.** [Author-linked arXiv manuscript](https://arxiv.org/pdf/1802.05333), §2 (A1)–(A4), (Z1)–(Z2), pp. 5–6; §3 (B1)–(B2), Algorithm 3.1, Theorems 3.1–3.2, pp. 13–15. Relevant sections reviewed. Assumptions include local Lipschitz behavior between finitely many breaks, bounded fourth moments, geometric physical-dependence decay, positive long-run variance and bandwidth exponent between zero and one third. Algorithm 3.1 generates a recursive pseudo-series under the unit-root null; it uses unrestricted residuals at its residual-estimation step. Decision: **nonstationary DWB precedent, not the frozen fixed-X AMS-DEP algorithm**. Supplementary proofs were not independently audited.

**S5 — Brüggemann, Jentsch and Trenkler (2016), VAR inference.** [Author/institution-hosted manuscript dated July 16, 2015](https://lwus.statistik.tu-dortmund.de/storages/lwus-statistik/r/Paper/Brueggermann_Heteroskedasticity.pdf), abstract, §1 pp. 1–2, §2.2 and §3.1–3.3 pp. 8–10. Relevant sections reviewed; the manuscript date differs from journal publication. The authors distinguish slope inference under additional martingale-difference assumptions from inference involving innovation variances. Ordinary wild and pairwise bootstraps can fail to reproduce the required fourth-moment structure; residual moving-block bootstrap is their positive alternative. Decision: **retain as conditional precedent and negative evidence**. Their iid multiplier counterexample does not, by itself, reject dependent Gaussian multipliers or the project's studentized slope tests. It also cannot certify them.

**S6 — Dynamic-regression references retained at limited evidence status.** Hafner–Herwartz (2009), [publisher record](https://onlinelibrary.wiley.com/doi/10.1111/j.1467-9574.2009.00424.x): abstract-level evidence for fixed-design wild-bootstrap VAR restrictions; full-text opening failed in this session. Gonçalves–Kilian (2004), DOI `10.1016/j.jeconom.2003.10.030`, and Godfrey (2011), DOI `10.1111/j.1468-0084.2010.00630.x`: existing repository references, not independently formula-reviewed here. Djogbenou–Gonçalves–Perron (2015), DOI `10.1111/jtsa.12118`, is already in the repository and remains a candidate for estimated-regressor follow-up. No uninspected theorem from these references is used to close a gap.

## 3. Assumption-to-implementation matrix

Locations below are pinned to the reviewed SHA. Labels mean: **supported** for the stated narrow use, **unsupported** for the proposed inference from a source, and **unresolved** where an exact justification is absent. Implementation agreement is not a theorem.

Code references:

- [DWB core](https://github.com/jcbones01-glitch/ai-crypto-trading-command-center/blob/6431e9995ed3c904b673603b662506692d370539/src/research_core/dependent_wild_bootstrap_v2.py).
- [Design and Holm helper](https://github.com/jcbones01-glitch/ai-crypto-trading-command-center/blob/6431e9995ed3c904b673603b662506692d370539/src/research_core/dependence_statistics.py).
- [Numerical contract](https://github.com/jcbones01-glitch/ai-crypto-trading-command-center/blob/6431e9995ed3c904b673603b662506692d370539/docs/AMS_DEP_V2_NUMERICAL_CONTRACT.md).
- [Calibration runner](https://github.com/jcbones01-glitch/ai-crypto-trading-command-center/blob/6431e9995ed3c904b673603b662506692d370539/research/scripts/run_ams_dep_v2_calibration_shard.py).

| ID / source locator | Actual implementation and contract location | Applicability decision / follow-up |
| --- | --- | --- |
| A01 / S1 §2 | Core `parzen`, `ParzenGeometry.__init__`, `multipliers`; contract “Exact-time Parzen kernel” | **Supported building block.** Gaussian innovations multiplied by the Cholesky factor generate the specified conditional covariance. No centering or normalization of realized multipliers is added. This is not an assertion that residuals are Gaussian. |
| A02 / S1 Theorem 3.1 | `primary_design`; core `FixedOLS`, `wald`; contract “Model and restrictions” | **Unresolved.** Fourteen design columns include realized returns and year/state interactions. Need a score/vector limit argument plus covariance consistency, not a theorem-name match. The quadratic null statistic is not automatically a scalar smooth statistic with nonzero first derivative. |
| A03 / S1 Assumptions 3.1–3.2; S2 §0.1 | Synthetic `_base_returns`; `FixedOLS.fit` constructs regressor-residual products | **Unresolved at score level.** Moment conditions must be checked for transformed variables and scores. Finite fourth moments of raw returns alone do not establish all required moments after squaring or interaction. |
| A04 / S1 Corollary 4.1 | `segment_geometry`: `max(2,n_s**.2)`; same rule in contract | **Unsupported as an optimal-test claim.** The exponent does not justify the unit constant, floor, segment-specific application or finite-sample rejection behavior. Calculated from the frozen rule: 2,000 rows give about 4.573 hours of kernel support, so integer-hour weights vanish from lag 5 onward. Keep the registered rule; no post-result bandwidth choice. |
| A05 / S1 Assumptions 4.1–4.2; S2 boundary argument | Core geometry uses actual hour differences and independent segment blocks | **Supported exact-time implementation; unresolved sampling-limit transfer.** Arbitrary missingness, short segments and a growing number of boundaries need separate justification. A continuity break is not automatically proof that the underlying economic process restarts independently. |
| A06 / S1 §5; S4 Algorithm 3.1 | `_observed_mask`, `_segment_for_offsets`; fixed calendar masks | **Unsupported direct use of a nonlattice random-sampling theorem.** Project hours lie on a lattice and masks are deterministic. Neither that theorem nor the unit-root recursion is the actual implementation. |
| A07 / S3 §3; S4 Algorithm 3.1 | Core `restricted_components`; runner `_run_slot`; contract “Model and restrictions” | **Specification supported; statistical transfer unresolved.** Free-column OLS imposes each zero restriction; residuals are centered by segment; `y*=fitted+residual*weights`; X remains fixed. Re-estimating beta/residuals does not regenerate lagged returns or state labels. |
| A08 / S3 Theorem 3.2; S5 §3 | Core `FixedOLS.fit`, `wald`; contract “Studentization” | **Unresolved exact test validity.** Original and bootstrap samples use the same Parzen sandwich and `n/(n-p)` adjustment. This is internally consistent, but different from S3's self-normalization and not validated by S5's ordinary-wild results. |
| A09 / project algorithm, not a borrowed theorem | `bootstrap_p_value`, `count_exceedances`; contract “Draws, seeds and invalidity” | **Supported accounting.** Exactly 4,999 requested draws for available originals; equality and invalid draws count as exceedances; no redraw. For any fixed draw list, counting invalids this way cannot lower the reported p-value. The +1 formula is not itself proof of an exact finite-sample test for an estimated composite null. |
| A10 / project multiplicity | `holm_six`; frozen six `primary_slots`; aggregation `summarize` | **Retain unchanged.** Six-slot correction does not repair miscalibrated marginal p-values. Unavailable slots remain present. Calibration checks true-null subsets in partial alternatives, not only the global null. |
| A11 / S1 §4; S5 §3 | Gaussian multipliers; all Wald covariance estimates recomputed | **Unsupported universal accuracy claim.** Neither higher-order accuracy nor validity under arbitrary heteroskedasticity follows from the word “bootstrap.” No profitability inference follows from statistical rejection. |

Additional reviewer deduction for A03: a Student-t5 variable has divergent eighth moment, so a naive smooth-moment-vector argument containing squared returns cannot assume that vector has a finite fourth moment. This follows from the t5 tail density proportional to `|x|^-6`. It does **not** prove failure of V2: a weaker score-based argument might suffice. Retain the t5 stress rather than excluding it to fit convenient theory.

## 4. Existing synthetic coverage

Authoritative specification: [frozen V2 JSON](https://github.com/jcbones01-glitch/ai-crypto-trading-command-center/blob/6431e9995ed3c904b673603b662506692d370539/research/experiments/ams_dep_synthetic_core_v2.json). Implementation: [synthetic generator](https://github.com/jcbones01-glitch/ai-crypto-trading-command-center/blob/6431e9995ed3c904b673603b662506692d370539/src/research_core/ams_dep_v2_synthetic.py), particularly `_base_returns`, `_observed_mask`, `_segment_for_offsets`, `simulate_case`.

| Frozen case | What it covers | Limit relevant to R01 |
| --- | --- | --- |
| `iid_null` | Baseline zero conditional-mean dependence | Does not establish robustness to dependent scores |
| `heteroskedastic_null` | Exogenous state-linked variance levels | States are deterministic, not estimated from returns |
| `garch_null` | Conditional variance dynamics | One registered parameterization |
| `stable_ar` | Planted stable dependence; true TIME/STATE nulls | One effect magnitude |
| `time_ar` | Year-varying dependence; true STATE nulls | Fixed calendar changes, not arbitrary change-point inference |
| `state_ar` | State-varying dependence; true TIME nulls | Fixed exogenous states |
| `bid_ask_bounce` | Measurement-induced return dependence | Diagnostic only; no registered null-size/power success criterion |
| `student_t5_null` | Heavy-tailed martingale null | Independent hours; no heavy-tail-plus-GARCH combination |
| `volatility_break_null` | Deterministic variance breaks | Independent innovations; no combined persistent dynamics |
| `irregular_null` | Isolated holes and long gaps, exact hours, segment resets | Underlying returns are IID |
| `asynchronous_null` | Different asset supports and exact-intersection expectation | Underlying returns are IID; production cross-asset join is deferred |

Each DGP has 2,000 calibration outer replications and a separately reserved 2,000-replication holdout. Six slots and 4,999 requested inner draws imply 132,000 scheduled outer-slot tasks and up to 659,868,000 inner draws per suite; unavailable originals are recorded without inner draws. Preserve size ≤0.075, registered power ≥0.80, and invalidity ≤0.01. The aggregation code compares point rates with the thresholds and reports Wilson intervals; it does not require the upper Wilson bound itself to fall below 0.075. Do not silently change that rule.

Inspected engineering checks include:

- `tests/test_dependent_wild_bootstrap_v2.py`: dense kernel/factor oracle; exact-time meat; unrestricted and restricted OLS oracle; Wald calculation; deterministic replay; invalid-draw accounting; invalid geometry; bounded fixtures.
- `tests/test_ams_dep_v2_synthetic.py`: 10,000-row regular cases; 9,680-row irregular masks; distinct asynchronous supports; heavy-tail/variance sanity checks; planted AR directions. These are sanity checks, not proofs of DGP distributions or inferential size.
- `tests/test_ams_dep_v2_shard_planner.py` and `tests/test_ams_dep_v2_calibration_runner.py`: complete task assignment and freeze/guard checks.
- `tests/test_ams_dep_v2_aggregation.py`: true-null accounting distinct from power and invalidity failures.
- `tests/test_ams_dep_release_gate.py`: calibration-only permissions; holdout and empirical prerequisites.

The old `_proposed.json` remains intentionally referenced by engineering planner tests. Its unauthorized status should not be confused with the separate frozen execution specification.

## 5. Bounded gap register and review requirements

These are proposals, not additions to the running/frozen suite.

| Gap | Concrete next artifact | Closure / rejection condition | Required review |
| --- | --- | --- | --- |
| G1: exact score-level theory | Derivation for restricted residuals, stochastic x, year/state interactions, segment centering, joint Wald and covariance consistency | Identify a theorem and verify each assumption, or explicitly retain an engineering-only claim | Statistical-method review; a method change requires versioning |
| G2: combined stresses | Separate prospective specification for gaps plus GARCH and variance breaks plus dependence; retain matched no-gap/no-break comparisons | All cases and criteria fixed before output; retain every failure | New experiment/version decision; do not append to V2 |
| G3: segment geometry | Specification for unequal/short segments and dependence persisting across an observation gap; distinguish genuine process reset from missing data | Demonstrate intended boundary treatment and quantify its error within the registered future design | Statistical and pipeline review before execution |
| G4: generated states and eligibility | Full synthetic price/bar history through unchanged AMS-V1, 744-bar warm-up, state eligibility, return endpoints, year labels and exact joins | Provenance/timing/support checks plus approved inferential checks; protected reads denied | Existing mandatory full-pipeline gate and separate empirical approval |
| G5: source qualification | Add explicit slope-versus-variance scope to the BJT citation; retain Rho–Shao as a different algorithm | No blanket bootstrap-validity claim; precise estimator and assumptions named | Documentation review; no inference change needed |
| G6: stale status prose | Short dated reconciliation pointing older packet/PR text to the machine gate, frozen spec and ratification record | Historical decisions preserved; current stage unambiguous | Documentation-only maintenance; no gate mutation |

G4 is already a repository blocker, not a newly invented requirement. G2–G3 are coverage proposals to be adjudicated prospectively, not automatic reasons to stop or modify the authorized frozen calibration. G1 can remain unresolved after this literature work; simulations provide bounded evidence, not a general theorem.

## 6. Completion and handoff

| Playbook criterion | Outcome |
| --- | --- |
| Verify repository and allowed scope | Complete at pinned SHA |
| Deduplicate R01 and relevant literature | Complete for current method documents; limits stated |
| Obtain/read source and needed supplement | Shao full article and supplement obtained; follow-up review scope and access limits explicit |
| Map relevant assumptions to actual implementation | A01–A11 above |
| Inventory synthetic checks and gaps | Eleven cases, inspected tests, G1–G6 |
| Decision memo with sources and actions | Complete; exact-method validity unresolved, no release authorization |

Next **playbook literature task**: R02 order-flow replication specification and data-feasibility review. R04 follows as a future-phase feasibility review. Neither authorizes market-data experiments. The separate **repository execution task** remains its frozen calibration workflow and eventual artifact/gate assessment.

This report changes no repository authority and does not reopen the closed OHLCV research program.

## Source snapshot fingerprints

SHA-256 of retrieved PDF bytes (for source-version identification, not validation):

- Shao article: `133f712d8c2b708a6897facdde14b465a5c36a5652dab9ea3c7015291534ff9a`
- Shao supplement: `0295a9812b7991e2112e98d32dab5a5107ec31e81ff32250a1883b0a7cddd4c6`
- Rho–Shao regression accepted manuscript: `7ef25c3177d8be3a779fd8b9579135685aa51dcc027def69c99cda5370baf180`
- Rho–Shao unit-root arXiv PDF: `fdc1ec5cd74b16ea32a750fd931a6e2cdf1e35c8c2c7264d7d1ccdbd247c876a`

Full source URLs above remain the authoritative publications. Copyrighted papers are not republished as part of this deliverable.
