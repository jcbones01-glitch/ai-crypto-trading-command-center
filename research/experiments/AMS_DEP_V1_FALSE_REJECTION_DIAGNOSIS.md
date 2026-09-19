# AMS-DEP V1 False-Rejection Diagnosis

## Status

**DIAGNOSTIC ONLY — SYNTHETIC EVIDENCE — NO EMPIRICAL RELEASE**

This note diagnoses the V1 synthetic calibration failure recorded in
`research/experiments/AMS_DEP_SYNTHETIC_CORE_V1_RESULT.md`. It does not alter
V1, does not inspect BTC/ETH market returns, and does not authorize V2
execution.

## 1. Implementation audit

The V1 implementation was re-read against
`docs/AMS_DEP_NUMERICAL_CONTRACT_V1.md`.

The following implementation components have direct independent software
oracles in `tests/test_dependence_statistics.py`:

- exact-time Bartlett HAC is checked against an explicit double-sum oracle,
  including gaps and declared continuity breaks;
- lag-0 HC1 OLS coefficients/covariance are checked against a separate normal
  equation implementation;
- Wald statistics are checked against the scalar closed-form calculation;
- coefficient rescaling is checked for inference invariance;
- Holm's six-slot family is checked with fixed expected adjusted p-values;
- the variance-ratio point estimator is checked against an exact rational
  arithmetic oracle;
- synthetic generators are checked for deterministic replay and exact
  x/y lag pairing.

The full repository regression suite passed immediately before the completed
7,000-replicate V1 calibration.

**Diagnosis:** no implementation defect has been demonstrated in these audited
primitives. This does not prove the entire inference procedure is correct in
finite samples; it narrows the present failure away from the tested algebraic
implementation and toward inferential calibration.

## 2. What the V1 results say

The preregistered family-level false-rejection ceiling was 0.075. V1 produced:

- IID null: 0.126;
- heteroskedastic null: 0.247;
- GARCH null: 0.143;
- stable-AR true TIME/STATE restrictions: 0.116;
- time-varying-AR true STATE restrictions: 0.075;
- state-varying-AR true TIME restrictions: 0.123.

Invalid-fit rate was zero in every case. Registered strong-alternative power
was 1.000 for the planted DEP/TIME/STATE targets.

The heteroskedastic-null per-slot rates are especially informative: BTC DEP
0.127, ETH DEP 0.112, BTC TIME 0.094 and ETH TIME 0.088. Therefore the
family-level failure cannot be explained solely by the expected accumulation
of six individually valid 5% tests. Several constituent asymptotic p-values
are themselves anti-conservative under the registered DGP.

## 3. Statistical diagnosis

V1 uses a long Bartlett HAC bandwidth (168 hours), a finite regression sample
of 2,000 observations per year/segment, joint Wald restrictions, and
chi-square asymptotic reference distributions.

The synthetic evidence demonstrates that the resulting p-values are not
sufficiently calibrated for the project's registered finite-sample nulls.
The failure is largest under unconditional heteroskedasticity and remains
material under GARCH and several nested-restriction nulls.

The current evidence therefore supports the following diagnosis:

> **V1 is an asymptotic-inference calibration failure unless and until a
> specific implementation defect is independently demonstrated.**

This is deliberately narrower than claiming one unique mathematical cause.
The completed experiment does not separately identify how much distortion is
attributable to the 168-hour HAC bandwidth, finite-sample Wald approximation,
heteroskedasticity, persistence, or their interaction.

## 4. Andrew Lo / Lo-MacKinlay implication

This failure is methodologically useful rather than something to tune away.

Lo and MacKinlay's finite-sample variance-ratio research explicitly examined
the size and power of test statistics with Monte Carlo experiments before
trusting empirical significance. The relevant lesson for this project is
procedural:

1. specify the statistic/inference rule;
2. measure its finite-sample behavior under known nulls and alternatives;
3. reject or redesign a procedure that has unacceptable size;
4. only then expose it to market data.

V1 has completed steps 1–3 and failed the release criterion. High power does
not compensate for excessive type-I error.

## 5. V2 design direction

A V2 should not merely swap one asymptotic reference distribution for another
after seeing the failure. It requires a new prospectively frozen numerical
contract.

The preferred design direction for independent review is a **null-imposed
resampling/bootstrap inference procedure** that estimates the finite-sample
null distribution of each registered DEP/TIME/STATE statistic while
preserving the dependence/heteroskedastic features the method is intended to
tolerate.

Before implementation, V2 must explicitly freeze:

- null imposed for each DEP/TIME/STATE restriction;
- resampling unit and dependence-preserving mechanism;
- block/bandwidth rule if block resampling is used;
- bootstrap replication count and RNG algorithm/seeds;
- whether nuisance parameters are re-estimated in each replicate;
- exact studentization/test statistic;
- treatment of year/state indicators and interactions;
- six-slot multiplicity procedure;
- invalid-replicate policy;
- computational precision/package versions;
- all V1 DGPs retained without deletion;
- additional DGPs, if any, added before V2 output;
- unchanged <=0.075 family false-rejection ceiling;
- unchanged >=0.80 registered power floor;
- unchanged <=0.01 invalid-fit ceiling;
- explicit no-retuning-after-result policy.

A V2 calibration should also add the previously deferred **endogenous AMS-V1
state construction / row-selection pipeline** before empirical release.
Passing the exogenous-state numerical core alone will not be sufficient.

## 6. What is not authorized

Until a prospectively frozen V2 passes calibration and receives the required
independent release review:

- no BTCUSDT/ETHUSDT AMS-DEP empirical computation;
- no Development p-values from actual returns;
- no Validation/OOS access;
- no strategy construction from AMS-DEP;
- no P&L, paper trading, live trading, or leverage;
- no reinterpretation of V1 thresholds;
- no deletion of the V1 artifact or failure record.

## Decision

**V1 remains failed. EMPIRICAL RELEASE remains blocked.**

The next permitted artifact is a V2 *design/preregistration*, not a V2 result.
