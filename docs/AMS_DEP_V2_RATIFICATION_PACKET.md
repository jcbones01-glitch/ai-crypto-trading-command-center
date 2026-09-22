# AMS-DEP V2 independent ratification packet

## Status

**READY FOR INDEPENDENT RATIFICATION — NO SYNTHETIC EXECUTION AUTHORIZED YET**

This packet is the final follow-up to the external/user-supplied decision:

`APPROVE_V2_DESIGN_AFTER_SPECIFIED_CHANGES`

The implementer has completed the requested engineering response and
prospectively specified the previously ambiguous details. The implementer does
not ratify its own choices.

The reviewer must inspect the current `adaptive-markets-research` head and
record its exact SHA in the review. Do not rely on an older SHA quoted in prior
documents.

## 1. Prior independent decision

The supplied review selected, for synthetic-only V2 work:

- null-imposed restricted-residual dependent wild bootstrap;
- residual centering within declared continuity segments;
- Gaussian dependent multipliers;
- Parzen covariance kernel using actual integer-hour separation;
- segment-specific
  `ell_s = max(2, n_s^(1/5))`;
- zero multiplier covariance across declared segments;
- unrestricted OLS refit and exact-time Parzen HAC/Wald statistic per draw;
- 4,999 requested bootstrap draws;
- `p=(1+exceedances)/5000`;
- invalid draws never redrawn and conservatively counted as exceedances;
- deterministic SeedSequence hierarchy;
- unchanged six-slot Holm family;
- Python 3.12.14, NumPy 2.2.6, SciPy 1.15.3, float64, one BLAS thread;
- retained V1 DGPs plus heavy-tail, variance-break, irregular-time and
  asynchronous-time stresses;
- 2,000 calibration outer replications per DGP;
- separately reserved unopened 2,000-replication holdout per DGP;
- unchanged engineering thresholds:
  - family false rejection <= 0.075;
  - target power >= 0.80;
  - invalidity <= 0.01.

The prior review did **not** authorize BTC/ETH empirical execution.

## 2. Exact implementation/proposal files to inspect

Mandatory:

- `docs/AMS_DEP_V2_CONDITIONAL_REVIEW_RESPONSE.md`
- `docs/AMS_DEP_V2_NUMERICAL_CONTRACT.md`
- `research/experiments/ams_dep_synthetic_core_v2_proposed.json`
- `src/research_core/dependent_wild_bootstrap_v2.py`
- `tests/test_dependent_wild_bootstrap_v2.py`
- `docs/AMS_DEP_V2_RESOURCE_SHARDING_PLAN.md`
- `research/scripts/plan_ams_dep_v2_shards.py`
- `tests/test_ams_dep_v2_shard_planner.py`
- `docs/AMS_DEP_V2_STOCHASTIC_REGRESSOR_REVIEW.md`
- `research/governance/ams_dep_release_gate_v1.json`
- `src/research_core/release_gate.py`
- `tests/test_ams_dep_release_gate.py`

Context:

- `research/experiments/AMS_DEP_SYNTHETIC_CORE_V1_RESULT.md`
- `research/experiments/AMS_DEP_V1_FAILURE_DIAGNOSTIC_RESULT.md`
- `docs/AMS_DEP_V2_FORMULA_SOURCE_RECOVERY.md`
- `docs/AMS_DEP_V2_THEORY_GAP_MATRIX.md`
- Issue #43
- Issue #44
- PR #42

## 3. Current engineering evidence

Latest verified engineering state before this packet:

- engineering workflow run: `35456903336`
- release-gate PR run: `35456905962`
- both: SUCCESS
- full regression suite: **183 passed**
- release-gate focused suite: **6 passed**
- engineering artifact:
  - ID: `10587774686`
  - name: `ams-dep-v2-engineering-only`
  - digest:
    `sha256:af6dc7622da0f313d37071766ce8fa29fa99accb25cbae7d5d56440bc4a4ff3e`

The workflow output explicitly reports:
- `calibration_run: false`;
- `market_data_accessed: false`;
- RNG-free shard planning;
- no Validation/OOS access.

