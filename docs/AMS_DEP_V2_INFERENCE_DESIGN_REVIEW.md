# AMS-DEP V2 Inference Design Review Packet

## Status

**DESIGN REVIEW ONLY — NOT FROZEN — NO V2 EXECUTION AUTHORIZED**

This packet exists because AMS-DEP synthetic calibration V1 failed its
predeclared false-rejection screen. It is a prospective design document for
independent statistical review.

It does not inspect BTCUSDT/ETHUSDT dependence results, does not alter V1, and
does not authorize a new synthetic run.

## Problem to solve

V1 used OLS, exact-time Bartlett HAC with maximum lag 168 hours, joint Wald
statistics and asymptotic chi-square reference distributions.

The implementation passed its software oracles, but the completed fixed
7,000-replicate synthetic experiment produced excessive false rejection under
multiple true-null DGPs.

Therefore the V2 problem is not "find significance." It is:

> construct an inference procedure with acceptable finite-sample size under
> predeclared dependence/heteroskedasticity environments while retaining
> useful power against the registered alternatives.

The V1 acceptance standards remain binding:

- family-level erroneous-rejection rate <= 0.075;
- registered strong-alternative power >= 0.80 per asset/target;
- invalid-fit fraction <= 0.01.

These thresholds are not candidates for revision.

## Primary methodological principle from Lo / Lo-MacKinlay

Lo and MacKinlay's finite-sample work on variance-ratio tests used Monte Carlo
experiments to study the size and power of a statistic before relying on its
empirical significance.

The project applies the same methodological principle here:

1. define the inferential procedure;
2. freeze the finite-sample calibration experiment;
3. measure size and power on synthetic data;
4. reject a procedure that fails its calibration gate;
5. expose a procedure to market data only after calibration and separate
   release approval.

This does not imply that Lo or MacKinlay prescribed the specific bootstrap or
fixed-b methods considered below.

## Candidate A — Dependent Wild Bootstrap (DWB)

Relevant methodological source: Xiaofeng Shao, "The Dependent Wild Bootstrap,"
Journal of the American Statistical Association 105(489), 218–235.

### Why it is a serious candidate

The DWB was developed for dependent time series and extends wild-bootstrap
logic to serially dependent observations. It is attractive here because the
project must tolerate heteroskedasticity/autocorrelation and may later face
irregular/gapped time grids.

### Proposed role

For each registered DEP/TIME/STATE restriction:

1. estimate the null-restricted model;
2. construct null-imposed residual/score objects;
3. generate a dependent multiplier sequence according to a prospectively
   fixed kernel/bandwidth rule;
4. form bootstrap pseudo-samples or bootstrap score statistics while
   preserving the fixed regressors/state/year labels;
5. re-estimate required nuisance quantities in each bootstrap replicate;
6. compute the same registered test statistic;
7. obtain a finite-sample bootstrap p-value from the bootstrap null
   distribution;
8. feed exactly six p-values into the unchanged Holm family.

### Unresolved items that MUST be frozen before implementation/results

- exact DWB variant;
- multiplier covariance kernel;
- multiplier bandwidth and whether it is fixed or sample-size based;
- residual-versus-score bootstrap construction;
- null-imposition formula for 7-, 4- and 2-restriction tests;
- centering/studentization;
- handling of declared continuity segments;
- whether multiplier processes reset at segment boundaries;
- number of bootstrap replications;
- deterministic RNG and seed hierarchy;
- finite-bootstrap p-value convention, including +1 correction if used;
- nuisance re-estimation in every bootstrap replication;
- invalid-bootstrap-replicate policy.

No choice may be made after observing BTC/ETH results.

## Candidate B — Fixed-b HAC inference

Relevant methodological source: Kiefer and Vogelsang, "A New Asymptotic
Theory for Heteroskedasticity-Autocorrelation Robust Tests," Econometric
Theory 21(6), 1130–1164.

### Why it is a serious candidate

Traditional HAC asymptotics treat bandwidth as small relative to sample size.
Fixed-b asymptotics explicitly retain the bandwidth/kernel choice in the
limiting distribution. That is relevant because V1 uses a long 168-hour
bandwidth and exhibited over-rejection.

### Proposed role

Retain a HAC-style covariance/test framework but replace naive chi-square
critical values with a prospectively specified fixed-b reference procedure.

### Unresolved items that MUST be frozen before implementation/results

- exact fixed-b statistic and critical-value source;
- how multiple year/continuity segments map to the fixed-b theory;
- whether one b ratio is defined globally or per segment;
- treatment of unequal real-data segment lengths;
- kernel and bandwidth policy;
- joint-restriction critical values for 7/4/2 restrictions;
- interaction with the six-test Holm family;
- validity under the project's heteroskedastic and state-selection structure.

The segmented/gapped design makes theoretical transfer nontrivial. Fixed-b is
therefore a review candidate, not an automatic solution.

## Candidate C — Revised conventional HAC

Possible components include bandwidth changes, prewhitening or other HAC
small-sample corrections.

### Status

**LOWER PRIORITY FOR V2.**

V1 already demonstrated that a conventional HAC/Wald implementation can have
poor finite-sample size in the registered environments. Merely selecting a
different bandwidth after seeing V1 could become calibration overfitting.

