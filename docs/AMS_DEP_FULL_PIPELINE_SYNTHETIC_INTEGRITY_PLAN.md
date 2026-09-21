# AMS-DEP full-pipeline synthetic integrity plan V1

Status: **REVISED AFTER ISSUE #59 REVIEW — REQUIRES INDEPENDENT RE-APPROVAL BEFORE IMPLEMENTATION**

## Purpose

The frozen AMS-DEP V2 numerical core passed calibration and its separately reserved one-shot synthetic holdout. The post-holdout machine gate records `v2_synthetic_holdout_passed=true` and `full_pipeline_synthetic_integrity_passed=false`.

This stage is the next mandatory release gate before any BTC/ETH empirical AMS-DEP execution. It is deterministic engineering/integrity certification, not a new trading experiment, not a second calibration, and not permission to inspect Development market outcomes.

The already reviewed upstream requirement is to exercise the real production sample-construction path on generated price/volume data and prove that a future empirical runner cannot silently alter the preregistered sample or open protected partitions.

Issue #59 identified several fail-closed gaps in the initial V1 proposal. This revision keeps FP-01 through FP-11 but freezes the missing source-bundle, exact-hour, numerical-wiring, multiplicity, provenance, and production-interface invariants before implementation.

## Strict firewall

This stage MUST NOT:

- read Binance BTCUSDT or ETHUSDT empirical archives;
- inspect Development market outcomes;
- access Validation or OOS;
- calculate strategy P&L;
- generate trading signals;
- paper trade or live trade;
- reuse calibration or holdout data/bootstrap seed namespaces;
- rerun, reset, delete, move, recreate, or repoint the consumed V2 holdout claim;
- modify the frozen V2 DGPs, inference method, Holm family, thresholds, or accepted holdout result.

All certification fixtures are generated locally and deterministically. Network access is unnecessary for the certification workflow.

## Pinned existing production components

V1 freezes the following existing production Git blobs **before implementation**:

| Production component | Frozen Git blob SHA-1 |
|---|---|
| `src/research_core/market_state.py` | `0d7a60bf581142bab5439ed93992839105d61e1f` |
| `src/research_core/data_quality_treatment_v2.py` | `f4876660fd88b91f0cfb9b9e87a8f9f09f1ddf19` |
| `src/research_core/data_ingestion.py` | `bbed81b3ffed215b04dc162368ef9866a4753875` |
| `src/research_core/data_interfaces.py` | `579b27b515d25ce69d565208416a88506286e534` |
| `src/research_core/dataset.py` | `236dcd2bc598a68b331788eb28a1b06e19d6cd12` |
| `src/research_core/dependence_statistics.py` | `c902bf2c8c85320933fcb8d0d1fd43e1d5fb694b` |
| `src/research_core/dependent_wild_bootstrap_v2.py` | `4e77f4576b85a4a35c3738d71e9b49315dd4f248` |
| `src/research_core/release_gate.py` | `14f283025fd217bbf5b5a248e3dac9ad38c4fb81` |
| `src/research_core/source_identity.py` | `8445e4bb1f36d0f9ef5f45961848bf8aea57c6f9` |
| `src/research_core/historical_dataset.py` | `7910e95b6f34a97e0034070884748b592a7b11d0` |

`source_identity.py` is the authoritative Gate 1A raw-archive-set identity implementation for this specification. The private `historical_dataset._archive_set_identity()` helper uses a different serialization and MUST NOT be substituted for the Gate 1A identity. If `historical_dataset.py` is used for archive reading/assembly, its behavior is also frozen by the blob above.

These are specification inputs, not files that implementation may silently edit. Any change to a pinned existing component before the first certification run invalidates this V1 specification and requires a versioned amendment plus independent review.

New implementation files cannot be pinned yet. After implementation review and **before the first certification run**, a separate implementation-freeze manifest must bind every new production runner/access/pipeline file, test, workflow, this plan, this machine registration, and all pinned existing components.

## Existing production logic that MUST be reused

