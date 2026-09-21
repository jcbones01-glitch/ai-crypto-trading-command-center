# AMS-DEP full-pipeline synthetic integrity plan V1

Status: **PROPOSED FOR INDEPENDENT REVIEW — NO EMPIRICAL MARKET-DATA ACCESS AUTHORIZED**

## Purpose

The frozen AMS-DEP V2 numerical core has passed calibration and its separately reserved one-shot synthetic holdout. The machine gate now records that holdout PASS, but `full_pipeline_synthetic_integrity_passed=false`.

This stage is the next mandatory release gate before any BTC/ETH empirical AMS-DEP execution. It is an engineering/integrity certification, not a new trading experiment, not a second calibration, and not permission to inspect Development market outcomes.

The design requirement already frozen in `AMS_DEP_V2_INFERENCE_DESIGN_REVIEW.md` is to exercise the real production sample-construction path on generated price/volume data and prove that protected samples cannot be read.

## Strict firewall

This stage MUST NOT:

- read Binance BTCUSDT or ETHUSDT empirical archives;
- access Development market outcomes;
- access Validation or OOS;
- calculate strategy P&L;
- generate trading signals;
- paper trade or live trade;
- reuse calibration or holdout data/bootstrap seed namespaces;
- rerun the consumed V2 holdout;
- modify the frozen V2 DGPs, inference method, Holm family, thresholds, or holdout result.

All fixtures are generated locally and deterministically in memory. Network access is unnecessary for the certification workflow.

## Existing production components that MUST be exercised

The implementation must call the existing production modules rather than reimplementing their logic in the test harness:

- `research_core.market_state.build_market_states` — unchanged AMS-V1 state construction;
- `research_core.data_quality_treatment_v2.build_manifest` and certified-segment/continuity helpers;
- `research_core.data_quality_treatment_v2.return_eligible`;
- `research_core.data_quality_treatment_v2.common_certified_intervals`;
- `research_core.dependence_statistics.primary_design`;
- `research_core.dependence_statistics.RESTRICTIONS`;
- `research_core.dependent_wild_bootstrap_v2.engineering_fixture` for bounded wiring only;
- `research_core.release_gate.assert_ams_dep_empirical_release_allowed` in any future empirical runner path.

The DWB engineering fixture is explicitly `ENGINEERING_ONLY_NOT_CALIBRATION`, has no p-value, uses only the reserved engineering namespace, and is not a statistical release screen.

## Canonical primary-row semantics

For a predictor bar with stored open timestamp `t`:

- `C_t` is known at `t + 1 hour`;
- `x_t = log(C_t / C_(t-1))`;
- `y_t = log(C_(t+1) / C_t)`;
- `t-1`, `t`, and `t+1` must all be exact hourly bars in the same certified continuity segment;
- state is the complete AMS-V1 state at bar `t`, never the state at `t+1`;
- row year is the UTC year of predictor availability time `t + 1 hour`;
- every input and label bar must lie inside Development `[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`;
- primary rows require all three AMS-V1 state axes to be complete;
- no interpolation, forward fill, time compression, winsorization, nearest matching, or post-result exclusion is allowed.

The future empirical path must use one canonical row builder implementing these exact rules.

## Frozen support rules

Each asset's primary inference is supported only if:

- eligible primary rows >= 5,000;
- each of the 15 calendar-year × volatility-state cells has >= 200 rows;
- each of those 15 cells spans >= 10 distinct UTC availability dates.

Calendar years are 2017, 2018, 2019, 2020, 2021.
Volatility states are `VOL_LOW`, `VOL_NORMAL`, `VOL_HIGH`.

Every cell must be reported even if inadequate. The support checker may not merge years/states or lower thresholds.

## Exclusion accounting

Every observed candidate predictor bar in the requested Development interval must end in exactly one of two top-level outcomes:

- accepted primary row; or
- rejected primary row with one or more explicit reason codes.

Registered reason codes:

- `PREVIOUS_ENDPOINT_UNAVAILABLE`
- `FORWARD_ENDPOINT_UNAVAILABLE`
- `CROSSES_CONTINUITY_BOUNDARY`
- `INCOMPLETE_AMS_V1_STATE`
- `PROTECTED_PARTITION_ENDPOINT`
- `NONFINITE_RETURN`

Reason counts may overlap because one rejected candidate can violate more than one condition. The report must also include an exact accounting identity:

`candidate_rows = accepted_rows + rejected_rows`.

The set of rejected predictor timestamps must be retained so the accounting is reproducible.

## Cross-asset join rule

Cross-asset diagnostics must use exact intersection by predictor bar timestamp only.

The implementation must prove on an asynchronous synthetic fixture that:

- BTC and ETH can have different missing timestamps;
- the joined set equals the exact set intersection of accepted predictor timestamps;
- no nearest-neighbor match is permitted;
- no row-index match is permitted;
- no time compression occurs after gaps.

The registered asynchronous pattern from V2 may be reused as an engineering fixture:

- BTC missing offsets divisible by 97;
- ETH missing offsets divisible by 89;
- ETH additional missing block `[1000,1024)`.

This reuse is for timing/join integrity only and does not consume the frozen V2 holdout namespace.

## Protected-partition read firewall

A future empirical loader/runner must fail before any data-loader callback executes unless all of the following are true:

1. requested partition is exactly `development`;
2. the machine empirical release gate passes;
3. requested source/certification/dataset identity matches the preregistered asset identity.

