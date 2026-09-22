# AMS-DEP V2 Formula-Level Source Recovery Audit

## Status

**SOURCE RECOVERY / METHOD AUDIT — NOT V2 APPROVAL**

This document strengthens the independent-review packet for Issue #44 by
recording legitimate open or author-hosted full-text sources that permit
formula-level inspection of leading V2 method families.

No statistical method is selected here. No V2 synthetic calibration or
BTC/ETH empirical execution is authorized.

## 1. Shao (2010) — Dependent Wild Bootstrap

Primary publication:
- Xiaofeng Shao, "The Dependent Wild Bootstrap," JASA 105(489), 218–235.
- DOI: `10.1198/jasa.2009.tm08744`.

Open author-hosted sources verified:
- full paper hosted on Xiaofeng Shao's University of Illinois publication site;
- supplementary material hosted on the same author site.

### Formula-level points recovered

For regularly spaced observations, the DWB introduces auxiliary random
variables (W_t) independent of the data with:
- (E(W_t)=0);
- (operatorname{var}(W_t)=1);
- covariance
  (operatorname{cov}(W_t,W_{t'})=a((t-t')/l)),
  where (a(cdot)) is a covariance kernel and (l) is a bandwidth.

The paper explicitly states that:
- the bandwidth plays a role analogous to block size in block bootstrap
  methods;
- kernel choice and bandwidth determine the induced dependence structure;
- common admissible kernel examples include Bartlett, Parzen and quadratic
  spectral under the paper's positive-definiteness requirement;
- multivariate Gaussian auxiliary draws are a convenient practical
  construction, but the joint distribution is itself a design choice;
- the DWB variance estimator is linked to lag-window / long-run-variance
  estimation;
- bandwidth affects first-order accuracy.

The paper's concluding discussion explicitly identifies bandwidth, covariance
kernel and the joint distribution of (W_t) as practical choices that still
must be made.

### Irregular observations / gaps

The paper explicitly studies irregularly spaced observations and missing
values.

Important nuance for AMS-DEP:
- the paper supports the proposition that DWB can accommodate irregular
  temporal configurations without the same block-partitioning problem as
  block bootstrap methods;
- however, the nonlattice theory in the paper is developed most directly for
  the mean, under a stochastic sampling framework;
- extension to the project's exact multi-parameter regression with
  deterministic year/state interactions, exact-hour continuity segments and
  composite 7/4/2 restrictions is **not automatically established** by this
  result.

Therefore the repository must not replace its exact-time continuity rules
with compressed-row distances merely because DWB supports irregular data.

### Critical bandwidth observation

For regular-lattice smooth-function settings, Shao derives asymptotic
bandwidth rates for variance-estimation MSE under particular conditions.
Those rates are **not a ready-made AMS-DEP bandwidth rule**.

The same paper notes that:
- coverage-optimal behavior need not coincide with MSE-optimal bandwidth;
- bandwidth selection is important in practice;
- no general automatic bandwidth rule is supplied for every irregular
  nonlattice setting.

This reinforces Issue #44's requirement that a V2 DWB bandwidth rule be
prospectively justified rather than selected from the V1 lag-24 diagnostic.

## 2. Kiefer–Vogelsang (2005) — fixed-b HAC

Primary publication:
- Nicholas M. Kiefer and Timothy J. Vogelsang,
  "A New Asymptotic Theory for Heteroskedasticity-Autocorrelation Robust
  Tests," Econometric Theory 21(6), 1130–1164.
- DOI: `10.1017/S0266466605050565`.

Open source verified:
- author-hosted Cornell working-paper version, revised March 2005.

### Formula-level points recovered

The framework holds
(b=M/T), the bandwidth-to-sample-size ratio, fixed while deriving the
asymptotic law.

The paper develops fixed-b asymptotics for familiar HAC robust Wald/F-type and
t-type statistics rather than proposing a completely unrelated statistic.

For multiple restrictions, the paper writes an F-version of a HAC robust Wald
statistic. Therefore fixed-b is relevant in principle to joint restrictions,
not only scalar t-tests.

Most importantly:
- the limiting law is nonstandard;
- it explicitly depends on the kernel and bandwidth;
- fixed-b critical values are therefore part of the test definition;
- kernel and bandwidth materially affect both null size and power.

The paper's simulations and analysis emphasize a size–power trade-off:
different bandwidths/kernels can change both rejection accuracy and power.

### Relevance to AMS-DEP V1

V1 used:
- Bartlett HAC;
- lag 168;
- ordinary asymptotic chi-square reference values.

The V1 diagnostic found severe finite-sample over-rejection at lag 168.

The fixed-b literature therefore directly supports reviewing whether the
reference law must reflect the non-negligible smoothing choice rather than
changing only the covariance estimate.

### Limitation for AMS-DEP

The paper treats stationary/GMM-style settings under its own assumptions.
The repository has:
- five separately declared synthetic continuity segments;
- later unequal empirical continuity segments;
- year/state interactions;
- warm-up and row-selection rules;
- exact-hour gaps;
- potentially endogenous AMS-V1 state labels.

A reviewer must show how these map into the fixed-b theory. The existence of
a multi-restriction F statistic in the paper does not by itself solve the
segmentation problem.

## 3. Sun, Phillips and Jin — fixed-b bandwidth choice

