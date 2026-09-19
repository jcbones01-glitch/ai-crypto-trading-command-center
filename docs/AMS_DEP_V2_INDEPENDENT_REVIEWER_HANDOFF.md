# AMS-DEP V2 Independent Reviewer Handoff

## Purpose

This is the compact handoff for the independent statistical reviewer required
by Issue #44.

It collects the evidence that now exists, the decisions still open, and the
boundaries that may not be crossed.

## Current evidence chain

### V1 fixed calibration

- frozen specification commit:
  `2dd1543f654b5a605a902ce2b3cf98c70c9755b1`
- completed run: `35434647946`
- artifact ID: `10582128182`
- result:
  `research/experiments/AMS_DEP_SYNTHETIC_CORE_V1_RESULT.md`

V1 failed its predeclared finite-sample size gate.

Family false-rejection rates:
- IID null: 12.6%
- heteroskedastic null: 24.7%
- GARCH null: 14.3%
- stable-AR true TIME/STATE nulls: 11.6%
- time-AR true STATE nulls: 7.5%
- state-AR true TIME nulls: 12.3%

Registered strong-alternative power was 100% in the planted target tests.
Invalid-fit rates were zero.

### Frozen V1 failure diagnostic

- diagnostic plan:
  `docs/AMS_DEP_V1_FAILURE_DIAGNOSTIC_PLAN.md`
- frozen plan commit:
  `e490b1fb5a8da8cbfaaceebf96ea1979896932a7`
- executing commit:
  `8083c714cdbc725fb683e1ef07649dea50106636`
- workflow run:
  `35435551922`
- artifact:
  `ams-dep-v1-failure-diagnostic-v1`
- artifact ID:
  `10581624694`
- result:
  `research/experiments/AMS_DEP_V1_FAILURE_DIAGNOSTIC_RESULT.md`

### Diagnostic findings

The production OLS/HAC implementation matched an independently coded,
unscaled normal-equation OLS + direct Bartlett-lag-sum covariance oracle within
the frozen 1e-10 tolerances.

Conclusion:
**NO_ORACLE_MISMATCH_OBSERVED.**

Family false-rejection sensitivity:

| Null DGP | HAC 0 | HAC 24 | HAC 168 |
| --- | ---: | ---: | ---: |
| IID | 3.0% | 5.1% | 12.6% |
| Heteroskedastic | 4.5% | 5.7% | 24.7% |
| GARCH | 3.4% | 4.7% | 14.3% |

At lag 168, empirical Wald 95th-percentile / chi-square 95th-percentile ratios
were materially above one, especially for DEP/TIME and the heteroskedastic
null. Estimated coefficient variances also understated across-replication
variance, especially at lag 168.

Allowed diagnostic conclusions:
- NO_ORACLE_MISMATCH_OBSERVED
- BANDWIDTH_SENSITIVITY_OBSERVED
- ASYMPTOTIC_REFERENCE_MISMATCH_OBSERVED
- COVARIANCE_UNDERESTIMATION_OBSERVED

## What the diagnostic DOES NOT authorize

The diagnostic does **not** authorize changing the primary HAC lag from 168
to 24.

Lag 24 was inspected after V1 failed. Selecting it as the new primary rule
solely because the diagnostic looked better would be post-result method
selection.

Any conventional-HAC V2 requires an independent theoretical rationale for its
bandwidth rule, fixed prospectively before new calibration outcomes.

## Primary reviewer question

Given:

1. verified implementation equivalence to an independent HAC oracle;
2. large finite-sample distortion at L=168;
3. much smaller distortion at diagnostic L=0/24;
4. heteroskedastic/GARCH environments;
5. composite 7/4/2 Wald restrictions;
6. five declared synthetic continuity segments and later irregular empirical
   segments;
7. future endogenous AMS-V1 row/state selection;
8. a fixed six-test Holm family;

what exact inference procedure should be frozen for AMS-DEP V2?

## Candidate ranking for REVIEW, not approval