Validation and OOS must be rejected even when a fabricated test gate otherwise grants empirical Development release.

Current repository state must reject even Development empirical reads because:

- `full_pipeline_synthetic_integrity_passed=false`;
- `separate_empirical_release_approved=false`;
- `development_market_data_execution_authorized=false`.

Tests must use injected synthetic callbacks and prove blocked callbacks are never invoked.

Expected empirical dataset identities remain:

- BTC: `1590cf8e69ed757eeb6701a218d561448beb2eb6ea09dcd0ae31d15a8f5197cf`;
- ETH: `d35bf21e309820abc88090bad29601adc1d1ea6b31dcddf0b80d510af4cf542f`.

## Registered integrity oracles

### FP-01 — AMS-V1 warm-up

On a continuous generated price/volume path:

- no complete AMS-V1 state exists before index 744;
- index 744 is eligible to become the first complete state when all required history exists;
- future-bar mutation cannot alter a past state.

### FP-02 — continuity reset

Using the real treatment manifest and certified segments:

- a declared break is never bridged;
- no return spans the break;
- state warm-up restarts after the break;
- the second segment cannot produce a complete state before its own 744-bar warm-up.

### FP-03 — row timing and endpoints

The canonical row builder must prove:

- x uses `t-1 -> t`;
- y uses `t -> t+1`;
- state comes from t;
- row year uses availability `t+1h`;
- a Development-end predictor whose forward label requires a Validation bar is rejected.

### FP-04 — complete-state selection

Rows with any unavailable AMS-V1 axis are excluded. No partial state is promoted to the primary sample.

### FP-05 — support enforcement

The checker must have deterministic fixtures that:

- pass all 5,000-row and 15-cell thresholds;
- fail total-row support;
- fail a single cell's 200-row minimum;
- fail a single cell's 10-distinct-date minimum.

All 15 cells are reported in every case.

### FP-06 — exclusion accounting

For fixtures containing warm-up losses, continuity breaks, endpoint losses and protected-boundary losses:

- every candidate timestamp is accepted or rejected;
- no timestamp disappears silently;
- exact candidate = accepted + rejected identity holds;
- reason counts and rejected timestamps are emitted.

### FP-07 — exact BTC/ETH join

The asynchronous fixture must produce an exact timestamp intersection and must demonstrate that row-index and nearest-time joins would differ.

### FP-08 — design/restriction wiring

Accepted rows must feed the unchanged numerical core:

- `primary_design` returns exactly 14 columns;
- DEP restriction indices remain 7..13;
- TIME remain 8..11;
- STATE remain 12..13;
- a bounded DWB `engineering_fixture` executes with `classification=ENGINEERING_ONLY_NOT_CALIBRATION` and `p_value=None`.

No engineering-fixture result is a pass/fail statistical criterion.

### FP-09 — source identity/certification fail-closed

A future empirical request must reject:

- wrong symbol;
- wrong dataset identity;
- uncertified source;
- altered partition boundaries;

before numerical inference.

### FP-10 — protected read blocking

Tests must prove:

- current machine state blocks Development before the loader callback;
- Validation is blocked before the callback;
- OOS is blocked before the callback;
- with a fabricated fully authorized Development-only gate, only Development can reach an injected synthetic loader.

No real source is opened in these tests.

### FP-11 — output inventory

The certification report must contain:

- classification and version;
- code commit;
- hashes of this plan and machine-readable registration;
- production-component Git blob identities;
- fixture identities;
- oracle-by-oracle PASS/FAIL;
- candidate/accepted/rejected row counts;
- exclusion reason counts;
- all 15 support cells per asset;
- exact join counts;
- access flags;
- explicit `market_data_accessed=false`;
- explicit `validation_or_oos_accessed=false`;
- explicit `strategy_pnl_calculated=false`;
- explicit `paper_trading_authorized=false`;
- explicit `live_trading_authorized=false`.

## Certification decision

The full-pipeline integrity result is binary:

- `FULL_PIPELINE_SYNTHETIC_INTEGRITY_PASS`, only if FP-01 through FP-11 all pass; or
- `FULL_PIPELINE_SYNTHETIC_INTEGRITY_FAIL`.

There is no statistical score, weighted partial pass, or threshold tuning.

Implementation defects may be fixed and the deterministic engineering suite rerun, but the registered oracle definitions may not be weakened after the first certification attempt. Any material change to the oracle set or row semantics requires a new version and independent review.

## Proposed implementation surface

After independent approval of this plan, implementation may add:

- `src/research_core/ams_dep_pipeline.py`;
- `src/research_core/ams_dep_empirical_access.py`;
- `research/scripts/run_ams_dep_full_pipeline_integrity.py`;
- a fail-closed `research/scripts/run_ams_dep_empirical.py` shell that cannot read data under current gates;
- `tests/test_ams_dep_full_pipeline_integrity.py`;
- `tests/test_ams_dep_empirical_firewall.py`;
- `.github/workflows/ams-dep-full-pipeline-integrity.yml`.

Existing frozen V2 numerical/scientific files must not be modified.

## Release consequence

A PASS permits only a later governance proposal to set:

`full_pipeline_synthetic_integrity_passed=true`.

It does **not** set or imply:

- `separate_empirical_release_approved=true`;
- `development_market_data_execution_authorized=true`;
- Validation/OOS access;
- strategy P&L;
- paper trading;
- live trading.

Those remain separate later gates.
