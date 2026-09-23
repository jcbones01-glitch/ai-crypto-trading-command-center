# AMS-DEP Development empirical execution recovery specification V2

Status: **PROPOSED — PRE-IMPLEMENTATION — NO V2 MARKET-DATA ACCESS AUTHORIZED**

Parent incident: Issue #71  
Parent V1 execution run: `35834431025`  
Parent V1 artifact: `10738551310`  
Consumed V1 claim: `refs/tags/ams-dep-development-execution-claimed-v1`

## 1. Purpose

This specification defines a narrowly scoped V2 recovery from the consumed AMS-DEP Development V1 source-construction incident.

V1 did **not** produce an empirical AMS-DEP result. It failed at `SOURCE_BTCUSDT` before primary-sample construction, numerical inference, p-values, Holm adjustment, Validation/OOS, P&L, paper trading, or live trading.

The independently accepted incident classification is that V1 combined two individually intentional behaviors that were incompatible in sequence:

1. Gate 1A `scan_archive()` classifies localized bad raw rows, including `NON_ALIGNED_TIMESTAMP`, as explicit source-quality events and permits deterministic treatment/exclusion semantics; but
2. the later V1 normalization pass re-read the same raw archive through strict `read_archive()`, which aborts immediately on such a row before the treatment can be realized.

V2 repairs **only that source-normalization seam**. It does not rescue a statistical result, change a hypothesis, lower a threshold, alter a bootstrap method, change multiplicity, or open any protected downstream scope.

## 2. Immutable V1 incident

V1 is permanently consumed.

The following must remain immutable historical evidence:

- reviewed V1 candidate: `ccd825c92208030adf59d9f383aaa8ae806381db`;
- V1 execution head / claim target: `969f6aeadda4143b0882b8e9169e3f6dd9c177ed`;
- V1 run: `35834431025`, attempt 1;
- V1 artifact: `10738551310`;
- artifact ZIP SHA-256: `b947d8a9d73dd05da0455ad8c1fb7ab845f4a187ff56ec99856b385fc0e403c7`;
- `result.json` SHA-256: `19f53015e725526b8baa8da89fec5cdbf58d7e6f9a1985fcc626309ab0e2cca7`;
- V1 claim: `refs/tags/ams-dep-development-execution-claimed-v1`.

V2 must never delete, repoint, recreate, or reuse the V1 claim. V1 must never be rerun.

The V1 artifact is incident/provenance evidence only. It is not an empirical input dataset for V2.

## 3. Contract precedence

Conflicts resolve in this order:

1. **this V2 recovery specification and its machine registration** control treatment-aware raw-row normalization, V2 projection/accounting, V2 execution/versioning, and V2 one-shot governance;
2. **the accepted V1 Development execution specification/registration** control every first-Development invariant not explicitly overridden here, including source universe, Development boundary, support, primary sample, DWB inference, multiplicity, protected scope, and output discipline;
3. **the accepted full-pipeline contract** controls canonical sample/state/support/join semantics;
4. **the frozen AMS-DEP numerical V2 contract** controls the statistical method;
5. historical preregistration remains provenance only where later controlling contracts explicitly adopt it.

V2 does **not** amend the frozen numerical method or the primary estimand.

## 4. Exact source universe remains unchanged

Assets remain exactly:

- `BTCUSDT`;
- `ETHUSDT`.

Source remains:

- Binance Public Data;
- spot;
- 1-hour;
- UTC;
- monthly archives from 2017-08 through 2021-12 inclusive;
- exactly 53 archives per asset and 106 total;
- Development partition exactly `[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`.

V2 must independently reacquire archives after the V2 one-shot claim from the same official `data.binance.vision` URLs and verify each official `.CHECKSUM`.

V2 must not use a V1 local download/cache as source input.

### 4.1 BTC V1 incident checksum continuity

The V1 incident artifact already exposed and cryptographically preserved all 53 BTC official checksum values.

The V2 machine registration therefore prospectively pins those 53 BTC checksum values as parent-incident continuity evidence.

For every BTC archive in V2:

