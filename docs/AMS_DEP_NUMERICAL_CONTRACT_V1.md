# AMS-DEP numerical contract v1

Status: proposed numerical specification; synthetic verification authorized. Empirical execution remains blocked by the parent preregistration. This contract resolves draft numerical choices; it is not independent approval.

## Source and equation audit

Original source: [Lo and MacKinlay, Wharton working paper 5-87, unabridged](https://rodneywhitecenter.wharton.upenn.edu/wp-content/uploads/2014/04/8705.pdf), precursor to the 1988 Review of Financial Studies article. The scan was retrieved and inspected visually on 2026-09-19: PDF pages 8–12, and footnote 8 on pages 32–33. Equations 8b, 10–11 and footnote 8 distinguish overlapping returns and the finite-sample denominators. The ratio itself is not unbiased merely because its component estimators are corrected. Sections 2.2 and its moment restrictions also limit the heteroskedastic inference. We do not transplant its weekly-equity evidence into crypto, and do not implement a VR significance test in this release.

For one contiguous segment containing N hourly log returns r, q is 2, 6 or 24. Define mean m=mean(r), z=r-m, A=sum(z²)/(N-1), B=sum of squared rolling q-return centered sums / [q(N-q+1)(1-q/N)]. Report VR=B/A and VR-1, N, q and overlapping-sum count. Use all N returns, even when N is not divisible by q; this algebraic extension of the overlapping estimator is explicit. Require N>=max(720,20q), finite observations, strictly hourly timestamps and positive A. Constant data or gaps fail closed. No segment concatenation, pooled VR, state filtering or p-value. Each qualifying segment/q is reported separately; omitted segments retain an insufficient-support reason. q/N<=0.05 is a fixed design constraint, not evidence of adequate asymptotics.

Primary-source PDF SHA-256: 0917c10a5e86ed4b0f78f8257f8fc5405b4b687f6919fb3365610a469e6aa59a. The paper is referenced, not copied into the repository.

## Numerical representation and model

Float64 NumPy 2.2.6 and SciPy 1.15.3; use one BLAS thread for calibration reproducibility. Math inputs are explicit in-memory arrays. This module has no market loader, network interface, credentials or empirical CLI. It cannot certify the provenance of arrays supplied by a caller. A future empirical runner must independently enforce the research firewall before reading/fetching observations.

For the 14-column model, columns in order are: intercept, year 2018/2019/2020/2021 indicators, VOL_LOW/VOL_HIGH indicators, x, x×year 2018/2019/2020/2021, x×VOL_LOW/x×VOL_HIGH. Valid years are exactly 2017–2021 and state codes LOW/NORMAL/HIGH. Unknown labels and mismatched/nonfinite arrays raise an error. Primary restriction column indices are DEP=7..13, TIME=8..11, STATE=12..13. These restrictions are not interchangeable with tests of subgroup p-values.

Scale each design column by its Euclidean norm, without demeaning; a zero norm is invalid. Compute reduced SVD; reject if n<=p, any singular value is <=1e-12 times the largest, or scaled condition number exceeds 1e8. Only after these checks use the full-rank SVD OLS solution and inverse cross-product. Transform coefficients and covariance back to original units. No ridge, dropping columns or rank-reducing pseudo-inverse is permitted. Reject nonfinite intermediates and nonpositive restriction covariance. No threshold may be relaxed after failure.

## Exact-time Bartlett HAC

Let score g_t=x_t*u_t, using scaled design and OLS residuals. For each declared continuity segment separately, place scores on the exact integer-hour grid; absent eligible rows have zero scores but are not regression observations. Duplicate or globally unsorted hours and a segment ID reappearing after another segment are invalid. Segment IDs are caller-supplied certified boundaries; the math core does not infer certification. Maximum grid span per segment is 100,000 hours; exceeding it fails rather than allocating unbounded storage.

With L=168 and weights w_l=1-l/(L+1), meat=sum g_t*g_t' + sum_l w_l sum_t(g_t*g_(t-l)' + g_(t-l)*g_t'). Never include cross-segment products. Compute exactly the same matrix efficiently as the sum of outer products of every width-(L+1) moving score sum, divided by L+1, with L zero vectors padded at both segment ends. This identity preserves actual time and positive semidefiniteness; it is an implementation identity, not a new statistical theorem claimed from the source.

Covariance=(X'X)^-1 meat (X'X)^-1 × n/(n-p), where n counts eligible regression rows, not padded hours. Symmetrize roundoff. Require positive semidefiniteness within -1e-12 times the largest absolute eigenvalue; do not clip eigenvalues or silently repair invalid covariance. Restriction covariance must be positive definite with condition number <=1e12; otherwise the test is invalid. Wald statistic uses a solve, chi-square survival function with 7/4/2 degrees of freedom, and no F-reference substitution. Intervals are marginal normal 95% coefficient intervals using 1.959963984540054; label them non-simultaneous.

The HAC form follows the Bartlett approach of [Newey and West (1987)](https://www.jstor.org/stable/1913610). The source's bibliographic record was checked; this specification spells out the complete formula and will be checked against a separate direct summation oracle. Finite-sample correction, bandwidth, numerical thresholds and segmentation are project choices.

## Multiplicity and missing inference

Use exactly six slots in order BTC_DEP, BTC_TIME, BTC_STATE, ETH_DEP, ETH_TIME, ETH_STATE. Missing/invalid slots carry raw p=null, calculation p=1, adjusted p=null and reject=false; retain their place in the six-test family. Sort by calculation p then slot order. Adjusted p for sorted rank i (1-based) is min(1,max_{j<=i}[(7-j)*p_(j)]). Reject available slots only if adjusted p<=0.05. Reject out-of-range, NaN or infinite supplied p-values rather than treating them as missing. [Holm (1979)](https://www.ime.usp.br/~abe/lista/pdf4R8xPVzCnX.pdf) supplies the sequential family-wise framework; valid individual p-values remain a prerequisite.

## Descriptive conventions and exclusions

Quantiles use NumPy linear interpolation (Hyndman–Fan type 7). Pearson correlations use paired-sample demeaning, with zero variance reported unavailable. Exact hourly lag joins must not compress gaps. Existing draft support thresholds and row eligibility remain unchanged and are not waived by primitive tests. Complete support enforcement, AMS-V1 row construction, secondary rolling/cross-asset summaries and empirical report assembly are separate implementation work. This contract does not claim those parts are implemented.

No finite-sample stability conclusion, equivalence test, trading profitability, validation eligibility or independent certification is produced by this contract or synthetic results.
