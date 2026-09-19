# AMS-DEP V1 False-Rejection Diagnostic Result

## Classification

**SYNTHETIC DIAGNOSTIC ONLY — NOT MARKET EVIDENCE**

Diagnostic status: **COMPLETE**

Empirical AMS-DEP release status: **BLOCKED**

## Provenance

- Branch: `adaptive-markets-research`
- Frozen diagnostic plan commit: `e490b1fb5a8da8cbfaaceebf96ea1979896932a7`
- Executing commit: `8083c714cdbc725fb683e1ef07649dea50106636`
- Workflow: `AMS DEP V1 Failure Diagnostic`
- Workflow run: `35435551922`
- Artifact: `ams-dep-v1-failure-diagnostic-v1`
- Artifact ID: `10581624694`
- Artifact digest: `sha256:220a2a3825e9c26619f64e593c5a3a62bb8165b3e87399d8184c4b3d3e896be4`
- Full software regression suite: PASS
- Diagnostic firewall: PASS
- Market data accessed: NO
- Validation/OOS accessed: NO
- Strategy P&L/signals generated: NO

The failed V1 calibration evidence remains unchanged.

## Independent numerical-oracle audit

The production OLS/HAC implementation was compared with an independently
coded unscaled normal-equation OLS and direct Bartlett lag-sum covariance on
the preregistered oracle replications.

**Result: NO_ORACLE_MISMATCH_OBSERVED.**

All coefficient and covariance comparisons were within the frozen
`1e-10` absolute tolerances.

This materially reduces the probability that the V1 false-rejection inflation
was caused by an algebraic implementation error in the production
Bartlett-HAC covariance.

## Family-wise rejection sensitivity

All values below use the same V1 null DGPs, model, restrictions, six-test Holm
family, sample sizes, and seed schedule. Only the diagnostic HAC lag differs.

| Null DGP | HAC 0 | HAC 24 | HAC 168 (V1) |
| --- | ---: | ---: | ---: |
| IID null | 3.0% | 5.1% | **12.6%** |
| Heteroskedastic null | 4.5% | 5.7% | **24.7%** |
| GARCH null | 3.4% | 4.7% | **14.3%** |

These are diagnostic sensitivities, not a post-hoc authorization to replace
168 with 24.

## Raw null rejection at V1 lag 168

### IID null

- BTC DEP: 14.4%
- BTC TIME: 9.6%
- BTC STATE: 8.1%
- ETH DEP: 13.8%
- ETH TIME: 10.5%
- ETH STATE: 7.1%

### Heteroskedastic null

- BTC DEP: 22.7%
- BTC TIME: 20.8%
- BTC STATE: 6.8%
- ETH DEP: 23.7%
- ETH TIME: 20.5%
- ETH STATE: 6.9%

### GARCH null

- BTC DEP: 18.0%
- BTC TIME: 12.5%
- BTC STATE: 8.3%
- ETH DEP: 17.1%
- ETH TIME: 11.6%
- ETH STATE: 9.0%

The distortion is strongest for the larger joint DEP/TIME restrictions and
under conditional heteroskedasticity.

## Wald reference-distribution mismatch

The diagnostic compared empirical Wald 95th percentiles with their registered
asymptotic chi-square 95th percentiles.

Selected empirical/theoretical 95th-percentile ratios:

### IID null

At HAC 0, ratios were approximately 0.90–1.03.
At HAC 24, approximately 0.95–1.09.
At HAC 168:

- BTC DEP: **1.369**
- BTC TIME: **1.288**
- BTC STATE: **1.114**
- ETH DEP: **1.319**
- ETH TIME: **1.204**
- ETH STATE: **1.105**

### Heteroskedastic null

At HAC 168:

- BTC DEP: **1.734**
- BTC TIME: **1.826**
- BTC STATE: **1.139**
- ETH DEP: **1.641**
- ETH TIME: **1.776**
- ETH STATE: **1.160**

### GARCH null

At HAC 168:

- BTC DEP: **1.456**
- BTC TIME: **1.293**
- BTC STATE: **1.190**
- ETH DEP: **1.298**
- ETH TIME: **1.325**
- ETH STATE: **1.226**

Thus the V1 chi-square reference is materially anti-conservative in the
registered finite synthetic samples at lag 168.

## Covariance calibration

The diagnostic also compared empirical across-replication coefficient
variance with the mean model-estimated marginal variance for the seven
slope/interaction coefficients.

At HAC 0 and 24 the ratios were generally close to one.

At HAC 168:

- IID null median ratios were about **1.093 BTC** and **1.070 ETH**;
- heteroskedastic null median ratios were about **1.305 BTC** and **1.223 ETH**;
- GARCH null median ratios were about **1.125 BTC** and **1.169 ETH**.

Some heteroskedastic-null coefficient ratios reached about **1.40**.

This supports covariance underestimation as part of the V1 finite-sample
problem, while the Wald-quantile inflation shows that covariance scale alone
does not exhaust the issue.

## Diagnostic conclusions

The allowed diagnostic conclusions are:

- **NO_ORACLE_MISMATCH_OBSERVED**
- **BANDWIDTH_SENSITIVITY_OBSERVED**
- **ASYMPTOTIC_REFERENCE_MISMATCH_OBSERVED**
- **COVARIANCE_UNDERESTIMATION_OBSERVED**

The evidence points to a finite-sample HAC/Wald calibration problem associated
with the large fixed V1 bandwidth, rather than a discovered coding error.

This does not prove that 24 is the correct empirical bandwidth and does not
authorize selecting it after the fact. A replacement procedure must be
prospectively specified and recalibrated.

## Andrew Lo / Lo-MacKinlay connection

This result reinforces the project's Lo-guided rule that finite-sample size
and power must be studied before trusting empirical test significance.

The correct response is not to inspect BTC/ETH results or weaken thresholds.
The next step is a prospectively frozen V2 inference design, followed by
synthetic calibration before any empirical-release review.

## Decision

**AMS-DEP V1 remains failed. Actual BTCUSDT/ETHUSDT dependence estimates remain blocked.**

Any V2 must:

1. state its finite-sample rationale before results;
2. preserve V1 and this diagnostic evidence;
3. use synthetic/null calibration before market-data release;
4. retain the six-test multiplicity family unless a new scientific question
   is separately preregistered;
5. avoid choosing a procedure because it produces favorable BTC/ETH results;
6. undergo the separate independent design/implementation release review
   required by the parent preregistration.