`current_official_checksum == V1_incident_official_checksum == V2_local_zip_sha256`.

Any mismatch is a hard source-integrity failure requiring separate review. V2 may not silently accept provider byte drift.

V1 never reached ETH acquisition. Therefore no ETH checksum may be invented or retrospectively preregistered. V2 must require:

`V2_current_official_checksum == V2_local_zip_sha256`

for all 53 ETH archives and record the resulting source identity prospectively during the authorized V2 execution.

## 5. Frozen Gate 1A classifications remain unchanged

V2 must reuse the existing frozen:

- `data_quality.scan_archive`;
- `data_quality_treatment_v2.event_id`;
- `data_quality_treatment_v2.build_manifest`;
- `source_identity`;
- strict `data_ingestion.normalize_row` for rows that are accepted for normalization.

V2 must **not** redefine anomaly types or localization rules.

No recovery may:

- round a timestamp;
- shift/snap a timestamp;
- interpolate a bar;
- synthesize a bar;
- resample;
- repair OHLC/volume;
- silently discard an arbitrary exception;
- add a special case for the observed V1 error only.

## 6. Treatment-aware raw-row normalization V2

V2 introduces one deterministic normalization algorithm after scanning and manifest construction.

For each expected archive:

1. verify checksum and archive identity under the frozen source contract;
2. run frozen `scan_archive(path, symbol, checksum_verified=True)`;
3. build the Development treatment manifest from the complete 53-report asset set;
4. require source integrity `SOURCE VERIFIED`;
5. require Development certification `VALID` or `VALID WITH DOCUMENTED EXCLUSIONS`;
6. if any non-checksum event has `parsed_timestamp is None`, hard-fail the asset as unlocalized/`UNUSABLE`;
7. open each archive and enumerate the same physical CSV row numbers used by `scan_archive`;
8. skip blank rows exactly as the scanner does; every remaining row is a `raw_data_row`;
9. obtain all scanner events whose `event.row` equals that physical row number.

### 6.1 Accepted raw row

A raw row is accepted for normalization only when it has **zero row-level scanner events**.

For such a row, call frozen `normalize_row(row, symbol)`.

If `normalize_row` now raises any exception, V2 must hard-fail with a scanner/normalizer mismatch. It may not catch-and-skip that row.

### 6.2 Explicitly rejected raw row

A raw row with one or more scanner events is rejected from normalized-bar construction only if all of the following hold:

- every event is tied to that exact physical row number;
- every event has a non-null `parsed_timestamp`;
- every event's frozen `event_id(event)` exists in the manifest anomaly-ID set;
- for any event whose canonical affected hour lies inside Development, that event ID is referenced by the Development treatment/exclusion state covering that affected hour.

The rejected raw row must never be passed to `normalize_row`.

A valid raw row that merely lies inside a broader documented exclusion region because of a different anomaly is **not** automatically dropped. If that row has no row-level scanner event, it is normalized normally; downstream certification rules determine whether it may enter the primary sample.

This preserves the distinction between:

- rejecting the anomalous raw row itself; and
- excluding an affected canonical region from certified inference.

### 6.3 Fatal conditions

V2 hard-fails rather than dropping data when any of these occur:

- unlocalized non-checksum scanner event;
- archive/member schema error that cannot be localized;
- scanner event/row-number mismatch;
- scanner anomaly ID missing from the manifest;
- in-Development localized row event not linked to the corresponding treatment/exclusion state;
- accepted row that fails strict `normalize_row`;
- duplicate accounting key;
- row-accounting mismatch;
- mixed unsupported timestamp precision after accepted-row normalization;
- any certified-segment hourly-grid failure.

## 7. Exact raw-row accounting

Accounting is separate from the already frozen primary-sample accounting.

For every archive:

`raw_data_rows = normalized_accepted_raw_rows + explicitly_rejected_raw_rows`.

`raw_data_rows` means the same nonblank CSV rows counted by frozen `scan_archive.rows_processed`.

Rejected counts use unique physical row numbers, not event counts.

