# AMS-DEP V2 synthetic holdout governance closeout — 2026-09-21

Status: **HOLDOUT PASS ACCEPTED; ONE-SHOT EXECUTION CONSUMED; EMPIRICAL RELEASE STILL LOCKED**.

## Independent acceptance

Issue #56 returned:

`ACCEPT_V2_SYNTHETIC_HOLDOUT_PASS`

after independently reviewing the original GitHub aggregate artifact, exact execution provenance, frozen/safety blob identities, the aggregate arithmetic, and the one-shot claim.

## Accepted execution evidence

- workflow run: `35529411234`
- execution SHA: `80d0fb5a90a6c4dc02073605159c38f520ad3410`
- aggregate job: `106443566096`
- aggregate artifact: `10655486394`
- artifact ZIP SHA-256:
  `0208861fc4dbeed2d6dda1a6b574678eb59957e628f1a521ba6c56227ef5435d`
- summary SHA-256:
  `ad66d2a8b153e9e98209e82dbb475de4a7714d178233e0ebb0d7d6a749a01ebd`
- compressed outer-ledger SHA-256:
  `089b5be7b049090a22be17c04b266e0247c384df58f06ee3a2090bfb795cbb5d`
- durable one-shot claim:
  `refs/tags/ams-dep-v2-holdout-execution-claimed-v1`
- claim target:
  `80d0fb5a90a6c4dc02073605159c38f520ad3410`

The claim must not be deleted, moved, recreated, or repointed.

## Accepted statistical result

The unchanged frozen V2 holdout screen passed.

Independent audit established:

- 22000 exact DGP/outer families;
- 132000 ordered primary slot tests;
- zero missing, duplicate, or extra DGP/outer coordinates;
- all 22000 six-slot Holm decisions independently recomputed with zero mismatches;
- all 219 summary metric objects independently recomputed with zero mismatches;
- all registered false-rejection rates below the frozen 7.5% ceiling;
- all six registered power targets above the frozen 80% floor;
- original invalidity zero throughout;
- pooled bootstrap invalidity zero throughout;
- maximum per-outer bootstrap invalid fraction zero throughout.

This is synthetic inference evidence only. It is not evidence of market predictability or profitability.

## Governance transition

The post-holdout machine state now records:

- `status=V2_SYNTHETIC_HOLDOUT_PASSED`;
- `v2_synthetic_holdout_passed=true`;
- `v2_holdout_execution_authorized=false`;
- holdout addendum `status=CONSUMED_PASS_RECORDED`;
- `explicit_holdout_execution_authorized=false`;
- `reserved_holdout_seeds_consumed=true`.

The following remain false:

- `full_pipeline_synthetic_integrity_passed`;
- `separate_empirical_release_approved`;
- `development_market_data_execution_authorized`;
- `validation_or_oos_access_authorized`;
- `strategy_pnl_authorized`;
- `paper_trading_authorized`;
- `live_trading_authorized`.

## Historical execution provenance preserved

The authorized execution manifest is intentionally **not modified after execution**. It remains the historical bundle against which the completed run was authorized and bound.

Execution-manifest Git blob at closeout branch creation:

`c07967f4e46a0d324b1db323276c88de3df1f050`

Recorded execution-manifest SHA-256:

`3d20b86f25ac5d3bdf938b4c4832269429da0495300a3c4c6d2ccaceaa073dba`

The result artifact remains explicitly bound to that historical execution provenance.

## Next valid gate

The next valid gate is **full-pipeline synthetic integrity**.

That gate must exercise production-pipeline properties that were intentionally outside the numerical-core holdout, including actual pipeline/join/state handling and the other unresolved full-pipeline synthetic integrity requirements in the numerical contract and related review artifacts.

Only after independent acceptance of full-pipeline synthetic integrity may the project separately consider:

1. separate empirical-release approval; and
2. Development market-data execution authorization.

Validation/OOS remains a later protected boundary. Strategy P&L, paper trading, and live trading remain locked.