The implementation must call, not reimplement:

- `research_core.market_state.build_market_states`;
- `research_core.data_quality_treatment_v2.build_manifest` and certified-segment/continuity helpers;
- `research_core.data_quality_treatment_v2.return_eligible`;
- `research_core.data_quality_treatment_v2.common_certified_intervals`;
- `research_core.data_ingestion.validate_dataset`, `content_hash`, and `dataset_identity` for returned normalized bars;
- `research_core.source_identity.source_identity` as the sole authoritative raw-archive-set identity algorithm for Gate 1A source binding;
- the exact Gate 1A manifest-identity construction used by `source_identity.bind_source_identity`: SHA-256 of canonical JSON over the full manifest record with `dataset_identity` removed and the bound `source_version` present, using `sort_keys=True`, separators `(",", ":")`, and `ensure_ascii=True`;
- `research_core.dependence_statistics.primary_design`;
- `research_core.dependence_statistics.RESTRICTIONS`;
- `research_core.dependence_statistics.SLOTS`;
- `research_core.dependence_statistics.holm_six`;
- `research_core.dependent_wild_bootstrap_v2.engineering_fixture` for bounded wiring only;
- `research_core.release_gate.assert_ams_dep_empirical_release_allowed` in the future canonical empirical access path.

The DWB engineering fixture is explicitly `ENGINEERING_ONLY_NOT_CALIBRATION`, has `p_value=None`, is limited to at most 32 engineering draws, and must never become a statistical release criterion.

## Canonical certified-data bundle

The future empirical path must use one canonical immutable certified-data bundle. The production row builder may not accept caller-supplied bars plus loose identity strings.

The bundle must contain, at minimum:

- requested partition name and exact half-open partition boundaries;
- normalized `MarketBar` sequence;
- `DatasetMetadata`;
- `ResearchTreatmentManifest`;
- exact source symbol;
- source/version metadata;
- treatment protocol version;
- normalization version;
- source integrity;
- research/partition certification;
- treatment-manifest `dataset_identity`;
- normalized-content `dataset_id`;
- normalized-content hash;
- complete loaded normalized timestamp inventory.

### Identity terminology is frozen

The preregistered BTC/ETH hashes are **Gate 1A treatment-manifest identities**, specifically `ResearchTreatmentManifest.dataset_identity`. They are not `data_ingestion.dataset_identity(bars)`.

Registered treatment-manifest identities:

- BTCUSDT: `1590cf8e69ed757eeb6701a218d561448beb2eb6ea09dcd0ae31d15a8f5197cf`;
- ETHUSDT: `d35bf21e309820abc88090bad29601adc1d1ea6b31dcddf0b80d510af4cf542f`.

The normalized-content `DatasetMetadata.dataset_id` and `content_hash` are separate runtime integrity values. They must be recomputed from the returned bars and must match the returned metadata, but V1 does not substitute them for the registered treatment-manifest identity.

### Treatment-manifest identity must be recomputed, not trusted

The returned `ResearchTreatmentManifest.dataset_identity` field is never trusted by string comparison alone.

Before state or row construction, the pipeline must:

1. take the complete returned manifest contents;
2. remove only the `dataset_identity` field;
3. serialize the remaining record exactly with `json.dumps(..., sort_keys=True, separators=(",", ":"), ensure_ascii=True)`;
4. SHA-256 that canonical JSON payload;
5. require:

`recomputed_manifest_identity == manifest.dataset_identity == registered_treatment_manifest_identity[symbol]`.

This recomputation therefore binds all result-affecting manifest contents, including source version, normalization/treatment versions, symbol/timeframe, research boundaries, anomaly IDs, affected regions, continuity breaks, exclusions, certified segments, partitions, source integrity, and certification.

A fixture must alter a certified segment or exclusion while deliberately leaving the stored `dataset_identity` unchanged and prove hard failure before state construction.

### Raw archive set must be rebound to the registered manifest

The authoritative raw-source identity algorithm is exactly `research_core.source_identity.source_identity(paths)`:

- sort raw archive paths by filename;
- for each archive form `(filename, sha256(file_bytes))`;
- JSON-serialize the ordered record list with separators `(",", ":")` and `ensure_ascii=True`;
- SHA-256 the resulting bytes.

For an authorized empirical load, the raw archive set actually opened by the canonical loader must be hashed with that exact algorithm. The resulting digest must equal the digest encoded in the registered manifest's `source_version`, which must have the exact form:

`binance-public-data-spot-1h:<64-lowercase-hex-source-identity>`.

The loader must also require any returned `DatasetMetadata.source_identity` used by the canonical bundle to equal this same authoritative `source_identity(paths)` value.

The private `historical_dataset._archive_set_identity()` digest is explicitly non-authoritative for this gate because it serializes filenames/digests differently. It may not satisfy or replace this check.

A fixture must alter one raw archive's bytes while keeping filenames, returned normalized-bar metadata, and stored manifest identity strings unchanged and prove hard failure before state/row construction.

## Two-stage empirical access contract

### Stage A — pre-load authorization

The production empirical access function must reject before any source loader executes unless:

1. requested partition is exactly `development`;
2. requested symbol is exactly BTCUSDT or ETHUSDT;
3. requested treatment-manifest identity equals the registered identity for that symbol;
4. requested Development boundaries equal `[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`;
5. the **canonical repository machine gate**, loaded from its fixed repository path, passes `assert_ams_dep_empirical_release_allowed`.

Production code must expose **no** CLI option, environment variable, generic path parameter, arbitrary gate object, or public callback parameter that can override the machine gate or loader.

Fabricated gates and synthetic loader substitution are permitted only in unit tests through private/internal seams or monkeypatching. They must not be reachable through the production CLI/public production API.

### Stage B — post-load bundle verification

After an authorized production loader returns and **before state construction, row construction, or inference**, the returned certified-data bundle must be verified.

Required checks:

- returned symbol equals requested symbol;
- every returned bar symbol is the expected canonical asset;
- source is exactly `Binance Public Data`;
- market is exactly `spot`;
- timeframe is exactly `1h`;
- timezone is exactly `UTC`;
- normalization version is exactly `gate1-v1`;
- treatment protocol version is exactly `gate1a-v1`;
- source integrity is exactly `SOURCE VERIFIED`;
- research and Development partition certification are only `VALID` or `VALID WITH DOCUMENTED EXCLUSIONS`;
- treatment-manifest identity equals the registered asset identity;
- treatment-manifest Development boundaries equal the frozen Development boundaries;
- metadata row count, start/end timestamps and symbol metadata match the returned bars;
- the treatment-manifest identity is recomputed from the complete returned manifest and equals both its stored identity and the registered asset identity;
- the raw archive set actually opened is hashed with authoritative `source_identity(paths)`, equals the digest embedded in manifest `source_version`, and equals the bundle's source-identity metadata where present;
- whole-bundle structural validation checks symbol, UTC/hour-grid alignment, strict ordering, duplicates and nonfinite/invalid bars;
- documented gaps are handled only by the frozen certified-segment rule below rather than by silently accepting an invalid whole-bundle report;
- each manifest-certified continuous segment is separately passed to `validate_dataset` and MUST return `valid=True`;
- every whole-bundle `missing_interval` timestamp MUST lie entirely inside a manifest-documented exclusion interval and outside all certified segments; any undocumented missing timestamp is a hard failure;
- no whole-bundle validation issue other than such fully accounted `missing_interval` findings is tolerated;
- recomputed normalized-content `dataset_identity(bars)` equals metadata `dataset_id`;
- recomputed `content_hash(bars)` equals metadata `content_hash`;
- no bar lies outside the requested Development interval;
- loaded timestamp inventory is exactly the inventory used by all later sample construction.

Wrong returned symbol, altered archive bytes, truncated/altered bars, stale or forged manifest identity, mismatched metadata, wrong manifest, unverified source, unusable certification, undocumented gaps, or boundary mismatch is a **hard source-integrity failure**, not a row exclusion.

