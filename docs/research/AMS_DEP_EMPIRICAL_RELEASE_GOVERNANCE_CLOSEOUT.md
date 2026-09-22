# AMS-DEP separate empirical-release governance closeout — 2026-09-22

Status: **SEPARATE EMPIRICAL RELEASE APPROVED; DEVELOPMENT EXECUTION STILL LOCKED**.

## Independent decision

Issue #64 returned:

`APPROVE_SEPARATE_EMPIRICAL_RELEASE`

after independently reviewing the current governance head, the accepted V2 calibration/holdout evidence, the accepted full-pipeline certification, the production empirical-access boundary, source/data provenance checks, canonical sample/numerical semantics, and the machine-enforced separation between release approval and Development execution.

Reviewed governance head:

`90380637dcfe91dd5e9c78ec9de88b4f79b4d92f`

## Verified upstream chain

The independent review reconfirmed:

- independent V2 design approval;
- frozen V2 specification;
- successful V2 synthetic calibration;
- successful independently accepted one-shot synthetic holdout;
- consumed durable holdout claim;
- successful deterministic full-pipeline synthetic certification;
- independent acceptance of that certification in Issue #62;
- no result-affecting production/scientific drift between the accepted certification and the reviewed governance head.

The accepted full-pipeline certification remains bound to:

- run `35706223905`;
- execution SHA `b884658b7b7f231ba17015912a2f70d0ff11e803`;
- artifact `10684737205`;
- ZIP SHA-256 `588e95d70e9f0d2eb8d9f3bb5bf8c69d5a09b2542d29256422e3f4cdd37ec2cf`;
- JSON SHA-256 `7af3619dd9c901dc94fe99cc20ac952f279064d1dd5c4672eef6100f9c5337f5`.

## Governance transition

The canonical release gate now records:

- `status=SEPARATE_EMPIRICAL_RELEASE_APPROVED`;
- `separate_empirical_release_approved=true`.

The following remain false:

- `development_market_data_execution_authorized`;
- `validation_or_oos_access_authorized`;
- `strategy_pnl_authorized`;
- `paper_trading_authorized`;
- `live_trading_authorized`.

The release approval therefore does not itself permit any empirical BTCUSDT/ETHUSDT read.

## Two-key execution separation

The canonical guard `assert_ams_dep_empirical_release_allowed()` independently requires both:

- `separate_empirical_release_approved=true`; and
- `development_market_data_execution_authorized=true`.

After this closeout only the first condition is true.

The public empirical CLI and production access layer still cannot reach a market-data loader while Development execution authorization remains false.

## Remaining execution blocker

The current private function:

`_load_registered_development_bundle()`

is intentionally unconfigured and raises `EmpiricalAccessError`.

Before the first empirical Development execution, the project must therefore prepare a separate execution package that:

1. defines the exact local archive adapter/inventory to be used;
2. pins the implementation and source-inventory/provenance contract;
3. proves that only the registered BTCUSDT/ETHUSDT Development source universe can be reached;
4. preserves authoritative raw archive hashing and manifest/source/metadata identity checks;
5. preserves the fixed Development partition and all certified sample semantics;
6. exposes no Validation/OOS, gate override, arbitrary loader, P&L, paper, or live path;
7. obtains independent review before governance may set `development_market_data_execution_authorized=true`.

That work must remain pre-outcome: no empirical AMS-DEP result may be inspected while building or reviewing the adapter/execution package.

## Scope limit

This closeout does not establish that BTC/ETH dependence exists, that any AMS-DEP hypothesis is significant, or that any economic edge/profitability exists.

Validation/OOS, strategy P&L, paper trading, live trading, and the deferred directed 1/6/24-hour cross-asset diagnostics remain locked.
