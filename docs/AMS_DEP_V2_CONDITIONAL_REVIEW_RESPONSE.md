# AMS-DEP V2 conditional review receipt and implementation response

## Provenance and authority

The user supplied an external review in this conversation, with decision
`APPROVE_V2_DESIGN_AFTER_SPECIFIED_CHANGES`, against branch head
`81db0d6f5d6f3a711106b6e157ebaabd98a8566a`, PR #42 and Issues #43/#44.
GitHub independently confirmed that head and the still-blocked gate. The
reviewer's identity/independence has not been independently authenticated;
this record is a faithful decision/requirements summary, not a forged signed
review or a claim that the implementer is the independent reviewer. The pasted
reference list was truncated. Verified primary-source URLs are provided below.

The review selects null-imposed residual DWB, exact-time segment-reset Gaussian
Parzen multipliers, ell=max(2,n_s^(1/5)), 4,999 requested draws, six-slot Holm,
2,000 outer replications, retained V1 DGPs plus four stresses, and a separate
unopened 2,000-replication-per-DGP holdout. Invalid draws count as exceedances;
no redraw, bandwidth selection, threshold relaxation or V1 erasure. Thresholds
remain size <=0.075, target power >=0.80, invalidity <=0.01. It requires
covariance oracles, full endogenous-state/744-bar pipeline integrity, exact
asynchronous joins, partition read denial, and separate empirical approval.
It explicitly reports no access to actual BTC/ETH AMS-DEP outcomes.

## Assessment

V1 evidence remains unchanged: implementation-oracle agreement is distinct
from valid inference. Lag 168 over-rejection and covariance underestimation
support a finite-sample inference failure; no unique causal decomposition is
claimed. Lag 24 remains contaminated diagnostic information, not a V2 choice.

Primary-source verification: Shao (2010), section 2 assumption 2.1, supports
kernel-defined dependent multipliers and lists Parzen as admissible. Sections
4–5 distinguish irregular lattice and nonlattice settings; section 4 discusses
the absence of general second-order correctness for Gaussian multipliers.
This does not prove validity for the AMS regression. The chosen bandwidth
constant and regression studentization remain project design choices.

- https://publish.illinois.edu/xshao/files/2012/11/JASA-DWB.pdf
- https://publish.illinois.edu/xshao/files/2012/11/ZhouShaoJRSS.pdf

Zhou–Shao concerns fixed-design dependent-error regression with a different,
self-normalized architecture. It is contextual support, not a proof of this
DWB implementation. No academic endorsement of this specific method is claimed.

## Completed engineering response

- Exact-time banded Parzen multiplier covariance and banded Cholesky, no PSD
  projection/jitter, with independent dense scalar-kernel oracle and factor
  reconstruction, unit diagonal, PSD, zero-support and segment-block checks.
- Scaled fixed-design SVD algebra cached; coefficients, residuals and Parzen
  HAC recomputed for each pseudo-target. Observed and bootstrap statistics
  use the same Parzen studentization (explicit interpretation for ratification).
- Each hypothesis has its own null-restricted least-squares fit. Restrictions
  select free columns because all registered restrictions are zero coefficients;
  a separate KKT/normal-equation oracle verifies this implementation.
- Segment-centered restricted residuals and independently seeded segment
  multipliers; exact hour distance survives missing rows.
- Conservative invalid-draw accounting; exactly 4,999 draws required by the
  p-value helper. Bounded engineering fixture exposes no p-value or calibration
  conclusion and is limited to 32 draws.
- Synthetic execution guard now requires review, freeze and oracle prerequisites
  as well as its authorization flag; a lone flag cannot bypass them.
- No calibration or empirical runner was introduced. No calibration/holdout
  realizations or BTC/ETH AMS-DEP results were accessed.

## Remaining conditional decisions

The review requests prospectively fixed stress parameters/seeds but does not
supply them. The companion JSON and numerical contract propose exact values.
They are **not yet the independently accepted calibration freeze**. The
implementer has not silently marked conditional approval as unconditional.
The reviewer should ratify:

1. Same Parzen covariance for observed and bootstrap Wald statistics.
2. Exact four stress definitions, masks, true-null/target slots and reserved
   seed namespaces in `ams_dep_synthetic_core_v2_proposed.json`.
3. Per-slot original invalidity plus any-invalid-family accounting; bootstrap
   invalidity aggregated per DGP/asset/hypothesis, with per-outer maxima also
   reported. Original invalid fits remain unavailable slots, not replaced draws.
4. The synthetic holdout as a second required size/power check only after
   unchanged calibration passage. Any calibration-driven method/code repair
   creates V3; no V2 holdout is used to rescue it.
5. Exact segmented RNG/factor construction and numerical tolerances in the
   contract. Segment coordinates follow the required draw coordinate.
6. A feasible complete-run resource/sharding plan, without reducing B, outer
   replications, DGPs or thresholds.

## Resource finding

If all eleven DGPs run six slots, calibration requests
11*2000*6*4999 = **659,868,000** inner draws; holdout doubles that to
**1,319,736,000**. Each V1-style sample has 10,000 rows, not 2,000 total.
A bounded eight-draw deterministic fixture at that size took about 0.027 seconds
locally in the requested package/Python environment with one BLAS thread.
Linear extrapolation including setup is approximately **618 serial CPU-hours**
per suite; it is a rough planning measurement, not a calibrated runtime promise.
Thirty-two fully utilized independent workers would imply roughly 19.3 hours
per suite before overhead, provisioning, invalid-fit variation and contention.
Actual billing limits and capacity are unverified; no such workload is launched.
The calibration is not responsibly characterized as a routine short CI job.

Next action is an independent follow-up decision on these concrete details and
resource plan. `independent_v2_design_approved`, `v2_specification_frozen`,
calibration, holdout, full-pipeline integrity and all execution approvals remain
false. Issue #44 remains open. The actual partition-access firewall proof is
still future full-pipeline work; the existing authorization guard is not
misrepresented as proof that every storage backend denies protected reads.

Additional theory caveat for the follow-up reviewer: the synthetic generator's
predictor is a lagged return, so it is stochastic and related to the path of
future targets. Keeping X fixed in the residual bootstrap is an explicit
approximation under review, not a claim that fixed-exogenous-design theory
covers this autoregressive setting automatically. A passing numerical oracle
checks equations; it cannot resolve that statistical transfer question.