## Exact-hour certified-segment invariant

`build_market_states` is defined for one already-certified continuous segment and works by row index. Therefore the canonical pipeline must prove hourly completeness **before calling it**.

For every certified segment used for state construction:

- segment boundaries are half-open UTC hours;
- the bars assigned to that segment must have timestamps exactly equal to every UTC hour from segment start through segment end minus one hour;
- adjacent timestamps must differ by exactly one hour;
- there may be no missing, duplicate, extra, out-of-order, or off-grid bar inside the segment;
- a loaded bar outside all certified segments may not be silently inserted into a segment.

Any mismatch between the loaded timestamp inventory and the manifest-certified grid is a hard source-integrity failure. The pipeline must **not** auto-create a new continuity segment, interpolate, compress time, or silently repair the manifest.

A dedicated synthetic oracle must delete one hour inside a purported certified segment and prove failure occurs before `build_market_states`.

## Canonical primary-row semantics

For a predictor bar with stored open timestamp `t`:

- `C_t` is known at `t + 1 hour`;
- `x_t = log(C_t/C_(t-1))`;
- `y_t = log(C_(t+1)/C_t)`;
- `t-1`, `t`, and `t+1` must all be exact hourly bars in the same certified continuity segment;
- state is the complete AMS-V1 state at bar `t`, never at `t+1`;
- row year is the UTC year of predictor availability `t+1h`;
- every input and label endpoint must lie within frozen Development;
- primary rows require a complete three-axis AMS-V1 state;
- no interpolation, forward fill, time compression, winsorization, nearest matching, or post-result exclusion is allowed.

The production empirical runner and the synthetic integrity harness must call the **same canonical row builder**. A second empirical row-definition path is forbidden.

## State-label translation into the numerical design

The only allowed translation from AMS-V1 volatility labels into `primary_design` is:

- `VOL_LOW -> LOW`;
- `VOL_NORMAL -> NORMAL`;
- `VOL_HIGH -> HIGH`.

No fallback, alias, default, partial-match, or unknown label is permitted.

## Frozen support rules

Each asset's primary inference is supported only if:

- eligible primary rows >= 5,000;
- each of the 15 calendar-year × volatility-state cells has >= 200 rows;
- each cell spans >= 10 distinct UTC availability dates.

Years: 2017, 2018, 2019, 2020, 2021.

Volatility states: `VOL_LOW`, `VOL_NORMAL`, `VOL_HIGH`.

Every cell must be emitted even when inadequate. The checker may not merge years/states, change date semantics, or lower thresholds.

DEP, TIME, and STATE for a given asset must use the exact same accepted primary-row sample, design matrix, target vector, actual-hour coordinate vector, and continuity-segment vector.

## Source and sample inventory accounting

The accounting universe begins **before** row filtering.

The canonical bundle must produce deterministic ordered inventories and SHA-256 digests for:

1. all loaded normalized source timestamps;
2. all candidate predictor timestamps in Development;
3. accepted predictor timestamps;
4. rejected predictor timestamps;
5. accepted row segment assignments.

A source/manifest mismatch is a hard integrity failure and is not allowed to disappear into row accounting.

Every candidate predictor timestamp must end in exactly one top-level outcome:

- accepted primary row; or
- rejected primary row with one or more explicit reason codes.

Registered row-level rejection codes:

- `PREVIOUS_ENDPOINT_UNAVAILABLE`
- `FORWARD_ENDPOINT_UNAVAILABLE`
- `CROSSES_CONTINUITY_BOUNDARY`
- `PREDICTOR_NOT_CERTIFIED`
- `INCOMPLETE_AMS_V1_STATE`
- `PROTECTED_PARTITION_ENDPOINT`
- `NONFINITE_RETURN`

`PREDICTOR_NOT_CERTIFIED` applies when an observed normalized predictor timestamp lies outside every certified segment because the treatment manifest deliberately excludes that region. It is not used for a mismatched certified grid; that is a hard integrity failure.

