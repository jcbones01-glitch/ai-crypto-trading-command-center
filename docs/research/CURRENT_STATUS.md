# Current research handoff

Snapshot: 2026-09-22. Recheck live repository and Actions state before acting.

## Authority

Controlling gate: [ams_dep_release_gate_v1.json](../../research/governance/ams_dep_release_gate_v1.json).

AMS-DEP V2 synthetic calibration passed. The separately authorized one-shot synthetic holdout passed, was independently accepted in Issue #56, and remains consumed. The deterministic full-pipeline synthetic integrity certification passed in run `35706223905`, was independently accepted in Issue #62, and was closed out through PR #63.

Issue #64 then independently returned:

`APPROVE_SEPARATE_EMPIRICAL_RELEASE`.

The current closeout state records:

- `full_pipeline_synthetic_integrity_passed=true`;
- `separate_empirical_release_approved=true`;
- `development_market_data_execution_authorized=false`;
- `validation_or_oos_access_authorized=false`;
- `strategy_pnl_authorized=false`;
- `paper_trading_authorized=false`;
- `live_trading_authorized=false`.

No empirical BTCUSDT/ETHUSDT execution is authorized yet.

## Completed AMS-DEP synthetic evidence

### V2 calibration

Run `35460656875` completed successfully and the frozen calibration screen passed. The aggregate artifact was independently audited.

### V2 one-shot holdout

Run `35529411234` completed successfully and reported `AMS_DEP_V2_HOLDOUT_PASS`.

Issue #56 independently accepted the result. The one-shot claim remains consumed and immutable.

### Full-pipeline synthetic integrity

Run `35706223905` executed at:

`b884658b7b7f231ba17015912a2f70d0ff11e803`.

Certification emitted:

`FULL_PIPELINE_SYNTHETIC_INTEGRITY_PASS`.

Issue #62 independently accepted the original artifact after direct re-download/re-hashing and FP-01 through FP-11 review.

The reviewed/certified implementation was merged through PR #60. The governance closeout was merged through PR #63 at:

`90380637dcfe91dd5e9c78ec9de88b4f79b4d92f`.

See [AMS_DEP_FULL_PIPELINE_GOVERNANCE_CLOSEOUT.md](AMS_DEP_FULL_PIPELINE_GOVERNANCE_CLOSEOUT.md).

## Separate empirical-release review accepted

Issue #64 independently verified the upstream release chain, current machine-gate state, source/data provenance contract, canonical sample/numerical semantics, and two-key separation between release approval and Development execution.

Its decision authorizes governance to record only:

`separate_empirical_release_approved=true`.

It explicitly does not authorize Development market-data execution.

See [AMS_DEP_EMPIRICAL_RELEASE_GOVERNANCE_CLOSEOUT.md](AMS_DEP_EMPIRICAL_RELEASE_GOVERNANCE_CLOSEOUT.md).

## Remaining Development execution blocker

The production empirical access path still contains an intentionally unconfigured private Development adapter:

`_load_registered_development_bundle()`.

The canonical machine gate also still requires:

`development_market_data_execution_authorized=true`

before any market-data read is reachable.

Therefore the next bounded AMS-DEP task is to prepare, freeze, and independently review the exact Development source adapter/inventory and first empirical execution package without opening empirical outcomes.

That package must preserve:

- BTCUSDT/ETHUSDT only;
- Development only:
  `[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`;
- registered treatment-manifest identities;
- authoritative raw archive `source_identity(paths)`;
- manifest/source/metadata identity equality;
- normalized dataset/content recomputation;
- certified-segment/hour-grid enforcement;
- canonical row/accounting/support semantics;
- exact numerical/multiplicity wiring;
- no Validation/OOS access;
- no P&L;
- no paper/live trading;
- no deferred directed 1/6/24-hour lag diagnostics.

Only after that package passes independent review may governance consider setting:

`development_market_data_execution_authorized=true`.

## Other research work

The R05 global search-ledger / selection-inference specification remains a separate future research-governance task. It must not be used to bypass the AMS-DEP release sequence.