### Candidate 1 — Null-imposed dependent wild bootstrap

Why it deserves first review:
- directly targets finite-sample null calibration;
- designed for dependent observations;
- potentially handles heteroskedasticity without relying solely on chi-square
  approximation;
- does not require pretending the diagnostic lag-24 result was prospectively
  selected.

Unresolved:
- multiplier kernel and bandwidth;
- null imposition;
- score versus residual construction;
- segment resets;
- nuisance re-estimation;
- bootstrap statistic/studentization;
- finite-bootstrap p-value formula;
- replication count;
- exact seed hierarchy.

### Candidate 2 — Fixed-b HAC inference

Why it deserves review:
- directly addresses the fact that conventional HAC reference distributions
  can depend on non-negligible bandwidth;
- the V1 diagnostic implicates large bandwidth/reference-distribution
  mismatch.

Unresolved:
- mapping fixed-b theory to multiple segments;
- unequal future segment lengths;
- exact joint-restriction critical values;
- integration with state/year interactions and later row selection.

### Candidate 3 — Prospectively justified conventional HAC rule

Why it remains possible:
- diagnostic lag 24 behaved well on the three tested null DGPs.

Why it cannot be adopted directly:
- lag 24 is now observed evidence;
- choosing it because it passed these DGPs would be tuning;
- a new rule must arise from a priori bandwidth theory or a fixed
  sample-size-based formula, then face a new untouched synthetic gate.

## Required reviewer output

The reviewer must produce a signed-off design record containing:

1. selected primary inference procedure;
2. rejected alternatives and reasons;
3. exact mathematical algorithm;
4. exact null-restriction implementation;
5. segment/gap treatment;
6. nuisance re-estimation policy;
7. kernel/bandwidth or resampling rule;
8. bootstrap/fixed-b replication or critical-value machinery;
9. deterministic RNG/seed hierarchy if applicable;
10. six-test multiplicity treatment;
11. invalid-fit/invalid-bootstrap handling;
12. exact package/version requirements;
13. retained V1 DGPs;
14. all added V2 stress DGPs;
15. calibration-set and optional synthetic-holdout separation;
16. unchanged release thresholds:
    - family false rejection <= 0.075
    - registered target power >= 0.80
    - invalid-fit fraction <= 0.01
17. additional blockers, if any;
18. explicit statement that actual BTC/ETH AMS-DEP outcomes were not inspected.

## Recommended V2 stress suite

Retain all V1 DGPs and preregister before output:

- heavy-tail martingale null;
- deterministic volatility-break martingale null;
- irregular-observation / declared-continuity null;
- asynchronous cross-asset timing stress for future cross-asset diagnostics;
- full endogenous AMS-V1 state-construction/row-selection integrity stage.

Exact parameters must be frozen before output.

## Required separation of synthetic data

To avoid calibrating and certifying on the same random draws:

- **engineering fixtures:** small deterministic examples for code/oracle tests;
- **calibration suite:** frozen Monte Carlo seeds for size/power gate;
- **synthetic holdout:** separately frozen unopened seeds if any tuning occurs
  before final method freeze.

If the method changes after calibration outcomes are inspected, it is a new
version and the prior evidence remains.

## Andrew Lo / Lo-MacKinlay methodology

The governing principle from Lo/Lo-MacKinlay is not a specific bootstrap
algorithm. It is the discipline of examining finite-sample size and power
before trusting empirical significance.

The reviewer should preserve that principle:
- reject poorly calibrated tests;
- distinguish statistical dependence from profit;
- retain failures;
- prevent data snooping;
- do not expose protected empirical data while test design remains fluid.

## Authority boundary

The project author/implementer may prepare designs and code after freeze but
must not self-sign the independent statistical release approval.

Until that approval and a passing frozen V2 calibration:

**NO V2 EMPIRICAL EXECUTION.**
**NO BTC/ETH AMS-DEP RESULTS.**
**NO VALIDATION/OOS.**
**NO STRATEGY P&L OR TRADING.**