Primary publication:
- Yixiao Sun, Peter C. B. Phillips and Sainan Jin,
  "Optimal Bandwidth Selection in Heteroskedasticity–Autocorrelation Robust
  Testing," Econometrica 76(1), 175–194.
- DOI: `10.1111/j.0012-9682.2008.00822.x`.

A freely accessible working-paper version is available through the University
of California eScholarship repository.

The paper explicitly distinguishes:
- small-b asymptotics, with standard reference laws;
- fixed-b asymptotics, with nonstandard reference laws;
and studies bandwidth selection using a loss involving type-I and type-II
errors.

Project implication:
bandwidth selection for a **test** is not identical to choosing a bandwidth
that optimizes long-run-variance estimator MSE.

This makes a direct post-hoc choice of lag 24 especially inappropriate:
the project's inference rule must be frozen as a testing procedure, not
chosen because one diagnostic lag happened to exhibit favorable size.

## 4. Regression-specific adjacent literature

### Zhou and Shao (2013)

- "Inference for Linear Models with Dependent Errors,"
  JRSS Series B 75(2), 323–343.
- DOI: `10.1111/j.1467-9868.2012.01044.x`.
- Full author-hosted PDF is available from Xiaofeng Shao's University of
  Illinois site.

This paper develops inference for linear models with fixed regressors and
weakly dependent errors using a self-normalized approach and simulation-based
critical values.

It is relevant because it confirms that dependent-error regression inference
requires design-specific treatment; however, it is a different inferential
architecture from DWB and fixed-b HAC and is **not added as an automatic V2
candidate**.

### Rho and Shao (2015)

- "Inference for Time Series Regression Models With Weakly Dependent and
  Heteroscedastic Errors,"
  Journal of Business & Economic Statistics 33(3), 444–457.
- DOI: `10.1080/07350015.2014.962698`.

Author/institutional records describe a self-normalized regression method for
weakly dependent errors with changing unconditional variances and use a wild
bootstrap to approximate a nonpivotal limiting distribution.

Again, this is useful evidence that regression bootstrap/studentization must
be designed around the target statistic. It does not authorize importing that
procedure into AMS-DEP without a new prospective design decision.

## 5. Bravo–Godfrey status

Bravo and Godfrey:
- "Bootstrap HAC Tests for Ordinary Least Squares Regression,"
  Oxford Bulletin of Economics and Statistics 74(6), 903–922.
- DOI: `10.1111/j.1468-0084.2011.00671.x`.

Verified authoritative abstract/metadata sources state that the method uses:
- OLS coefficient inference;
- moving block bootstrap;
- quasi-estimators;
- a consistent asymptotic covariance estimator;
- Monte Carlo evaluation of finite-sample size and power.

A freely accessible formula-level author manuscript was not recovered during
this audit.

Therefore Bravo–Godfrey remains a legitimate comparator but **not
formula-certified in the repository**.

## 6. Consequences for Issue #44

The source recovery narrows what the independent reviewer must decide.

### DWB can no longer be specified merely as "use bootstrap"

A freeze must state at minimum:
- exact null-imposed statistic;
- whether resampling is residual-, score-, influence-function-, or
  pseudo-observation-based;
- exact kernel;
- exact bandwidth rule;
- auxiliary multiplier distribution;
- covariance construction using actual time distance versus segment-local
  index distance;
- whether multiplier processes reset at declared continuity boundaries;
- studentization;
- nuisance re-estimation;
- bootstrap replication count;
- finite-bootstrap p-value rule;
- seed hierarchy;
- invalid-replicate policy.

### fixed-b can no longer be specified merely as "change critical values"

A freeze must state:
- exact HAC kernel;
- exact (b=M/T) rule;
- what (T) means with multiple continuity segments;
- whether segments receive separate covariance contributions or a pooled
  construction;
- exact nonstandard critical-value generation/table procedure for 7/4/2
  restrictions;
- deterministic numerical simulation settings if critical values are
  simulated;
- interaction with the six-test Holm family.

## 7. Current methodological conclusion

Formula-level access materially improves the review packet, but it **does not
remove the independent-review requirement**.

The core unresolved issue is now more precise:

> Neither the original DWB paper nor the fixed-b paper directly supplies a
> turnkey inference rule for AMS-DEP's segmented, exact-time,
> state-interaction regression.

Therefore current status remains:

**INSUFFICIENT_EVIDENCE_FOR_DESIGN_FREEZE**

The next legitimate advancement is an independent reviewer selecting and
fully specifying one method (or rejecting all candidates) using these
full-text sources.

## 8. Open source locations recorded for reviewer use

- Xiaofeng Shao, University of Illinois author-hosted full DWB article.
- Xiaofeng Shao, University of Illinois DWB supplementary material.
- Nicholas M. Kiefer, Cornell author-hosted Kiefer–Vogelsang working paper.
- UC eScholarship working-paper version of Sun–Phillips–Jin.
- Xiaofeng Shao, University of Illinois author-hosted Zhou–Shao regression
  paper.
- Michigan Technological University publication record for Rho–Shao.

These are public research sources; they are not copied into the repository.

## Research-integrity boundary

No actual BTC/ETH AMS-DEP return result was inspected in this audit.

No:
- V2 simulation;
- Development market-data inference;
- Validation/OOS;
- strategy P&L;
- paper trading;
- live trading

was authorized or performed.
