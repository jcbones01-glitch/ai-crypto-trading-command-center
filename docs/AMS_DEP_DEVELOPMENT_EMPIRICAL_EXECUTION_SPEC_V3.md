# AMS-DEP Development empirical execution recovery specification V3

Status: **PROPOSED — PRE-IMPLEMENTATION — NO V3 MARKET-DATA ACCESS AUTHORIZED**

Parent incident review: Issue #78  
Parent V2 execution run: `35909778426`  
Parent V2 artifact: `10772389334`  
Consumed V2 claim: `refs/tags/ams-dep-development-execution-claimed-v2`  
V2 execution head / claim target: `f925897a5ef5ab1e34ecaa087b87ee07f779eb56`

## 1. Purpose

V3 is a narrowly scoped prospective recovery from the consumed V2 source-certification incident.

V2 successfully fixed the V1 strict-parser/treatment-aware normalization incompatibility. V2 scanned and classified the malformed BTC rows, explicitly rejected the 43 localized non-hour-aligned physical rows, completed raw-row accounting across all 53 BTC archives, and reached the unchanged canonical bundle verifier.

V2 then failed before primary-sample construction at:

`certified segment hourly grid mismatch`.

Independent Issue #78 classified the failure class as a latent **source-coverage/certification-boundary defect**: the frozen treatment construction can certify from nominal partition boundaries without first proving that normalized source coverage actually contains every hour in those certified intervals, while the frozen scanner does not create leading-edge, trailing-edge, or cross-archive coverage events.

The surviving artifact does **not** prove the exact first missing BTC timestamp. V3 must not hard-code, infer, or otherwise invent that timestamp.

V3 repairs only the missing source-coverage certification seam. It does not modify the trading hypothesis, primary estimand, statistical method, support thresholds, bootstrap, multiplicity, or protected downstream scope.

## 2. Immutable V1 and V2 incidents

The following historical evidence remains immutable.

### V1

- claim: `refs/tags/ams-dep-development-execution-claimed-v1`;
- claim target / execution head: `969f6aeadda4143b0882b8e9169e3f6dd9c177ed`;
- run: `35834431025`;
- artifact: `10738551310`;
- artifact ZIP SHA-256:
  `b947d8a9d73dd05da0455ad8c1fb7ab845f4a187ff56ec99856b385fc0e403c7`;
- result JSON SHA-256:
  `19f53015e725526b8baa8da89fec5cdbf58d7e6f9a1985fcc626309ab0e2cca7`.

### V2

- reviewed implementation candidate:
  `8538332bb20cbd47a0250c86686d367c4aa0aa2d`;
- review anchor:
  `refs/heads/ams-dep-development-implementation-reviewed-v2`;
- execution claim:
  `refs/tags/ams-dep-development-execution-claimed-v2`;
- claim target / execution head:
  `f925897a5ef5ab1e34ecaa087b87ee07f779eb56`;
- run: `35909778426`;
- artifact: `10772389334`;
- artifact ZIP SHA-256:
  `a37dbd7b2a6e31ba69a51c4f43c911aa844044b3852c07fb94151dd600390979`;
- result JSON SHA-256:
  `251c84d2090f510c80d91932e720648fa19fe26812741cc5018042c763fde144`.

Neither V1 nor V2 may be rerun. Neither consumed claim may be deleted, recreated, repointed, or reused.

The V1/V2 artifacts are incident and provenance evidence only. They are not empirical source datasets for V3.

## 3. Contract precedence

Conflicts resolve in this order:

1. **this V3 recovery specification and its machine registration** control V3 source-coverage audit, coverage-aware certification overlay, V3 provenance, V3 execution/versioning, and V3 one-shot governance;
2. **the accepted V2 Development recovery specification/registration and exact reviewed V2 treatment-aware normalizer** control raw-row treatment and row accounting except where this V3 document explicitly adds coverage certification;
3. **the accepted V1 Development execution contract** controls the unchanged source universe, Development boundary, primary sample, support rules, DWB inference, multiplicity, protected scope, and output discipline;
4. **the accepted full-pipeline contract** controls canonical sample/state/support/join semantics;
5. **the frozen AMS-DEP numerical V2 contract** controls the statistical method.

V3 does not amend the frozen numerical method.