Intermediate CI failures while the governance JSON and tests were being changed
are preserved in Actions history. The final head is the evidence that matters;
no failed run has been deleted or rewritten.

## 4. Exact proposed DWB mechanics for ratification

### Null imposition

For each DEP/TIME/STATE restriction:

1. keep the unrestricted 14-column design intact;
2. impose the registered zero-coefficient restriction by fitting only the free
   columns;
3. obtain the restricted fitted value and residual;
4. center residuals separately within each declared continuity segment;
5. keep X, year labels, state labels, eligible rows and exact-hour coordinates
   fixed;
6. construct
   `y* = yhat_restricted + centered_residual * W`.

Each bootstrap draw refits unrestricted OLS and recomputes the same Parzen
studentized Wald statistic used for the observed sample.

### Parzen multiplier covariance

For rows i,j in the same segment:

`z = abs(hour_i-hour_j)/ell_s`

`K(z)=1-6z^2+6z^3` for `0<=z<=1/2`

`K(z)=2(1-z)^3` for `1/2<z<1`

`K(z)=0` for `z>=1`.

`ell_s=max(2,n_s^(1/5))` hours, unrounded.

Across segments covariance is exactly zero.

Missing rows do not compress hour coordinates.

### Factorization

- lower-banded covariance representation;
- `scipy.linalg.cholesky_banded(lower=True)`;
- standard Gaussian innovations;
- no jitter;
- no eigenvalue clipping;
- no PSD projection;
- factorization failure is explicit failure.

### Studentization

Observed and bootstrap Wald statistics use the **same Parzen geometry**.

No V1 Bartlett/168 covariance remains in V2 inference.

### Invalidity

- exactly 4,999 requested draws;
- no redraw;
- invalid/nonfinite/negative bootstrap statistic counts as an exceedance;
- p-value denominator remains 5,000;
- cell bootstrap-invalid fraction >1% fails;
- original invalid fit remains unavailable/failing, not silently replaced.

## 5. Exact new stress DGPs proposed for ratification

The seven V1 scientific DGP definitions are retained with new V2 seed
namespaces.

Four additions:

### Student-t5 martingale null

- df=5;
- marginal SD normalized to 0.01;
- cross-asset correlation 0.6;
- common chi-square scale per hour;
- no conditional-mean predictability.

### Deterministic volatility-break martingale null

Per eligible year, SD blocks:

- 0..499: 0.005
- 500..999: 0.01
- 1000..1499: 0.03
- 1500..2000: 0.01

Burn-in SD 0.01.

Cross-asset correlation 0.6.

### Irregular-time null

Start from IID null, then apply identical asset masks:

- missing-hour blocks [720,744) and [1440,1464);
- isolated missing offsets:
  101, 307, 509, 911, 1117, 1723, 1901.

A regression row t is eligible only if both endpoints t and t+1 exist.
Long blocks create a new declared segment afterward; isolated holes do not
compress time.

### Asynchronous two-asset null

- BTC removes hour offsets divisible by 97;
- ETH removes offsets divisible by 89;
- ETH additionally removes [1000,1024);
- within-asset regression pairs require both endpoints;
- exact cross-asset join is intersection by actual hour only;
- never nearest-match or row-index-match.

The exact JSON is authoritative if ratified.

## 6. Seed namespaces proposed for ratification

Bootstrap roots:

- engineering: `2026092001`
- calibration: `2026092002`
- holdout: `2026092003`

Synthetic data roots:

- calibration: `2026092102`
- holdout: `2026092103`

Bootstrap coordinate:

`[root,2,dgp_index,outer_index,asset_index,hypothesis_index,bootstrap_index,segment_ordinal]`

No calibration or holdout RNG has been instantiated by the shard planner.

## 7. Deterministic sharding/resource plan

Per suite:

- 11 DGPs;
- 2,000 outer reps;
- 2 assets;
- 3 hypotheses;
- 132,000 outer-slot tasks;
- 4,999 requested draws per task;
- 659,868,000 requested inner draws.

