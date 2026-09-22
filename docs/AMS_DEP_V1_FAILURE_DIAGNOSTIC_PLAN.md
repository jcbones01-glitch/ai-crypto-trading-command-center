# AMS-DEP V1 False-Rejection Diagnostic Plan

## Status

**FROZEN DIAGNOSTIC PLAN — SYNTHETIC DATA ONLY — NOT A V2 METHOD SELECTION**

This diagnostic follows the failed AMS-DEP synthetic numerical-core V1 calibration.
It is designed to identify why V1 over-rejected true nulls before any replacement
inference method is proposed.

It does not authorize BTC/ETH market-data access, empirical AMS-DEP execution,
strategy P&L, Validation/OOS access, or trading.

## Preserved evidence

V1 remains failed. Nothing in this diagnostic may reinterpret or overwrite:

- frozen V1 specification commit `2dd1543f654b5a605a902ce2b3cf98c70c9755b1`;
- V1 completed run `35434647946`;
- V1 artifact `10582128182`;
- V1 false-rejection ceiling 0.075;
- V1 result record `research/experiments/AMS_DEP_SYNTHETIC_CORE_V1_RESULT.md`.

The diagnostic has no pass/fail threshold. It cannot promote V1.

## Questions fixed before execution

1. Does the production OLS/HAC covariance match an independently coded,
   unscaled normal-equation + direct Bartlett-lag-sum oracle?
2. How does null rejection change when the HAC maximum lag is 0, 24, or the
   registered V1 value 168, holding the DGP, model, restrictions, multiplicity,
   sample length, and seeds fixed?
3. How do empirical Wald-statistic quantiles compare with the asymptotic
   chi-square reference distribution for DEP, TIME, and STATE restrictions?
4. Does the average estimated covariance materially understate the empirical
   across-replication variance of the corresponding null coefficients?
5. Is the inflation concentrated in the seven-restriction DEP test, or does it
   also appear in TIME/STATE restrictions and heteroskedastic/GARCH nulls?

## Fixed synthetic scope

Use only the V1 null DGPs:

- `iid_null`;
- `heteroskedastic_null`;
- `garch_null`.

Use the original V1 configuration and seed schedule exactly:

- seed: 20260919;
- 1,000 replications per case;
- 5 synthetic year blocks;
- 2,000 retained predictor/target pairs per year;
- 1,000-hour burn-in;
- asset correlation 0.6;
- same deterministic LOW/NORMAL/HIGH state schedule;
- same full 14-column model;
- same six-test Holm family;
- same DEP/TIME/STATE restrictions.

This is reuse for diagnosis, not a second chance to pass V1.

## Fixed bandwidth sensitivity

Evaluate exactly:

- HAC lag 0;
- HAC lag 24;
- HAC lag 168.

No other bandwidth is added after results.

Lag 0 is a diagnostic covariance baseline, not a proposed valid empirical method.
Lag 24 is a prespecified intermediate sensitivity. Lag 168 is the failed V1
contract.

## Independent numerical oracle

For the first three replications of each null DGP and both assets at lag 168:

1. construct the same 14-column design;
2. fit OLS independently with unscaled normal equations using
   `numpy.linalg.solve(X.T @ X, X.T @ y)`;
3. calculate residual scores `g_t = X_t u_t`;
4. calculate Bartlett HAC directly as:
   `G0 + sum_l w_l (G_l + G_l.T)`, with
   `w_l = 1 - l/(L+1)`, and cross-products only within declared segments and
   only for exact-hour lag `l`;
5. use the same registered HC1-style factor `n/(n-p)`;
6. compare production and oracle coefficient/covariance matrices.

The oracle may fail closed if the direct normal equations are numerically
unidentified. No pseudo-inverse or ridge repair is allowed.

Tolerance is fixed at:
- coefficients: max absolute difference <= 1e-10;
- covariance: max absolute difference <= 1e-10.

An oracle mismatch is evidence of an implementation discrepancy and must be
reported; it does not authorize an ad hoc code fix in the same evidence run.

## Fixed diagnostic outputs

For each DGP × lag:

- 1,000-replication family-wise rejection rate after the unchanged six-slot Holm
  procedure;
- six adjusted rejection rates;
- six raw-p-value rejection rates at 0.05;
- invalid-fit count;
- for each asset/restriction, Wald statistic empirical 50th, 90th, 95th and 99th
  percentiles;
- corresponding theoretical chi-square 95th percentile;
- ratio of empirical 95th percentile to theoretical 95th percentile;
- empirical across-replication coefficient variances for the seven slope/
  interaction coefficients;
- mean model-estimated marginal variances for those coefficients;
- empirical-variance / mean-estimated-variance ratios.

No diagnostic value is itself an acceptance threshold.

## Interpretation boundary

Allowed conclusions are limited to:

- `IMPLEMENTATION_ORACLE_MISMATCH`;
- `NO_ORACLE_MISMATCH_OBSERVED`;
- `BANDWIDTH_SENSITIVITY_OBSERVED`;
- `ASYMPTOTIC_REFERENCE_MISMATCH_OBSERVED`;
- `COVARIANCE_UNDERESTIMATION_OBSERVED`;
- `CAUSE_NOT_ISOLATED`.

Multiple conclusions may apply.

The diagnostic cannot declare any replacement inference method valid. If a
specific cause is supported, a separate V2 design must be prospectively
specified, independently reviewed, frozen, and calibrated before results.

## Research firewall

- market data accessed: false;
- Validation/OOS accessed: false;
- strategy P&L calculated: false;
- strategy signals generated: false;
- empirical release authorized: false.