## 4. Source universe remains unchanged

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
- Development partition exactly
  `[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`.

V3 must independently reacquire official archives **only after** a future V3 durable one-shot claim has been created and verified.

V3 must not reuse a V1 or V2 local cache as source input.

### 4.1 BTC byte-continuity rule

The same 53 BTC checksum values already pinned before V2 remain the parent-byte continuity contract.

For every BTC V3 archive:

`current_official_checksum == pinned_parent_checksum == V3_local_zip_sha256`.

A mismatch is a hard source-integrity failure requiring separate review.

### 4.2 ETH rule

V1 and V2 did not reach ETH source acquisition.

Therefore no retrospective ETH parent checksum may be invented.

For every ETH V3 archive:

`V3_current_official_checksum == V3_local_zip_sha256`.

## 5. Frozen raw-row anomaly semantics remain unchanged

V3 must reuse unchanged:

- `data_quality.scan_archive`;
- `data_quality_treatment_v2.event_id`;
- `data_quality_treatment_v2.build_manifest` for the **base row-treatment manifest**;
- `data_ingestion.normalize_row` for accepted rows;
- the exact reviewed V2 treatment-aware normalizer semantics.

V3 must not alter anomaly classification, physical-row identity rules, or accepted/rejected row rules.

Specifically, the V2 behavior remains:

- a row with zero row-level scanner events is strictly normalized;
- a localized anomalous physical row may be explicitly rejected only under the V2 event-ID/treatment-linkage contract;
- a valid row inside a broader exclusion region is still normalized;
- unlocalized events remain fatal;
- no arbitrary catch-and-skip is permitted.

No recovery may:

- round, snap, or shift a timestamp;
- interpolate;
- resample;
- synthesize a bar;
- repair OHLC/volume;
- silently discard an exception.

## 6. V3 is a certification overlay, not a source repair

V3 introduces a deterministic **Development source-coverage audit** after V2-style treatment-aware normalization and before construction of the final certified bundle.

The audit acts only on timestamps and certification metadata.

It does not alter any normalized MarketBar value and does not create a missing MarketBar.

The audit is intentionally independent of the unproven hypothesis that the four absent hours in the first partial BTC month occur at the leading edge. The algorithm must work identically whether missing coverage is leading, trailing, cross-archive, or internal.

## 7. Two-stage treatment/certification sequence

For each asset V3 must perform these steps in this exact order.

### Stage A — base row treatment

1. verify the exact registered 53-archive inventory and checksums;
2. run frozen `scan_archive()` on all 53 archives;
3. build the frozen base Development treatment manifest using unchanged
   `build_manifest()`;
4. bind raw source identity using unchanged `source_identity` / `bind_source_identity`;
5. run the exact V2 treatment-aware raw-row normalization semantics;
6. require exact V2 raw-row accounting;
7. obtain the ordered accepted normalized MarketBar sequence.

Stage A must preserve the V2 handling of the 43 known-style non-hour-aligned rows. V3 must not reinterpret them as coverage events or repair them.

### Stage B — Development coverage audit and certification overlay

Only after Stage A succeeds, V3 audits the accepted normalized timestamp set against the **hours already claimed certified by the base Development partition**.

Let:

- `B` = the union of exact canonical hourly timestamps in all base Development certified segments;
- `O` = the set of accepted normalized timestamps from Stage A.

Define:

`M = B - O`.

`M` is the exact set of base-certified Development hours for which no accepted normalized bar exists.

This definition is controlling.

Hours already inside base Development exclusions are not in `B` and therefore are not duplicated as V3 coverage gaps.

V3 must never infer a coverage gap merely from archive row counts. It must compute `M` from the actual accepted timestamp vector during the future authorized execution.

## 8. Exact Development coverage-audit invariants

Before calculating `M`, V3 must require:

- every accepted timestamp is timezone-aware UTC;
- every accepted timestamp lies on an exact UTC hour boundary;
- accepted timestamps are unique;
- accepted timestamps are strictly increasing after canonical sort;
- every accepted timestamp lies inside the registered Development interval;
- the accepted timestamp vector is identical to the timestamp vector whose dataset/content identities are used in the bundle metadata.

Any violation hard-fails.