A revised conventional HAC method should enter V2 only if an independent
review supplies a clear theoretical rationale and freezes all tuning choices
before results.

## Prospective method-selection rule

V2 must not become an unrestricted search over inference procedures.

Before any V2 synthetic run, the independent review must select **one primary
procedure** and optionally **one diagnostic comparator**.

Selection must be based on:
- theoretical suitability for serial dependence and heteroskedasticity;
- compatibility with declared continuity segments and missing timestamps;
- ability to impose composite null restrictions correctly;
- reproducibility;
- computational feasibility for a frozen calibration;
- lack of dependence on actual BTC/ETH outcomes.

The chosen method and all tuning choices must then be frozen in Git.

If the selected V2 method fails its synthetic gate, V2 remains failed. The
project must not silently switch to the diagnostic comparator and call that
V2 a pass.

## V2 synthetic calibration suite

V1 cases MUST remain:
1. iid_null;
2. heteroskedastic_null;
3. garch_null;
4. stable_ar;
5. time_ar;
6. state_ar;
7. bid_ask_bounce.

To reduce method-tuning to the original V1 cases, V2 should also freeze
additional stress DGPs before results.

Recommended additions for independent review:

### Heavy-tail null
- zero conditional-mean dependence;
- Student-t innovations with prospectively fixed degrees of freedom and
  variance normalization;
- tests sensitivity to crypto-like tail behavior without inserting an edge.

### Volatility-break null
- zero conditional-mean dependence;
- deterministic variance shifts across predeclared time blocks;
- tests whether changing scale is misread as changing signed dependence.

### Irregular-observation / continuity stress
- generated observations with prospectively fixed missing-hour patterns;
- exact timestamps and declared segments;
- verifies that the inference implementation does not compress time or bridge
  gaps.

### Asynchronous cross-asset stress
- needed for later cross-asset diagnostics, not necessarily for the six
  within-asset primary tests;
- verifies exact-time join and missingness behavior before cross-asset
  empirical release.

The exact DGP parameters and RNG seeds must be committed before V2 output.

## Calibration and method-selection separation

Do not use the same synthetic realization both to tune a method and certify
it.

Preferred structure:

### Engineering set
Used only to verify code/oracles and detect implementation defects.
No pass/fail statistical claim.

### Calibration set
Fixed before results and used for the V2 size/power gate.

### Optional synthetic holdout set
If method tuning is unavoidable during implementation, a separately seeded
holdout suite must remain unopened until tuning stops. The holdout design and
seed schedule must be frozen in advance.

A method that is changed after calibration-set results requires a new version.

## Full-pipeline requirement before market-data release

Passing the numerical-core V2 gate is necessary but not sufficient.

Before actual BTC/ETH AMS-DEP execution, a later synthetic/integrity stage
must exercise:

- the real AMS-V1 state-construction code on generated price/volume paths;
- the 744-bar warm-up behavior;
- complete-state row selection;
- the real continuity-segment machinery;
- return endpoint availability;
- year/state support thresholds;
- all exclusion accounting;
- exact BTC/ETH join logic for cross-asset diagnostics;
- protected-partition read blocking.

This stage must prove that the empirical runner cannot silently alter the
sample relative to the preregistration.

## Multiplicity

The primary family remains exactly:

1. BTC_DEP
2. BTC_TIME
3. BTC_STATE
4. ETH_DEP
5. ETH_TIME
6. ETH_STATE

Holm family-wise control remains the default unless an independent review
identifies a defect in its implementation. A change in multiplicity procedure
requires explicit prospective justification and a new version; multiplicity
may not be weakened to obtain a pass.

## Interpretation boundary

Even a perfectly calibrated V2 can only support statements about registered
statistical dependence/heterogeneity in reused Development data.

It cannot by itself establish:
- a profitable edge;
- a causal market-ecology mechanism;
- AMH as "true";
- Validation eligibility;
- paper/live authorization.

Statistical dependence must later be connected to a separately registered
economic mechanism and executable strategy specification.

## Required independent-review questions

An independent statistical reviewer should answer, in writing:

1. Is DWB suitable for this regression/restriction structure and segmented
   time-series design?
2. If yes, which exact DWB construction and bandwidth/kernel rule should be
   frozen?
3. If fixed-b is preferred, how are segmented/gapped observations handled
   without violating the theory?
4. Does the six-test Holm family remain appropriate given cross-asset
   dependence?
5. Are the retained/additional synthetic DGPs sufficient to test the intended
   failure modes?
6. Are <=0.075 size, >=0.80 power, and <=0.01 invalid-fit screens acceptable
   engineering release criteria?
7. What additional failure conditions should block empirical release?
8. Does the final frozen procedure preserve exact timing/continuity and avoid
   hidden model selection?

The proposer/implementer may prepare code and tests after design freeze but
may not sign the final independent release approval.

## Current decision

**NO V2 EXECUTION YET.**

Next gate:
1. independent statistical review of this packet;
2. select/freeze one V2 primary inference method and all tuning choices;
3. freeze V2 synthetic DGPs/seeds/replication counts;
4. implement with independent numerical oracles;
5. run the synthetic gate exactly once under the frozen version;
6. retain pass or fail;
7. only after a pass, complete the full-pipeline synthetic/integrity gate and
   separate empirical-release review.
