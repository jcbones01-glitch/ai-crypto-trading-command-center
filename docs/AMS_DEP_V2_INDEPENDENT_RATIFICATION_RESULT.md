# AMS-DEP V2 independent ratification result

## Decision

**RATIFY_V2_FREEZE_FOR_SYNTHETIC_CALIBRATION**

This record preserves the user-supplied independent review received after the
conditional V2 design review.

The reviewer states that they did not design or implement AMS-DEP V2, did not
inspect actual BTC/ETH AMS-DEP outcomes, and did not inspect Validation/OOS.

The review authorizes only:

1. freezing the exact V2 scientific specification;
2. creating the guarded calibration runner;
3. executing the frozen synthetic calibration;
4. retaining the resulting PASS or FAIL.

It does **not** authorize:
- the reserved synthetic holdout automatically;
- BTC/ETH empirical AMS-DEP execution;
- Validation/OOS;
- strategy P&L;
- paper trading;
- live trading.

## Reviewer conclusions

The reviewer found no statistical-method change required before freezing V2.

Specifically ratified:
- same exact-time Parzen covariance/studentization for observed and bootstrap
  Wald statistics;
- null-imposed restricted-residual DWB;
- segment-centered restricted residuals;
- Gaussian Parzen dependent multipliers;
- `ell_s=max(2,n_s^(1/5))` using actual hour distances;
- zero covariance across declared continuity segments;
- 4,999 requested draws and `p=(1+exceedances)/5000`;
- no redraw of invalid draws; invalid draws count as exceedances;
- six-slot Holm family;
- all seven retained V1 DGPs;
- Student-t5, deterministic volatility-break, irregular-time and asynchronous
  stress DGPs;
- distinct calibration and unopened-holdout seed namespaces;
- 2,000 outer replications per DGP for calibration;
- separately reserved 2,000 outer replications per DGP for holdout;
- unchanged size/power/invalidity thresholds;
- deterministic 128-shard architecture;
- calibration-first / holdout-later version discipline.

The reviewer explicitly treated the fixed-X lagged-return predictor as a
documented theoretical transfer risk rather than a proven theorem. They judged
it acceptable to subject the exact frozen procedure to prospective Monte Carlo
calibration and later holdout, not acceptable as a reason to skip those gates.

## Required housekeeping identified by reviewer

Before calibration execution:
- synchronize release-gate engineering provenance to the reviewed successful
  engineering evidence;
- freeze/hash the exact V2 specification and code;
- create the guarded calibration runner;
- do not change scientific content while doing so.

## Reviewed-head reconciliation

The reviewer named engineering head:

`ee82f1625fce48900d00e4b61ad0e922aeb65451`

They also inspected the subsequently added ratification packet.

Repository comparison from that engineering head to
`690893781635e7179cbfe318d74a26e58c02fe73` shows exactly one added file:

`docs/AMS_DEP_V2_RATIFICATION_PACKET.md`

No statistical code, DGP, seed, threshold, bandwidth, restriction,
studentization, invalidity rule or governance helper changed in that diff.

Therefore the review is recorded as ratifying the scientific implementation
at `ee82f16...`, with the later packet treated as documentation-only.

Reviewed engineering evidence:
- run: `35456903336`
- result: SUCCESS
- 183 tests passed
- focused release-lock suite: 6 passed
- artifact: `10587774686`
- digest:
  `sha256:af6dc7622da0f313d37071766ce8fa29fa99accb25cbae7d5d56440bc4a4ff3e`

A later documentation-only head was also reverified successfully:
- run: `35456975333`
- artifact: `10587949263`
- no calibration or market-data access.

## Research-integrity rule after freeze

If calibration results cause any change to:
- bootstrap method;
- bandwidth/kernel;
- DGP definition;
- seed namespace;
- statistic/studentization;
- restriction family;
- invalidity policy;
- multiplicity;
- release threshold;
- result-affecting code;

then V2 remains the frozen historical experiment and the changed method becomes
V3. The reserved V2 holdout may not rescue a changed or failed V2 calibration.

## Authentication limitation

The repository records this as a user-supplied external/independent review.
The implementer can preserve the reviewer's self-attested independence but
cannot independently authenticate the reviewer's identity.