The audit must also verify that the base Development certified segments:

- are nonempty;
- are hour-aligned;
- are sorted;
- do not overlap.

## 9. Coverage-gap interval construction

Sort `M`.

Coalesce exactly adjacent missing canonical hours into maximal half-open intervals:

`[gap_start, gap_end)`.

For example, missing hours `t, t+1h, t+2h` become one interval
`[t, t+3h)`.

No interval may contain an observed accepted timestamp.

No interval may extend beyond the exact missing-hour set.

V3 must not add a heuristic buffer, repair window, or result-dependent extension.

The existing primary-sample rules already require neighboring endpoints and same certified segment; therefore splitting certification at the exact source-coverage gap is sufficient to prevent returns/state construction from crossing the gap.

## 10. Deterministic coverage-gap identity

Each coverage-gap interval receives a deterministic identity from the exact canonical record:

```
{
  "domain": "AMS_DEP_DEVELOPMENT_V3_SOURCE_COVERAGE_GAP",
  "version": 3,
  "symbol": SYMBOL,
  "start": START_ISO_UTC,
  "end": END_ISO_UTC,
  "reason": "BASE_CERTIFIED_HOUR_ABSENT_FROM_ACCEPTED_NORMALIZED_SOURCE"
}
```

Canonical bytes are exactly:

`json.dumps(record, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")`.

The coverage-gap ID is SHA-256 of those bytes.

No source price/volume field enters the gap identity.

## 11. Coverage-aware final Development certification

The final V3 Development certification is constructed from the base Development partition without weakening any base exclusion.

### 11.1 Base exclusions are preserved

Every base Development exclusion remains unchanged.

V3 may only add coverage-gap exclusions. It may not remove, shorten, relabel, or reinterpret a base exclusion.

### 11.2 Final certified hours

The final certified-hour set is:

`C = B ∩ O`.

Equivalently:

`C = B - M`.

Final certified segments are the maximal contiguous hourly runs in `C`.

This means V3 certification may only **remove unsupported hours from base certification**. It can never certify an hour that the base manifest did not certify.

### 11.3 Coverage exclusions

Each coverage-gap interval becomes a Development exclusion with:

- its deterministic coverage-gap ID;
- reason:
  `BASE_CERTIFIED_HOUR_ABSENT_FROM_ACCEPTED_NORMALIZED_SOURCE`.

Coverage exclusions must be disjoint from base exclusions by construction because `M` is computed only inside base-certified hours.

### 11.4 Continuity breaks

Each coverage-gap interval also becomes a continuity break.

Return/state/sample construction must not cross it.

### 11.5 Final certification label

If either:

- the base Development partition already has exclusions; or
- V3 adds at least one coverage-gap exclusion,

then final Development certification is:

`VALID WITH DOCUMENTED EXCLUSIONS`.

Otherwise it is:

`VALID`.

## 12. Coverage-aware manifest construction

V3 may introduce a new versioned helper module to create a **coverage-aware manifest record** from:

- the bound base treatment manifest;
- the accepted normalized timestamp vector;
- deterministic coverage-gap records.

The helper must preserve:

- symbol;
- timeframe;
- source-version/source identity;
- frozen normalization-version value;
- frozen row-treatment protocol value;
- all base anomaly IDs;
- all base affected regions;
- all base continuity breaks;
- all base exclusions;
- all non-Development helper partition objects as non-authoritative provenance only.

It may add:

- coverage-gap IDs;
- coverage affected regions;
- coverage exclusions;
- coverage continuity breaks;
- final coverage-aware Development certified segments.

The global `certified_segments` used by the existing cross-asset common-certification helper must equal the final coverage-aware Development certified segments.

The global exclusions/continuity-break collections must include both preserved base treatment and added V3 coverage treatment.

The Development partition object must carry the same final segments/exclusions.

The final manifest identity is recomputed using the existing canonical
`recompute_treatment_manifest_identity()` byte semantics.

The new helper must not modify:

- `data_quality_treatment_v2.py`;
- `ams_dep_pipeline.py`.

### 12.1 Compatibility field rule

The existing manifest's frozen treatment-protocol and normalization-version fields remain unchanged because V3 does not redefine raw-row anomaly treatment or raw normalization.