For every archive emit:

- archive filename;
- ZIP member;
- scanner `rows_processed`;
- normalized accepted raw-row count;
- explicitly rejected raw-row count;
- accounting equality;
- SHA-256 digest of all raw-row keys;
- SHA-256 digest of accepted raw-row keys;
- SHA-256 digest of rejected raw-row records.

Raw-row key canonical text is:

`{archive}|{member}|{physical_row_number}|{raw_timestamp}`.

Rejected raw-row canonical record contains exactly:

- symbol;
- archive;
- member;
- physical row number;
- raw timestamp;
- sorted unique parsed-timestamp strings from its scanner events;
- sorted frozen anomaly IDs;
- sorted anomaly types.

Canonical rejected-record digest input is compact sorted-key ASCII JSON for the ordered record list.

Also emit asset aggregates:

- total raw data rows;
- total normalized accepted raw rows;
- total explicitly rejected raw rows;
- exact equality;
- aggregate all/accepted/rejected digests.

No undocumented row may disappear.

## 8. Development projection V2

Projection version becomes:

`ams-dep-development-projection-v2`.

It inherits all V1 projection fields and additionally binds:

- normalization mode = `TREATMENT_AWARE_RAW_ROW_V2`;
- exact per-archive raw-row accounting records;
- aggregate raw-row accounting;
- rejected-row identity digests;
- proof that every in-Development rejected row is tied to frozen treatment anomaly IDs/exclusions;
- BTC parent-incident checksum continuity result;
- explicit `no_rounding_no_interpolation_no_repair=true`.

Projection canonicalization remains:

`json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")`

followed by SHA-256.

Validation/OOS helper partition objects remain non-authoritative and must not be emitted as protected-partition certification evidence.

## 9. Canonical bundle/sample/statistical path remains unchanged

After V2 treatment-aware normalization and projection verification, V2 must construct the same `CertifiedDataBundle` shape expected by the existing canonical pipeline and reuse the existing verifier/sample builder through the already-reviewed explicit Development-helper identity seam.

No modification is authorized to:

- `ams_dep_pipeline.py`;
- `market_state.py`;
- `data_quality.py`;
- `data_quality_treatment_v2.py`;
- `data_ingestion.py`;
- `source_identity.py`;
- `dependence_statistics.py`;
- `dependent_wild_bootstrap_v2.py`;
- `release_gate.py`.

Support, state construction, exact-time geometry, restrictions, invalidity policy, six-slot Holm family, exact cross-asset intersection, and protected scope remain exactly as in V1.

## 10. Empirical bootstrap namespace is retained

V1 failed before primary-sample construction and before empirical RNG/inference.

To minimize result-affecting change, V2 retains the exact V1 empirical bootstrap namespace:

- root `2026092201`;
- version coordinate `2`;
- DGP sentinel `4294967295`;
- outer sentinel `4294967295`;
- asset order BTCUSDT, ETHUSDT;
- hypothesis order DEP, TIME, STATE;
- requested draws = 4,999;
- exact pre-segment path:
  `[2026092201,2,4294967295,4294967295,asset_index,hypothesis_index,bootstrap_index]`.

This is a prospective decision made before any V2 source access. The V2 execution-package version does not alter the frozen numerical V2 method.

## 11. New V2 one-shot execution

V2 uses a new immutable claim:

`refs/tags/ams-dep-development-execution-claimed-v2`.

V2 must never use the V1 claim as an authorization mechanism.

Required exact confirmation token:

`AMS_DEP_DEVELOPMENT_EMPIRICAL_V2`.

Required workflow:

`.github/workflows/ams-dep-development-empirical-v2.yml`.

The workflow remains manual `workflow_dispatch` only and must provide a safe offline-review mode separated from execute mode.

The V2 claim must be atomically created and reverified against GitHub before:

- any V2 archive/network request;
- any V2 archive read;
- any empirical bootstrap seed instantiation.

Failure after V2 claim creation consumes V2 and requires another independent incident review.

## 12. V2 governance files

Implementation must create new versioned governance files rather than rewriting the V1 incident record:

- `research/governance/ams_dep_development_execution_manifest_v2.json`;
- `research/governance/ams_dep_development_implementation_freeze_v2.json`.

The V1 execution manifest, V1 freeze, V1 claim, V1 run, and V1 artifact remain historical evidence.

Before V2 implementation review:

- V2 manifest status = `DRAFT_LOCKED`;
- V2 execution authorization = false;
- V2 claim/executed flags = false;
- reviewed implementation commit unset.

Independent V2 implementation review and a separate governance authorization are required before V2 execute mode.

## 13. V2 artifact requirements

In addition to all inherited V1 artifact/provenance fields, V2 must include:

- parent V1 incident run/artifact/claim identifiers and hashes;
- V2 claim ref/target;
- exact V2 specification/registration/freeze hashes;
- V2 treatment-aware normalizer implementation blob;
- V1 BTC checksum-continuity results for all 53 archives;
- all per-archive and aggregate raw-row accounting;
- every rejected raw-row canonical record or a complete digest-backed record set sufficient for independent reconstruction;
- anomaly-ID linkage evidence;
- normalized accepted-row dataset identity/content hash;
- V2 projection record/hash;
- explicit booleans:
  - `timestamp_rounding_used=false`;
  - `interpolation_used=false`;
  - `synthetic_bar_used=false`;
  - `arbitrary_exception_skip_used=false`.

Post-claim failure artifacts must preserve progressive raw-row/source evidence exactly as V1 incident handling did.

## 14. Synthetic/offline regression requirements before V2 review

No empirical archive is needed for implementation testing.

Synthetic ZIP fixtures must cover at minimum:

1. a known-style non-hour-aligned row between adjacent valid hourly rows;
2. scanner emits `NON_ALIGNED_TIMESTAMP`;
3. the exact bad raw row is rejected, not rounded/repaired;
4. neighboring valid rows normalize unchanged;
5. affected canonical interval is treatment-excluded;
6. rejected row is linked to frozen event/anomaly IDs;
7. exact raw-row accounting holds;
8. accepted-row strict normalization still hard-fails if scanner failed to classify a bad row;
9. unlocalized schema/header errors remain fatal;
10. invalid OHLC/volume localized row treatment;
11. duplicate timestamp localized row treatment;
12. out-of-order localized row treatment;
13. no undocumented row disappearance;
14. certified segments remain exact hourly grids after treatment;
15. caller cannot override source URL/root/months/checksum/symbol/timeframe;
16. V1 claim cannot satisfy V2 execution;
17. V2 claim cannot be created by PR/push CI;
18. no Validation/OOS/P&L/trading path is introduced.

The test design must exercise the generalized treatment-aware contract, not only the exact V1 exception string.

## 15. Allowed V2 implementation surface

Only these new/bounded V2 paths may be implemented after specification approval:

- `src/research_core/ams_dep_treatment_aware_normalization_v2.py`;
- `src/research_core/ams_dep_development_source_v2.py`;
- `src/research_core/ams_dep_empirical_access_v2.py`;
- `src/research_core/ams_dep_development_execution_lock_v2.py`;
- `research/scripts/run_ams_dep_development_empirical_v2.py`;
- `research/governance/ams_dep_development_execution_manifest_v2.json`;
- `research/governance/ams_dep_development_implementation_freeze_v2.json`;
- dedicated V2 tests;
- `.github/workflows/ams-dep-development-empirical-v2.yml`.

Any need to modify a frozen upstream/V1 result-affecting path requires a prospective specification amendment and another independent review before implementation.

## 16. Current authorization state

This specification authorizes **nothing beyond review of the proposed V2 design**.

Current V1 incident lock remains authoritative:

- Development market-data execution false;
- V1 consumed claim retained;
- Validation/OOS false;
- strategy P&L false;
- paper trading false;
- live trading false;
- directed lag diagnostics false.

No V2 source access, implementation, claim creation, or empirical execution is authorized until this specification and machine registration are independently approved, followed by separately reviewed implementation and authorization.