Reason counts may overlap, but the top-level accounting identity must hold exactly:

`candidate_rows = accepted_rows + rejected_rows`.

No loaded normalized timestamp may disappear silently before candidate construction.

## Numerical actual-hour and segment wiring

For every accepted primary row:

- numeric hour coordinate = integer UTC epoch hour derived directly from predictor timestamp `t`;
- hour coordinates may not be reindexed to `0,1,2,...`;
- actual gaps remain gaps;
- segment ID = immutable ordinal of the row's certified continuity segment in chronological manifest order;
- segment IDs may not recur after another segment;
- no row may be assigned across a segment boundary.

The exact `hours` and `segments` arrays passed to DWB/HAC must be the arrays produced by the canonical row builder.

A deterministic gap/break fixture must independently construct expected actual-hour coordinates and expected segment IDs and compare them element-for-element to the arrays entering the bounded DWB engineering fixture.

## Six-slot primary family and multiplicity wiring

The empirical primary result assembler must use the unchanged `dependence_statistics.SLOTS` ordering exactly:

1. BTC_DEP
2. BTC_TIME
3. BTC_STATE
4. ETH_DEP
5. ETH_TIME
6. ETH_STATE

The six raw p-value positions are always retained. An unavailable test remains `None` and is passed to the unchanged `holm_six`, which internally uses calculation p=1 while preserving unavailability.

No unavailable asset/test may be dropped to reduce the family.

A deterministic fabricated-p-value wiring fixture must prove:

- exact six-slot order;
- no slot is dropped;
- unavailable slots remain in family;
- `holm_six` output maps back to the same slot;
- DEP/TIME/STATE within each asset all use that asset's identical accepted primary sample.

This is wiring verification only. It does not recalibrate Holm or create a new statistical threshold.

## Cross-asset join scope

### Certified in this V1 gate

The canonical exact-timestamp join primitive must use set intersection by **actual predictor timestamp only**.

An asynchronous fixture must prove:

- BTC and ETH can have different missing timestamps;
- joined timestamps equal the exact intersection of accepted predictor timestamps;
- nearest-neighbor matching is prohibited;
- row-index matching is prohibited;
- no time compression occurs after gaps.

### Explicitly deferred and blocked

The preregistration also describes directed lagged cross-asset diagnostics at 1, 6, and 24 hours with full continuity in both assets.

Their exact directional endpoint/sample-builder semantics are not frozen by this V1 integrity specification. Therefore after a V1 full-pipeline PASS they remain:

`BLOCKED_PENDING_SEPARATE_CROSS_ASSET_LAG_INTEGRITY_SPEC`.

The future empirical runner must not expose contemporaneous/lagged diagnostic execution beyond the exact intersection primitive certified here unless a later versioned synthetic-integrity specification freezes and tests the full 1/6/24-hour endpoint/continuity semantics.

V1 PASS must never be cited as proof that those deferred lagged diagnostic samples are valid.

## Registered integrity oracles

### FP-01 — AMS-V1 warm-up

On a continuous generated price/volume path:

- no complete AMS-V1 state exists before index 744;
- index 744 may be the first complete state when history is sufficient;
- future-bar mutation cannot alter a past state.

### FP-02 — continuity and exact-hour fail-closed behavior

Using the real treatment manifest and certified segments:

- declared breaks are never bridged;
- no return spans a break;
- state warm-up restarts after a break;
- the second segment cannot produce a complete state before its own 744-bar warm-up;
- every segment is verified against its exact hourly grid before state construction;
- an undeclared missing hour inside a purported certified segment causes hard failure before `build_market_states`;
- the pipeline does not silently auto-segment or repair that mismatch.

### FP-03 — row timing and endpoints

The canonical row builder must prove:

- x uses `t-1 -> t`;
- y uses `t -> t+1`;
- state comes from t;
- row year uses availability `t+1h`;
- a Development-end predictor whose forward label would enter Validation is rejected;
- all accepted endpoints share one certified segment.