V3 coverage semantics are separately and explicitly versioned through:

- the V3 execution specification;
- the V3 machine registration;
- the V3 coverage-gap domain/version;
- the V3 projection;
- the V3 coverage evidence record.

This compatibility choice must be independently reviewed before implementation.

## 13. Canonical verifier remains unchanged

The unchanged `verify_certified_bundle()` remains the final integrity authority.

V3 must not weaken or bypass:

`certified segment hourly grid mismatch`.

Instead, V3 must construct certification metadata such that the final certified segments contain only demonstrated accepted hourly coverage.

Before passing the bundle to the canonical verifier, V3 must itself assert for every final certified segment:

`actual accepted timestamps in [segment.start, segment.end) == exact expected hourly grid`.

The unchanged canonical verifier must then independently reach the same conclusion.

Any disagreement hard-fails.

## 14. No result-directed effective-start rule

V3 does **not** define a hard-coded replacement Development start timestamp.

The registered Development domain remains:

`[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`.

Coverage-aware certification determines which hours inside that fixed domain are certified.

If the source does not cover the nominal leading edge, those unsupported hours become documented coverage exclusions.

This avoids changing the research partition merely because the V2 incident suggested a possible four-hour leading deficit.

## 15. Coverage audit evidence and canonical digests

V3 must emit deterministic source-coverage evidence for each asset.

Required fields:

- registered Development start/end;
- accepted normalized row count;
- accepted first timestamp;
- accepted last timestamp;
- accepted timestamp-vector SHA-256;
- base certified-hour count;
- base certified-hour-vector SHA-256;
- V3 missing-coverage hour count;
- V3 missing-coverage-hour-vector SHA-256;
- complete ordered coverage-gap interval records;
- complete coverage-gap IDs;
- final certified-hour count;
- final certified-hour-vector SHA-256;
- complete final certified segment records;
- final certified-segment record SHA-256;
- preserved base exclusion count/hash;
- added coverage exclusion count/hash;
- final exclusion count/hash;
- base treatment-manifest identity;
- final coverage-aware manifest identity.

Timestamp-vector bytes are exactly the compact ASCII JSON encoding of ordered UTC ISO-8601 timestamp strings:

`json.dumps(sequence, ensure_ascii=True, separators=(",", ":")).encode("ascii")`.

Record-list bytes use:

`json.dumps(records, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")`.

No trailing newline or external framing is permitted.

## 16. V2 row accounting remains controlling

V3 inherits the exact V2 raw-row accounting contract and digest canonicalization.

No V3 coverage event is a physical raw row.

Coverage-gap counts must never be added to:

- `raw_data_rows`;
- `normalized_accepted_raw_rows`;
- `explicitly_rejected_raw_rows`.

The identity remains:

`raw_data_rows = normalized_accepted_raw_rows + explicitly_rejected_raw_rows`.

Coverage accounting is a separate certification layer.

## 17. V3 Development projection

Projection version becomes:

`ams-dep-development-projection-v3`.

It inherits V2 projection evidence and additionally binds:

- coverage audit version:
  `AMS_DEP_DEVELOPMENT_SOURCE_COVERAGE_V3`;
- base manifest identity;
- final coverage-aware manifest identity;
- accepted first/last timestamp;
- accepted timestamp-vector digest;
- base-certified grid count/digest;
- missing-coverage count/digest;
- full deterministic coverage-gap records/IDs;
- final certified-hour count/digest;
- final certified segment records/digest;
- preserved-base-exclusion and added-coverage-exclusion identities;
- assertion:
  `coverage_overlay_only_removes_base_certification=true`;
- assertion:
  `no_market_bar_created_or_modified=true`;
- V1/V2 parent incident identifiers and immutable claim references.

Projection canonicalization remains compact sorted-key JSON followed by SHA-256.

Validation/OOS helper partition objects remain non-authoritative and must not be emitted as protected-partition certification evidence.

## 18. Statistical contract remains unchanged

V1 and V2 both failed before empirical RNG/inference.

V3 therefore retains the exact preregistered empirical statistical namespace:

- root: `2026092201`;
- numerical-method/version coordinate: `2`;
- DGP sentinel: `4294967295`;
- outer sentinel: `4294967295`;
- asset order: BTCUSDT, ETHUSDT;
- hypothesis order: DEP, TIME, STATE;
- DWB draws: 4,999;
- exact pre-segment seed path:
  `[2026092201,2,4294967295,4294967295,asset_index,hypothesis_index,bootstrap_index]`.

V3 must retain unchanged:

- primary sample construction;
- market-state construction;
- support thresholds;
- FixedOLS;
- ParzenGeometry;
- restrictions;
- observed Wald;
- null-imposed restricted components;
- wild-bootstrap pseudo-series;
- invalid-draw handling;
- `invalid_fraction > 0.01` invalidity rule;
- six-slot family;
- Holm correction;
- exact cross-asset timestamp intersection.

No new seed namespace is justified merely because this is execution package V3.

## 19. New V3 one-shot governance

V3 uses a distinct immutable claim:

`refs/tags/ams-dep-development-execution-claimed-v3`.

Required exact confirmation token:

`AMS_DEP_DEVELOPMENT_EMPIRICAL_V3`.

Required manual workflow:

`.github/workflows/ams-dep-development-empirical-v3.yml`.

The workflow must be `workflow_dispatch` only with:

- safe `offline_review` default;
- explicit `execute` mode;
- exact confirmation required only for execute;
- concurrency with `cancel-in-progress: false`.

The V3 claim must be atomically created and verified before:

- V3 network/archive request;
- archive read;
- empirical bootstrap seed instantiation.

Failure after V3 claim creation consumes V3.

V1 and V2 claims can never satisfy V3.

## 20. V3 reviewed-candidate anchor

V3 prospectively requires:

`refs/heads/ams-dep-development-implementation-reviewed-v3`.

Lifecycle is the same immutable external-binding model approved for V2:

1. absent during implementation and pre-review;
2. created only after independent approval of the exact V3 implementation candidate;
3. never normally deleted/recreated/force-updated/repointed;
4. live GitHub target must equal the freeze candidate, execution-manifest candidate, and reviewed implementation commit;
5. missing/wrong/repointed anchor hard-fails before V3 claim/source access;
6. mutable governance JSON cannot rebind a different implementation while the live anchor remains on the actually reviewed candidate.

## 21. V3 governance files

Future implementation must create:

- `research/governance/ams_dep_development_execution_manifest_v3.json`;
- `research/governance/ams_dep_development_implementation_freeze_v3.json`.

Before independent implementation approval:

- manifest status = `DRAFT_LOCKED`;
- reviewed implementation commit unset;
- independent review false;
- Development execution authorization false;
- V3 claim false;
- V3 execution false.

A separate implementation review and a separate execution-authorization review are required.

## 22. V3 artifact and incident evidence

Success and post-claim failure artifacts must include:

- immutable V1 and V2 parent incident identifiers/hashes/claims;
- V3 claim/ref/target;
- V3 review-anchor evidence;
- exact specification/registration/freeze hashes;
- exact implementation blob evidence;
- 53-archive source/checksum evidence per reached asset;
- inherited V2 raw-row accounting;
- coverage audit evidence from Section 15;
- base and final manifest identities;
- V3 projection record/hash;
- sample/numerical/inference provenance as stages are reached;
- no-repair booleans.

If failure occurs during coverage audit, preserve:

- accepted normalized first/last timestamp if known;
- processed accepted timestamp count;
- accepted timestamp-vector digest through the deterministic completed normalization stage;
- base manifest identity;
- exact failure code/stage;
- any complete coverage-gap records constructed before failure.

If coverage audit completes but canonical verification fails, preserve the **complete** coverage evidence and final manifest/segment records.

## 23. Required synthetic/offline regressions

No empirical archive is required for V3 implementation testing.

At minimum tests must prove:

1. nominal Development start precedes first observed accepted bar; leading unsupported hours become coverage gaps, not synthetic bars;
2. accepted source ends before nominal Development end; trailing unsupported hours become coverage gaps;
3. a cross-archive missing hour not detected by per-archive scanner is caught by the V3 coverage audit;
4. an internal missing hour inside a base-certified segment becomes a coverage gap;
5. a missing hour already inside a base exclusion is **not duplicated** as a V3 coverage gap;
6. the 43-row-style V2 row treatment semantics remain unchanged;
7. valid rows in base exclusions remain normalized but uncertified;
8. coverage overlay only removes hours from base certification;
9. coverage overlay never adds a certified hour;
10. final certified segments equal maximal contiguous runs of `B ∩ O`;
11. final certified segments pass exact hourly-grid checks;
12. unchanged canonical verifier accepts the V3 synthetic bundle;
13. deliberately corrupted final segment metadata is still rejected by the unchanged canonical verifier;
14. accepted first/last timestamp evidence is exact;
15. timestamp-vector and coverage-record digests are deterministic under alternate container/dictionary iteration order;
16. coverage gaps do not alter V2 raw-row accounting totals;
17. V1/V2 claims cannot satisfy V3;
18. V3 reviewed-candidate rebinding attack fails;
19. claim must precede staging/network/source access;
20. no PR/push/schedule/repository-dispatch/workflow-run empirical trigger exists;
21. no Validation/OOS/P&L/paper/live/directed-lag path is introduced;
22. V3 statistical constants/path remain byte/behavior equivalent to V2 except provenance/source-certification integration;
23. post-claim coverage-audit failure preserves progressive evidence;
24. post-coverage canonical-verifier failure preserves complete coverage evidence.

## 24. Bounded future V3 implementation surface

Only these new/versioned paths may be added or changed during V3 implementation:

- `src/research_core/ams_dep_source_coverage_v3.py`;
- `src/research_core/ams_dep_development_source_v3.py`;
- `src/research_core/ams_dep_empirical_access_v3.py`;
- `src/research_core/ams_dep_development_execution_lock_v3.py`;
- `research/scripts/run_ams_dep_development_empirical_v3.py`;
- `research/governance/ams_dep_development_execution_manifest_v3.json`;
- `research/governance/ams_dep_development_implementation_freeze_v3.json`;
- dedicated `tests/test_ams_dep_development_v3_*.py`;
- `.github/workflows/ams-dep-development-empirical-v3.yml`.

V3 should import and reuse the reviewed V2 treatment-aware normalizer rather than clone or modify it.

Explicitly forbidden implementation changes include:

- every V1/V2 execution/claim/review-anchor record;
- `src/research_core/ams_dep_treatment_aware_normalization_v2.py`;
- `src/research_core/data_quality.py`;
- `src/research_core/data_quality_treatment_v2.py`;
- `src/research_core/data_ingestion.py`;
- `src/research_core/source_identity.py`;
- `src/research_core/archive_security.py`;
- `src/research_core/data_interfaces.py`;
- `src/research_core/ams_dep_pipeline.py`;
- `src/research_core/market_state.py`;
- `src/research_core/dependence_statistics.py`;
- `src/research_core/dependent_wild_bootstrap_v2.py`;
- `src/research_core/release_gate.py`;
- `pyproject.toml`.

If implementation later shows that one of these forbidden files must change, this V3 approval is insufficient. The project must return to a prospective specification amendment and independent review before changing it.

## 25. Protected scope

V3 does not authorize:

- Validation;
- OOS;
- strategy P&L;
- paper trading;
- live trading;
- leverage;
- directed cross-asset lag diagnostics;
- V1/V2 reruns;
- parameter tuning after observing outcomes.

The only eventual empirical authority contemplated is one first V3 Development execution under a new durable claim after the full review chain.

## 26. Required review sequence

No V3 implementation may begin until an independent reviewer approves this exact specification package.

Required sequence:

1. V3 specification package;
2. independent V3 specification review;
3. bounded implementation;
4. exact-candidate offline/synthetic evidence;
5. independent implementation freeze review;
6. immutable V3 reviewed-candidate anchor;
7. separate V3 execution-authorization review;
8. governance-only authorization transition;
9. explicit manual V3 execute dispatch;
10. atomic V3 one-shot claim;
11. source access and execution.

## 27. Current authorization state

At specification time:

- V1 claim exists and is consumed;
- V2 claim exists and is consumed;
- V2 review anchor remains immutable;
- Development market-data execution authorization is false;
- Validation/OOS/P&L/paper/live permissions are false;
- no V3 claim exists;
- no V3 review anchor exists;
- V3 empirical execution is not authorized.

This specification authorizes only independent review of the proposed V3 design.
