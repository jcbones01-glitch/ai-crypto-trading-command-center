# AMS-DEP V2 numerical contract — conditional review follow-up

Status: EXACT ENGINEERING PROPOSAL; NOT CALIBRATION FROZEN OR EMPIRICALLY APPROVED.
User-supplied conditional design review is recorded in
AMS_DEP_V2_CONDITIONAL_REVIEW_RESPONSE.md. This document completes ambiguities
for ratification before any calibration/holdout output. Engineering fixtures
are separate, bounded, non-calibrating examples.

## Model and restrictions

Retain V1's 14 columns and DEP=7..13, TIME=8..11, STATE=12..13 zero restrictions.
Scale columns by Euclidean norm; reject zero norms, n<=p, singular values
<=1e-12 times largest, or scaled condition >1e8. Preserve full rank; no ridge or
unrestricted column deletion. Cache only fixed-X algebra. Every target, original
or bootstrap, gets fresh OLS coefficients, residuals and covariance. No V1
chi-square p-value or marginal normal interval is reported as V2 inference.

For each restriction, fit the free-column model to impose beta_restricted=0.
Compute yhat0 from that model; center its residuals within each declared segment.
Generate y*=yhat0+centered_residual*W. Fixed X, labels, hour coordinates and
eligibility remain unchanged. No recentering of multiplier draws or leverage
adjustment is added. Failure of restricted identification makes that slot
unavailable, even if another restriction is available.

## Exact-time Parzen kernel

For z=abs(hour_i-hour_j)/ell_s, K(z) is:
1-6z^2+6z^3 for 0<=z<=1/2;
2(1-z)^3 for 1/2<z<1; zero for z>=1.
ell_s=max(2,n_s^(1/5)) hours, unrounded, where n_s counts eligible rows.
Across declared segments K=0. A missing observation within a declared segment
changes exact-hour distance; it is not automatically a new declared boundary.
No compression of hour coordinates. Preserve V1's sorted unique integer-hour
coordinates, nonrecurring segment IDs and maximum 100,000-hour segment span.

Construct the lower-banded covariance using row diagonals only for storage:
entry (j+d,j) still uses actual hour difference. Integer hours imply zero
entries for row distance >=ceil(ell_s). Use scipy.linalg.cholesky_banded,
lower=True. For independent standard Gaussian z_s, multiply by this lower
factor, never its inverse. No jitter, ridge, eigenvalue truncation or PSD
projection. Factorization failure is an explicit geometry/engineering failure.
Independent dense oracle must show symmetry, unit diagonal, PSD and exact zeros
across segments and outside support. Algebraic comparisons: atol=rtol=1e-10;
small covariance-factor fixture comparisons use 1e-14. These are numerical
agreement tolerances, not statistical release thresholds.

## Studentization — ratification item

Use the SAME Parzen geometry for both observed and bootstrap Wald covariance:
G_t = scaled_X_t * residual_t;
meat = sum_s sum_(i,j in s) K((h_i-h_j)/ell_s) G_i G_j';
cov_scaled = bread * meat * bread * n/(n-p), then transform to original units.
No cross-segment product. Symmetrize roundoff only. Preserve V1 PSD tolerance
-1e-12*largest_abs_eigenvalue and nonnegative diagonal. Restriction covariance
must be positive definite and condition <=1e12. Compute beta_R'cov_R^-1 beta_R.
Observed covariance must not retain V1 Bartlett while bootstrap uses Parzen.

## Draws, seeds and invalidity

Exactly B=4999 REQUESTED draws, indexed 0..4998, per original-data slot.
The phrase 'successful requested' in the review is interpreted as requested,
not 4999 valid survivors: invalids are never redrawn and count as exceedances.
p=(1+exceedances)/5000, including equality. Nonfinite/negative/singular bootstrap
statistics are invalid. Report original invalidity per slot and any-invalid
family, and inner invalid rates per DGP/asset/hypothesis over all requested
inner draws for available originals; report per-outer maxima separately.
Any original invalid rate or cell bootstrap-invalid rate >0.01 fails. Cells
with no available originals fail, never vacuously pass.

PCG64(SeedSequence([root,2,dgp_index,outer_index,asset_index,hypothesis_index,
bootstrap_index,segment_ordinal])). Indices are zero-based; hypothesis order
DEP,TIME,STATE. A segment ordinal is appended AFTER the required draw index.
Roots in companion proposal are distinct for engineering/calibration/holdout.
Generate one normal vector of n_s values per segment. No shared mutable streams,
shard-dependent seeds, rerolls or draw-count changes. Execution order must not
change the draw associated with any full coordinate. Use Python 3.12.14,
NumPy 2.2.6, SciPy 1.15.3, float64 and one BLAS thread per worker.

## Multiplicity and gates

Keep all six V1 Holm slots including unavailable slots calculated as p=1.
Size <=0.075, registered power >=0.80, invalidity <=0.01, with all rates and
Wilson intervals reported. The p-value helper alone grants no execution
permission. No new calibration CLI exists in this engineering change.
Calibration/holdout data remain unopened. No production state pipeline,
744-bar warm-up, actual cross-asset join or storage firewall has been certified
by these math tests. Their later synthetic tests and independent empirical
release remain mandatory. Changes prompted by calibration outcomes create V3.