### FP-04 — complete-state selection and label translation

- any unavailable AMS-V1 axis excludes the row;
- no partial state is promoted;
- the only volatility mapping is `VOL_LOW->LOW`, `VOL_NORMAL->NORMAL`, `VOL_HIGH->HIGH`;
- unknown labels fail hard.

### FP-05 — support enforcement

Deterministic fixtures must:

- pass all 5,000-row and 15-cell thresholds;
- fail total-row support;
- fail one cell's 200-row minimum;
- fail one cell's 10-distinct-date minimum;
- report all 15 cells in every outcome.

### FP-06 — source/sample inventory and exclusion accounting

Fixtures must prove:

- loaded source timestamp inventory is recorded before row filtering;
- candidate, accepted, rejected, and segment-assignment inventories/digests are deterministic;
- every candidate is accepted or rejected;
- `candidate = accepted + rejected`;
- deliberate manifest exclusions use `PREDICTOR_NOT_CERTIFIED`;
- a source/manifest grid mismatch is a hard failure rather than a row exclusion;
- no timestamp disappears silently upstream.

### FP-07 — exact BTC/ETH join and deferred lagged diagnostics

- asynchronous synthetic accepted-row sets join by exact predictor timestamp intersection only;
- row-index and nearest-time alternatives demonstrably differ and are rejected;
- time is not compressed;
- the 1/6/24-hour directed lagged cross-asset diagnostics remain explicitly blocked after V1 unless a separate integrity spec is later approved.

### FP-08 — numerical design, hours, segments, restrictions, DWB, and Holm wiring

Accepted rows must feed unchanged numerical primitives:

- `primary_design` returns 14 columns;
- `VOL_*` labels translate exactly to LOW/NORMAL/HIGH;
- DEP indices remain 7..13;
- TIME remain 8..11;
- STATE remain 12..13;
- actual epoch-hour coordinates from predictor timestamps are passed without reindexing;
- certified-segment ordinals are passed without collapse/recurrence;
- an independent gap/break fixture matches exact expected hour and segment arrays;
- bounded `engineering_fixture` returns `ENGINEERING_ONLY_NOT_CALIBRATION` and `p_value=None`;
- six-slot `SLOTS` ordering and `holm_six` assembly are verified with fabricated p-values;
- unavailable slots remain in the six-test family;
- each asset's three primary hypotheses share the exact same accepted sample, design matrix, target vector, actual-hour vector, and segment vector.

No engineering fixture or fabricated-p-value result is a statistical release criterion.

### FP-09 — two-stage source identity/certification fail-closed

Pre-load tests reject before source access:

- wrong partition;
- wrong symbol;
- wrong registered treatment-manifest identity;
- altered Development boundaries;
- current locked machine gate.

Post-load tests reject before row/state construction:

- wrong returned symbol;
- altered/truncated bar content;
- metadata/content-hash/dataset-ID mismatch;
- wrong timeframe/timezone/source/market;
- wrong normalization or treatment version;
- unverified source;
- unusable certification;
- forged/stale treatment-manifest identity, including changed segment/exclusion content with unchanged stored identity;
- raw archive bytes whose authoritative `source_identity(paths)` differs from the identity embedded in manifest `source_version`;
- bundle source-identity metadata inconsistent with the authoritative raw-source identity;
- use of the non-authoritative `historical_dataset._archive_set_identity()` as a substitute for Gate 1A source identity;
- partition boundary mismatch;
- certified-segment grid mismatch;
- any documented-exclusion gap whose timestamps are not exactly covered by manifest exclusions;
- any certified segment that fails `validate_dataset(...).valid is True`;
- any whole-bundle validation issue other than `missing_interval` findings exactly and completely accounted for by registered manifest exclusions.

### FP-10 — protected read and production-interface blocking

Tests must prove:

- current machine state blocks Development before the production loader is invoked;
- Validation is always blocked before loader invocation;
- OOS is always blocked before loader invocation;
- with a fabricated fully authorized gate in **test-only internal plumbing**, only Development can reach a synthetic test loader;
- production CLI/public API exposes no gate path, gate object, gate environment override, arbitrary loader callback, or partition override capable of bypassing the canonical repository machine gate;
- post-load bundle verification occurs before state/row/inference code.

No real source is opened in these tests.

### FP-11 — immutable/provenance output inventory

The certification report must contain:

- classification and version;
- code commit;
- SHA-256 of this plan and machine registration;
- expected and observed Git blob identities for every pinned existing production component, including `source_identity.py` and `historical_dataset.py`;
- implementation-freeze-manifest identity for all new implementation files;
- deterministic fixture identities;
- oracle-by-oracle PASS/FAIL;
- authoritative raw archive-set identity, manifest-embedded raw-source identity, recomputed treatment-manifest identity, normalized-content dataset ID/content hash, and their equality checks;
- whole-bundle validation findings plus exact documented-gap accounting;
- loaded/candidate/accepted/rejected timestamp counts and SHA-256 digests;
- accepted segment-assignment digest;
- exclusion reason counts;
- all 15 support cells per asset;
- exact join counts and digest;
- actual-hour and segment-vector digests entering DWB;
- exact six-slot assembly record;
- explicit deferred-cross-asset-lag status;
- access flags;
- `market_data_accessed=false`;
- `development_market_outcomes_accessed=false`;
- `validation_or_oos_accessed=false`;
- `strategy_pnl_calculated=false`;
- `paper_trading_authorized=false`;
- `live_trading_authorized=false`.

If any expected pinned blob differs from the registration, certification fails before fixtures execute.

## Certification decision

The full-pipeline integrity result is binary:

- `FULL_PIPELINE_SYNTHETIC_INTEGRITY_PASS`, only if FP-01 through FP-11 all pass; or
- `FULL_PIPELINE_SYNTHETIC_INTEGRITY_FAIL`.

There is no score, weighted partial pass, or threshold tuning.

Implementation defects may be fixed and the deterministic engineering suite rerun **before acceptance**, but the registered oracle definitions, row semantics, source-bundle contract, blob pins, or firewall rules may not be weakened after certification evidence exists. A material change requires a versioned amendment and independent review.

## Proposed implementation surface after specification approval

Only after independent re-approval may implementation add:

- `src/research_core/ams_dep_pipeline.py` — canonical bundle validation, exact-hour segmentation, primary row construction, support/accounting, exact join, numerical vectors;
- `src/research_core/ams_dep_empirical_access.py` — canonical production access with fixed repository gate and two-stage verification;
- `research/scripts/run_ams_dep_full_pipeline_integrity.py`;
- `research/scripts/run_ams_dep_empirical.py` — fail-closed production shell with no gate/loader override;
- `tests/test_ams_dep_full_pipeline_integrity.py`;
- `tests/test_ams_dep_empirical_firewall.py`;
- `.github/workflows/ams-dep-full-pipeline-integrity.yml`;
- `research/governance/ams_dep_full_pipeline_implementation_freeze_v1.json`.

Before the first certification run, the implementation-freeze manifest must be independently reviewed and bind all new result-affecting files plus the pinned existing components.

Existing pinned production components and frozen V2 scientific files must not be modified under this V1 implementation. In particular, implementation may not choose between competing raw-source identity algorithms: `source_identity.source_identity` is frozen as authoritative, and `historical_dataset._archive_set_identity` is not a valid substitute.

## Release consequence

A PASS supports only a later governance proposal to set:

`full_pipeline_synthetic_integrity_passed=true`.

It does **not** set or imply:

- `separate_empirical_release_approved=true`;
- `development_market_data_execution_authorized=true`;
- Validation/OOS access;
- strategy P&L;
- paper trading;
- live trading;
- authorization of the deferred directed 1/6/24-hour cross-asset diagnostics.

Those remain separate later gates.