Proposal:

- 128 deterministic shards;
- canonical task index:
  `(((dgp*2000)+outer)*2+asset)*3+hypothesis`;
- `shard_id = task_index % 128`;
- 32 shards have 1,032 slot tasks;
- 96 shards have 1,031;
- no shard scheduling affects RNG identity.

The planner imports no RNG/numerical bootstrap library and generated the
verified engineering artifact with:
- `rng_instantiated: false`;
- `calibration_run: false`.

## 8. Stochastic lagged-return predictor caveat

Additional literature review found direct precedent for fixed-design/wild
bootstrap in dynamic regressions:

- Gonçalves & Kilian (2004), autoregressions under unknown conditional
  heteroskedasticity, DOI `10.1016/j.jeconom.2003.10.030`;
- Godfrey (2011), OLS with lagged dependent regressors,
  DOI `10.1111/j.1468-0084.2010.00630.x`;
- Hafner & Herwartz (2009), fixed-design wild bootstrap for VAR parameter
  restrictions under conditional heteroskedasticity,
  DOI `10.1111/j.1467-9574.2009.00424.x`;
- Brüggemann, Jentsch & Trenkler (2016), bootstrap inference in VARs with
  conditional heteroskedasticity,
  DOI `10.1016/j.jeconom.2015.10.004`.

This narrows—but does not eliminate—the transfer risk.

No source was found that directly proves the exact AMS-DEP combination of
stochastic return predictor, segmented exact-time DWB, Parzen studentization
and 7/4/2 restrictions.

The project therefore relies on prospectively frozen Monte Carlo calibration
and holdout as engineering release evidence, not a claim of a turnkey theorem.

## 9. Ratification questions

The independent reviewer must answer all seven:

1. **Studentization:** Ratify same Parzen covariance/studentization for observed
   and bootstrap Wald statistics?
2. **Stress DGPs/seeds:** Ratify the exact four new DGP definitions, masks,
   slots and reserved seed namespaces in the proposed JSON?
3. **Invalidity:** Ratify conservative no-redraw invalid accounting and the
   per-cell/per-original 1% failure rule?
4. **Holdout:** Ratify calibration first, then separately authorized unopened
   holdout, with any calibration-driven method change creating V3?
5. **Segmented RNG/numerics:** Ratify exact segment resets, covariance
   construction, Cholesky rule and numerical tolerances?
6. **Stochastic predictor:** Ratify fixed-X restricted-residual DWB as an
   acceptable synthetic method to test through the frozen calibration/holdout,
   despite the absence of a theorem for the exact full design?
7. **Resource plan:** Ratify the 128-shard deterministic execution architecture
   without reducing statistical workload?

## 10. Required decision token

Return exactly one:

- `RATIFY_V2_FREEZE_FOR_SYNTHETIC_CALIBRATION`
- `REQUIRE_CHANGES_BEFORE_V2_FREEZE`
- `REJECT_V2_DWB_DESIGN`

If requiring changes, enumerate them precisely before any V2 output.

## 11. What ratification would authorize

A `RATIFY_V2_FREEZE_FOR_SYNTHETIC_CALIBRATION` decision would authorize only:

1. rename/freeze the proposed V2 spec without changing its scientific content;
2. mark independent design approval and specification freeze true;
3. create the guarded calibration runner;
4. authorize **synthetic calibration only**;
5. run the frozen calibration and retain pass/fail.

It would NOT authorize:
- holdout automatically;
- BTC/ETH AMS-DEP results;
- Validation/OOS;
- strategy P&L;
- paper trading;
- live trading.

The holdout requires a passing unchanged calibration and a separate execution
authorization. Empirical market-data release remains behind full-pipeline
integrity and a separate approval.

## 12. Independence statement required from reviewer

The reviewer must state:
- whether they designed or implemented the current V2 code;
- whether they inspected actual BTC/ETH AMS-DEP outcomes;
- whether they inspected Validation/OOS;
- exact repository branch/head SHA reviewed;
- exact decision token.

If independence cannot be represented truthfully, do not ratify.
