# AMS-DEP-001-v1 — Time-varying return dependence

**DRAFT — NOT FROZEN — NO EMPIRICAL EXECUTION AUTHORIZED.**

Classification: MODEL / HYPOTHESIS. No results observed for this new experiment during preparation. Historical Development strategy results and AMS-V1 occupancy are known; the sample is reused. This diagnostic ID is separate from the closed HYP-0001–HYP-0025 strategy family and existing Cycle 9 source probe.

## Proposed estimands and mechanism

Changing information incorporation, liquidity provision or participant composition might alter conditional signed-return dependence. The same observations could instead arise from microstructure or changing volatility; this design does not identify participants or establish causation.

Primary scope is deliberately narrow: one-hour linear conditional-mean dependence and its differences across calendar years and AMS-V1 volatility states. Other horizons and state axes are descriptive secondary diagnostics, not extra opportunities for primary rejection. Nonlinear predictability and economic profitability remain untested.

## Data and timing contract

- BTCUSDT and ETHUSDT, Binance Spot, 1-hour Gate 1A data.
- Development only: `[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`.
- Expected BTC identity: `1590cf8e69ed757eeb6701a218d561448beb2eb6ea09dcd0ae31d15a8f5197cf`.
- Expected ETH identity: `d35bf21e309820abc88090bad29601adc1d1ea6b31dcddf0b80d510af4cf542f`.
- Mismatching source/certification/identity fails closed; no silent recertification.
- `C_t` is close of bar indexed by its stored open timestamp; availability is stored timestamp + 1 hour.
- Predictor `x_t = log(C_t/C_(t-1))`, target `y_t = log(C_(t+1)/C_t)`; both require contiguous certified bars in the same segment.
- State is the unchanged complete AMS-V1 vector at close t. Never assign state at t+1 to y_t.
- Calendar year for a row is the UTC availability time of predictor x_t. Every input and label bar must be Development; no label may use a protected bar.
- Primary rows require complete AMS-V1 even though the primary conditioning axis is volatility. This matches the certified composite eligibility and must be reported as a selection limitation.
- Report all rejected rows by reason. No interpolation, forward fill, winsorization or post-result exclusions.

## Primary model and six hypotheses

Fit each asset separately on identical eligible rows for its three tests:

`y_t = a + sum_y a_y I(year=y) + c_L I(VOL_LOW) + c_H I(VOL_HIGH) + x_t [b + sum_y d_y I(year=y) + e_L I(VOL_LOW) + e_H I(VOL_HIGH)] + u_t`.

Years y are 2018, 2019, 2020, 2021; reference year is 2017. Reference volatility is VOL_NORMAL. All year and volatility intercept terms stay in the model. No model selection. Fourteen coefficients total.

For each asset:

1. DEP: joint null `b=d_2018=d_2019=d_2020=d_2021=e_L=e_H=0` (7 restrictions).
2. TIME: joint null `d_2018=d_2019=d_2020=d_2021=0` (4 restrictions), allowing the specified volatility effects.
3. STATE: joint null `e_L=e_H=0` (2 restrictions), allowing the specified calendar effects.

TIME and STATE directly test differences, not differences in subgroup significance. These are conditional linear projection tests; omitted nonlinear or time/state interactions limit interpretation. Calendar-year contrasts are fixed descriptive environment contrasts, not estimated structural break dates.

Proposed primary uncertainty estimator: OLS with heteroskedasticity/autocorrelation-consistent sandwich covariance, Bartlett weights, maximum lag 168 actual hours. Cross-products only within certified continuity segments and at exact timestamp lag, with omitted rows represented as zero score contributions, never compressed into adjacent time. No cross-segment covariance products. Wald reference is asymptotic chi-square with the stated restriction count. Its finite-sample adequacy must be assessed before release; HAC is not a cure for arbitrary nonstationarity, heavy tails or endogenous selection.

Multiplicity: Holm step-down over exactly six primary p-values at family-wise alpha 0.05, including both assets. Sort ascending; compare p_(i) to 0.05/(7-i), stopping at first non-rejection. An unavailable test remains in the family with p=1 for correction and an explicit unavailable status, not evidence of a null. Do not remove an asset to lower the multiplicity penalty. These controls address the registered family, not the entire historical search on reused Development data.

## Support and failure rules proposed for freeze

Each asset requires at least 5,000 eligible rows; each of 15 year × volatility cells requires at least 200 rows and 10 distinct UTC dates. Report every cell, even if inadequate. Rank-deficient design, nonfinite input, invalid covariance or insufficient support blocks that asset's primary inference. Do not merge years/states or lower thresholds to obtain a result. Numerical rank tolerance, covariance correction and conditioning thresholds are release blockers below.

Report coefficient estimates, covariance, restriction matrices, raw and adjusted p-values, sample counts, year/state support and every failure reason. Confidence intervals must state whether marginal or simultaneous; marginal intervals cannot substitute for the six-test correction. No automatic claim of stability from non-rejection, and no claim that AMH has been proved or disproved.

## Secondary outputs proposed for freeze

All are descriptive; no extra significance claims, post hoc selections or promotion decisions:

- Pearson correlations of signed, absolute and squared hourly returns at lags 1, 2, 6, 12, 24 actual hours, with separate mean/volatility interpretations.
- Backward 90-calendar-day windows ending at UTC month boundaries, plus expanding windows from Development start. At least 720 eligible lag pairs per statistic; no boundary bridging. Show all endpoints including insufficient windows. No overlapping-window independent-test counts.
- Nonoverlapping 1, 6 and 24-hour log-return blocks anchored on UTC epoch-hour multiples; every constituent bar must be contiguous. Adjacent nonoverlapping blocks for lag-one correlations. Never use overlapping horizon returns to manufacture autocorrelation.
- Lo–MacKinlay-inspired variance-ratio diagnostics q=2, 6, 24, on unconditioned consecutive hourly returns only. Never concatenate a state-filtered sequence and call it a random walk. Exact finite-sample formula and inference are NOT frozen here; no VR p-values or implementation until the source/equation audit below is complete.
- Forward 1, 6 and 24-hour conditional return counts, mean, median, 5th/95th percentiles by each separate frozen state axis. Use nonoverlapping UTC-anchored targets; quantile convention must be fixed before execution. No 27-state profitability search.
- BTC/ETH contemporaneous and directed lagged correlations at 1, 6 and 24 hours using exact timestamps and full continuity in both assets. Contemporaneous correlation is not a forecast; shared USDT exposure and venue are limitations.
- Primary-model summaries repeated after dropping each certified continuity segment, with no new p-values or decision threshold; report the full range and segment sample shares. Prespecified HAC bandwidth sensitivity at 24 and 720 hours is diagnostic only and cannot replace the primary result.
- Compare all-eligible and complete-state-eligible descriptive statistics; report coverage by asset, year and segment. Volatility/activity are environmental proxies, not observed market populations.

## Economics boundary

No entry/exit rules, strategy returns, Sharpe ratios, leverage or trade orders. Statistical effects are not net-of-cost profits. Preserve the existing baseline of 10 bps commission plus 5 bps directional slippage per side and all frozen stress tests for any future strategy; an approximate 30 bps round-trip cost is context, not a sufficient profitability test. Dependence estimates in log-return units cannot be compared directly to costs as if executable trades.

## Unresolved release blockers — must be frozen before actual-return access

1. Independent statistical review of the conditional linear estimands, HAC assumptions and finite-sample size/power. Freeze a synthetic Monte Carlo design with exact DGPs, sample/segment patterns, seeds, replication counts, calibration acceptance bounds and failure policy. Cover IID and heteroskedastic martingale nulls, stable AR alternatives, changing dependence, bid/ask bounce and asynchronous observations. Publish all simulation outcomes; do not calibrate to BTC/ETH findings.
2. Exact numerical OLS/rank/covariance implementation, finite-sample correction, singular-matrix behavior, interval construction and quantile convention. No pseudo-inverse silently repairing an unidentified test.
3. Read and verify the original variance-ratio equations and assumptions against the primary paper; freeze formula, denominators, segment aggregation, minimum support and whether inference is deferred. The bibliographic references alone do not complete this audit.
4. Freeze an exhaustive output/test inventory, package versions, fixed implementation SHA, expected data identities, hash of the approved preregistration and independent approval record. A file hash for this draft is provenance only, not certification.
5. Synthetic implementation review proving timestamp availability, both return endpoints, exact cross-asset joins, gap handling, all support rules, multiplicity, failure reporting and blocked protected reads.

Until all five are resolved and committed, no runner or workflow may emit actual-return dependence evidence. Changes before freeze remain versioned draft revisions; changes after evidence require a new experiment version and explicit exposure history. This is a concrete design for review, not a claim that a complete preregistration or statistical engine already exists.

## Allowed eventual outcomes

`DEPENDENCE_DETECTED`, `TIME_HETEROGENEITY_DETECTED`, `STATE_HETEROGENEITY_DETECTED`, `NO_EFFECT_DETECTED`, `INSUFFICIENT_SUPPORT`, `INFERENCE_INVALID`. Report DEP/TIME/STATE decisions separately and permit combinations. All remain Development observations; tradability and causal ecology explanations are unassessed. No outcome grants Validation/OOS or execution access.
