# AMS-DEP Development empirical execution specification V1

Status: **PROPOSED REVISION 2 — PRE-OUTCOME — NOT AUTHORIZED FOR MARKET-DATA EXECUTION**

Independent review history:

- Issue #67 initial decision:
  `REQUIRE_CHANGES_BEFORE_DEVELOPMENT_EMPIRICAL_IMPLEMENTATION`.
- This revision addresses the identity-model, future-partition semantics, one-shot execution, workflow, provenance, precedence, and machine-registration findings before any empirical archive is opened.

## Purpose

This specification defines the first outcome-producing AMS-DEP Development execution package after the independently accepted synthetic calibration, one-shot synthetic holdout, full-pipeline synthetic integrity certification, and separate empirical-release approval.

It prospectively freezes the source inventory, Development-scoped provenance model, production adapter behavior, numerical inference wiring, bootstrap seed namespace, output/provenance contract, one-shot execution claim, and authorization workflow **before any empirical BTCUSDT/ETHUSDT archive is opened by this stage**.

This stage is not Validation/OOS, not a trading-strategy backtest, not P&L analysis, and not paper/live trading.

## Current governance state

Base governance head:

`5918dd38bb043608a81cdab4af1abeefe18b3ce5`

The canonical gate records:

- `v2_synthetic_calibration_passed=true`;
- `v2_synthetic_holdout_passed=true`;
- `full_pipeline_synthetic_integrity_passed=true`;
- `separate_empirical_release_approved=true`;
- `development_market_data_execution_authorized=false`;
- `validation_or_oos_access_authorized=false`;
- `strategy_pnl_authorized=false`;
- `paper_trading_authorized=false`;
- `live_trading_authorized=false`.

No empirical read is authorized by this specification.

## Controlling-contract precedence

The historical file `docs/MARKET_STATE_DEPENDENCE_PREREGISTRATION_V1.md` remains unchanged as provenance. Its DRAFT banner is historical and is **not** the controlling authorization contract for the first empirical execution.

For the first Development execution, conflicts resolve in this order:

1. **this specification and its machine-readable registration** control source scope, Development execution, empirical bootstrap namespace, one-shot execution, outputs, and permissions;
2. **the accepted full-pipeline registration/specification** control canonical source/sample/state/support/join semantics except where this specification prospectively replaces the whole-research identity equality with the Development-scoped projection defined below;
3. **the frozen AMS-DEP V2 numerical contract/freeze** controls the primary numerical/DWB method;
4. the historical V1 preregistration is retained only for primary estimand/model/restriction concepts explicitly adopted by the later controlling artifacts.

Specifically superseded or unauthorized from the historical DRAFT:

- the old Bartlett/asymptotic chi-square primary inference is superseded by frozen V2 exact-time Parzen DWB;
- secondary outputs not explicitly included here are unauthorized;
- the directed 1/6/24-hour cross-asset lag diagnostics remain separately blocked;
- the historical whole-research treatment-manifest identities remain parent provenance and are **not** equality targets for a different Development-only source universe.

The historical preregistration must not be rewritten.

## Frozen primary scientific contract

Execution must reuse without modification:

- `research_core.ams_dep_pipeline` canonical row construction, support, numerical-input and exact-join logic;
- `research_core.market_state.build_market_states`;
- `research_core.data_quality_treatment_v2.build_manifest` and `return_eligible`;
- `research_core.source_identity.source_identity` / `bind_source_identity`;
- `research_core.data_ingestion` archive parsing, dataset identity and content hashing;
- `research_core.dependence_statistics.primary_design`, `RESTRICTIONS`, `SLOTS`, and `holm_six`;
- `research_core.dependent_wild_bootstrap_v2.FixedOLS`, `ParzenGeometry`, `wald`, `restricted_components`, and `bootstrap_p_value`.

The bounded `engineering_fixture` is forbidden for empirical p-values.

The old asymptotic `dependence_statistics.wald_zero` chi-square p-value is forbidden for the primary empirical results.

Any need to modify the frozen V2 numerical core or canonical AMS-DEP pipeline creates a prospective versioned amendment and requires another independent review before outcomes.

## Exact Development universe

Assets are exactly:

- `BTCUSDT`;
- `ETHUSDT`.

Market/source contract:

- Binance Public Data;
- spot;
- 1-hour klines;
- UTC;
- normalization version `gate1-v1`;
- treatment version `gate1a-v1`.

Frozen Development partition:

`[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`.

No archive month beginning 2022-01 or later may be requested or opened.

## Exact source inventory

For each asset, the source inventory is the deterministic monthly sequence from **2017-08 through 2021-12 inclusive**, exactly 53 monthly ZIP archives per asset and 106 total.

Filename rule:

`{SYMBOL}-1h-{YYYY}-{MM}.zip`

Official archive URLs must be generated only through frozen:

`research_core.data_ingestion.archive_url(symbol, year, month)`.

The corresponding checksum document is exactly:

`archive_url + ".CHECKSUM"`.

No caller may provide or override:

- source URL;
- hostname;
- archive path;
- data root;
- mirror;
- symbol set;
- timeframe;
- first/last month;
- checksum behavior.

The production adapter must create its own temporary local staging directory. No caller-supplied pre-existing archive directory may enter the first empirical path.

August 2017 is required because Development begins on August 17. If that monthly archive contains a bar before the frozen Development start, the canonical returned-bundle boundary check must hard-fail rather than silently widening or trimming by discretion.

December 2021 is the final permitted archive. January 2022 is forbidden.

## Acquisition and checksum rule

Each expected ZIP must be acquired from its exact official Binance Public Data URL and verified against its official `.CHECKSUM` before source construction.

Implementation must call existing:

`download_archive(..., verify_checksum=True)`

or a behavior-preserving private wrapper that does not expose the URL or checksum flag.

For every archive the artifact must record:

- symbol;
- year/month;
- filename;
- official URL;
- official checksum value;
- independently computed local ZIP SHA-256.

Acquisition failure, checksum failure, missing archive, duplicate filename, unexpected archive, alternate host, fallback mirror, or partial inventory is a hard failure.

No partial-source inference is allowed.

## Historical whole-research identities: parent provenance only

The historical Gate 1A whole-research treatment-manifest identities remain immutable provenance:

- BTCUSDT:
  `1590cf8e69ed757eeb6701a218d561448beb2eb6ea09dcd0ae31d15a8f5197cf`;
- ETHUSDT:
  `d35bf21e309820abc88090bad29601adc1d1ea6b31dcddf0b80d510af4cf542f`.

Those hashes were created from the historical research universe through 2026-01-01 and therefore **must not** be required to equal a manifest built from only the 53 Development archives.

They may never be altered or relabeled as Development-only identities.

They must appear in the first empirical artifact as:

`historical_whole_research_parent_manifest_identity`.

They establish lineage, not bytewise equality to the Development projection.

## Development-scoped certification projection V1

Because the original Gate 1A artifact containing the full historical partition evidence is no longer durably available from its workflow, this revision does not invent an expected Development digest after inspecting data.

Instead, it prospectively freezes the **algorithm** for a new Development-scoped execution projection before any archive is opened.

The source adapter may use existing `build_certified_bundle_from_archives` / `build_manifest` primitives to construct the deterministic Development-only treatment state from the exact 53-archive inventory. However, any Validation/OOS `PartitionCertification` objects emitted by the generic helper are explicitly:

`NON_AUTHORITATIVE_HELPER_OUTPUT_NOT_EVIDENCE_OF_PROTECTED_PARTITION_CERTIFICATION`.

They must not be used, interpreted, or emitted as evidence that unread Validation/OOS data were certified.

Only the Development projection defined here is authoritative for this execution.

### Projection record

For each asset, construct exactly one canonical JSON record with these fields:

- `projection_version = "ams-dep-development-projection-v1"`;
- `historical_whole_research_parent_manifest_identity`;
- symbol;
- source provider = `Binance Public Data`;
- market = `spot`;
- timeframe = `1h`;
- normalization version = `gate1-v1`;
- treatment protocol version = `gate1a-v1`;
- Development start/end exactly equal to the frozen half-open boundaries;
- authoritative Development raw-source identity from `source_identity(paths)`;
- exact ordered 53-archive evidence records, each containing filename, official checksum SHA-256, and local ZIP SHA-256;
- Development certification value;
- Development certified segments only;
- Development exclusions only;
- Development-intersecting continuity breaks only;
- sorted anomaly IDs referenced by the Development exclusions/breaks;
- normalized Development dataset ID;
- normalized Development content hash;
- normalized row count/start/end.

The record must exclude:

- Validation partition certification;
- OOS partition certification;
- any future-partition segment/exclusion claim;
- empirical statistics, p-values, coefficients, or market outcomes.

Canonicalization is exactly:

`json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")`

and the Development projection identity is:

`sha256(canonical_bytes).hexdigest()`.

This algorithm, not an outcome-selected expected digest, is frozen before exposure.

### Projection verification order

Before market-state construction, primary-row construction, DWB inference, or output interpretation:

1. require the exact 53-file inventory;
2. verify every official checksum;
3. compute authoritative raw `source_identity(paths)`;
4. deterministically construct the Development-only treatment state using the frozen Gate 1A primitives;
5. require Development boundaries exactly equal the registration;
6. require source integrity `SOURCE VERIFIED`;
7. require Development certification to be `VALID` or `VALID WITH DOCUMENTED EXCLUSIONS`;
8. require every returned bar to lie inside Development;
9. recompute normalized dataset ID/content hash;
10. construct and hash the exact Development projection record;
11. emit the historical whole-research identity separately as lineage;
12. only then allow the canonical state/sample path.

No projection field or digest may be selected, replaced, or revised in response to the resulting returns.

If the projection cannot be constructed under these frozen rules, V1 fails integrity. The remedy is a new prospective version reviewed before another empirical exposure opportunity.

### Relationship to canonical bundle verification

Implementation must not call the default production `verify_certified_bundle(bundle)` in a way that incorrectly compares the Development-only manifest to the historical whole-research identity.

A new narrow Development-source wrapper must first enforce the projection contract above.

After that wrapper establishes the exact source/projection evidence, it may reuse the existing canonical verifier/sample builder with the **recomputed Development-only manifest identity passed explicitly** solely to exercise the already-certified bundle/sample invariants.

That explicit identity is not a replacement for the new projection identity and must not be exposed as the historical registered identity.

Tests must prove that callers cannot use this explicit-identity seam to inject arbitrary data or bypass the fixed source adapter.

## Protected partition firewall

Before any network request, source download, archive read, or empirical-seed construction, production execution must require:

- `full_pipeline_synthetic_integrity_passed=true`;
- `separate_empirical_release_approved=true`;
- `development_market_data_execution_authorized=true`;
- `validation_or_oos_access_authorized=false`;
- the Development execution manifest authorized;
- the reviewed implementation candidate bound exactly.

No adapter may request 2022-01 or later.

## New execution-manifest layer

Implementation must add:

`research/governance/ams_dep_development_execution_manifest_v1.json`.

Before independent implementation review:

- `status=DRAFT_LOCKED`;
- `development_execution_authorized=false`;
- `first_empirical_execution_claimed=false`;
- `first_empirical_execution_executed=false`;
- reviewed implementation commit unset;
- exact implementation blob pins frozen.

After independent implementation approval, a governance-only transition may set:

- `status=AUTHORIZED_FOR_FIRST_DEVELOPMENT_EXECUTION`;
- reviewed implementation commit exactly equal to the frozen candidate;
- `independent_implementation_reviewed=true`;
- `development_execution_authorized=true`.

The canonical release gate and execution manifest must both authorize before the one-shot claim can be created.

## One-shot first-execution claim

The first outcome-producing Development opportunity is single-use.

Durable fixed claim ref:

`refs/tags/ams-dep-development-execution-claimed-v1`.

The workflow must use a concurrency group dedicated to this execution and must not cancel an in-progress execution.

Required sequence:

1. run all offline/static preflight checks;
2. verify exact executing commit, release gate, execution manifest, implementation pins, event, confirmation token, runtime, and that the claim ref does not already exist;
3. **atomically create the fixed claim ref at the exact reviewed executing commit**;
4. verify the created claim resolves to that exact commit;
5. only after successful claim creation may any network request, archive download/read, or empirical bootstrap seed be instantiated.

The workflow must never delete, recreate, move, force-update, or repoint the claim.

If the claim already exists, execution hard-fails before source access.

### Retry/incident boundary

- failure before successful claim creation: no empirical source or seed may have been touched; retry may be permitted after correcting infrastructure;
- successful claim creation consumes the V1 first-execution opportunity;
- any failure after claim creation, including network/source/inference/artifact failure, is a consumed execution incident and **must not be silently rerun**;
- post-claim failure requires independent incident review and a prospectively governed recovery/version decision.

Determinism is not permission to rerun the consumed V1 opportunity.

## Workflow trigger and PR-CI prohibition

The outcome-producing workflow must be:

`workflow_dispatch` **only**.

Exact confirmation token:

`AMS_DEP_DEVELOPMENT_EMPIRICAL_V1`.

The outcome-producing job must require literal equality with that token.

It must not run on:

- `pull_request`;
- `push`;
- schedule;
- repository_dispatch;
- workflow_run.

PR/push CI may execute only offline/static/synthetic tests. It must never:

- invoke the production Development source adapter against the network;
- request/download empirical BTC/ETH archives;
- instantiate the empirical bootstrap seed namespace;
- create the durable execution claim;
- produce a Development empirical-result artifact.

The workflow event, run attempt, confirmation value/status, claim ref and claim target commit must be recorded in the result artifact.

## Canonical first empirical runner

The first outcome-producing runner must be a new versioned script:

`research/scripts/run_ams_dep_development_empirical_v1.py`.

It must run both assets in one execution. Selective BTC-only or ETH-only execution is forbidden for the first six-test family.

No user-controlled option may alter:

- asset subset;
- partition;
- gate path;
- archive root;
- source URL;
- loader;
- seed;
- bootstrap draw count;
- hypothesis subset;
- restriction;
- alpha;
- support threshold;
- Validation/OOS;
- P&L/trading.

An internal output path for workflow plumbing is permitted.

## Canonical sample and support

After Development projection verification, each asset must use the frozen canonical primary sample builder.

Frozen semantics remain:

- predictor `x_t = log(C_t/C_(t-1))`;
- target `y_t = log(C_(t+1)/C_t)`;
- state at `t`;
- availability/year at `t+1h`;
- `t-1`, `t`, `t+1` in the same certified Development segment;
- all endpoints inside Development;
- 744-bar warm-up reset per certified segment;
- complete AMS-V1 state required;
- no interpolation or time compression;
- exact volatility label mapping.

Accounting must retain:

`candidate_rows = accepted_rows + rejected_rows`.

All five registered inventory digests must be emitted.

Support remains:

- at least 5,000 accepted rows per asset;
- all 15 year × volatility-state cells;
- at least 200 rows per cell;
- at least 10 distinct UTC availability dates per cell.

If an asset fails support, all three primary slots for that asset become unavailable. All six slots remain in the multiplicity family. No threshold lowering, state/year merging, or sample rescue is permitted.

## Exact V2 empirical DWB

For every supported asset/hypothesis:

- call `numerical_inputs(sample)`;
- construct exact-time `ParzenGeometry(hours, segments)`;
- construct `FixedOLS(design)`;
- observed statistic = `wald(model.fit(target, geometry), hypothesis)`;
- null-imposed components = `restricted_components(design, target, geometry, hypothesis)`;
- for each requested draw use exactly:
  `pseudo_y = restricted_fitted + centered_restricted_residual * multipliers`;
- refit with `model.fit(pseudo_y, geometry)`;
- evaluate `wald(..., hypothesis)`;
- request exactly 4,999 draws;
- never redraw invalid draws;
- invalid draws count as exceedances;
- compute the raw p-value through frozen `bootstrap_p_value`.

Forbidden for empirical p-values:

- `engineering_fixture`;
- `wald_zero`;
- asymptotic chi-square fallback;
- alternate bootstrap implementation.

Hypothesis order:

1. DEP
2. TIME
3. STATE

Asset order:

1. BTCUSDT
2. ETHUSDT

## Empirical bootstrap seed namespace

Frozen empirical root:

`2026092201`.

Distinct synthetic roots remain:

- engineering `2026092001`;
- calibration `2026092002`;
- holdout `2026092003`.

Exact pre-segment seed path:

`[2026092201, 2, 4294967295, 4294967295, asset_index, hypothesis_index, bootstrap_index]`.

Frozen V2 `ParzenGeometry.multipliers` appends `segment_ordinal`.

Indices are zero-based:

- asset 0=BTCUSDT, 1=ETHUSDT;
- hypothesis 0=DEP, 1=TIME, 2=STATE;
- bootstrap index 0..4998.

No rerolls, alternate roots, mutable RNG streams, draw substitutions, seed changes, calibration roots, or holdout roots are allowed.

## Original-fit and bootstrap-invalidity policy

If the original unrestricted fit/restriction statistic cannot be computed:

- `available=false`;
- `raw_p=null`;
- the slot remains in the six-slot family.

For available slots, invalid bootstrap draws remain requested draws and conservatively count as exceedances.

Artifact fields per slot include:

- availability;
- observed Wald;
- requested draws;
- invalid draws;
- invalid fraction;
- raw p-value.

If **any available slot** has:

`invalid_fraction > 0.01`

the whole run classification is:

`EMPIRICAL_INFERENCE_VALIDITY_FAIL`.

Raw mechanical values remain audit evidence, but:

- Holm adjusted/reject interpretation is withheld;
- no promotion decision is valid;
- no rerun or method adjustment may rescue V1.

## Six-slot family

Exact order:

1. BTC_DEP
2. BTC_TIME
3. BTC_STATE
4. ETH_DEP
5. ETH_TIME
6. ETH_STATE

When the validity screen passes, exactly these six raw values, including `None` for unavailable slots, go to frozen `holm_six`.

No slot dropping, family splitting, per-asset correction, hypothesis reordering, or extra primary test is allowed.

Alpha remains 0.05.

## Cross-asset scope

The runner must emit exact accepted-predictor timestamp intersection count and SHA-256 digest using the certified exact-join primitive.

Directed 1/6/24-hour BTC↔ETH diagnostics remain:

`BLOCKED_PENDING_SEPARATE_CROSS_ASSET_LAG_INTEGRITY_SPEC`.

They must not execute.

## Numerical environment

Outcome-producing workflow pins:

- Python 3.12.14;
- NumPy 2.2.6;
- SciPy 1.15.3;
- float64;
- one BLAS thread per worker.

`pyproject.toml` is **not** in the allowed implementation surface for V1 remediation. If a runtime packaging change becomes necessary, stop and obtain a prospective amendment/review.

## Output artifact

The first empirical artifact must contain at minimum:

### Execution and authorization provenance

- executing commit;
- implementation candidate commit;
- independently reviewed implementation commit;
- expected equality of reviewed commit and candidate;
- canonical release-gate SHA-256;
- Development execution-manifest SHA-256;
- Development execution-spec SHA-256;
- machine registration SHA-256;
- implementation-freeze SHA-256;
- exact expected/observed Git blob pairs for every frozen result-affecting implementation path;
- package/runtime versions;
- workflow event;
- workflow run ID;
- run attempt;
- job ID where available;
- exact confirmation token/check status;
- durable claim ref;
- durable claim target commit;
- claim-created-before-source-access evidence.

### Source provenance, per asset

- historical whole-research parent manifest identity;
- exact 53-filename expected inventory;
- exact 53-filename observed inventory;
- official URLs;
- official checksum SHA-256 values;
- local ZIP SHA-256 values;
- authoritative Development raw `source_identity(paths)`;
- Development-only helper manifest raw-source identity;
- metadata source identity;
- stored/recomputed Development-only helper manifest identity;
- Development projection record;
- Development projection SHA-256;
- normalized dataset ID;
- normalized content hash;
- normalized row count/start/end;
- Development certification;
- Development certified segments/exclusions/continuity breaks only;
- explicit statement that generic Validation/OOS helper partition objects are non-authoritative and were not evidence of protected-partition reads.

### Sample provenance, per asset

- loaded/candidate/accepted/rejected counts;
- five inventory digests;
- rejection reason counts;
- all 15 support cells;
- support pass/fail.

### Inference and seed provenance

- exact six slots/order;
- empirical root `2026092201`;
- version coordinate `2`;
- DGP/outer sentinels `4294967295`;
- asset and hypothesis order;
- exact seed-coordinate schema;
- 4,999 requested draws;
- availability;
- observed Wald;
- invalid draw count/fraction;
- raw p-values;
- adjusted Holm values/reject flags only if the inference-validity screen passes;
- exact hour-vector and segment-vector digests per asset;
- exact cross-asset intersection count/digest;
- explicit `engineering_fixture_used_for_empirical_p_value=false`;
- explicit `wald_zero_used_for_empirical_p_value=false`.

### Protected-access flags

- `market_data_accessed=true`;
- `development_market_outcomes_accessed=true`;
- `validation_or_oos_accessed=false`;
- `strategy_pnl_calculated=false`;
- `paper_trading_authorized=false`;
- `live_trading_authorized=false`;
- `directed_cross_asset_lagged_diagnostics_executed=false`;
- `calibration_or_holdout_seed_used=false`.

## Result classification

A technically valid completed run uses:

`AMS_DEP_DEVELOPMENT_EMPIRICAL_V1_EXECUTED`.

This means only that the preregistered Development dependence analysis executed with valid source/inference plumbing.

It is not a statement that any hypothesis is significant, predictive, economically useful, or profitable.

Source/provenance/integrity failure uses nonzero exit and:

`AMS_DEP_DEVELOPMENT_EMPIRICAL_V1_INTEGRITY_FAIL`.

Bootstrap invalidity above 1% uses:

`EMPIRICAL_INFERENCE_VALIDITY_FAIL`.

## Post-exposure no-rescue rule

Once the durable claim is created, V1 exposure opportunity is consumed.

After claim/result exposure:

- no result-affecting V1 source, projection, code, seed, sample, support, numerical, multiplicity, or threshold change may rescue the outcome;
- material changes create a new prospectively reviewed execution-package version;
- post-claim infrastructure/source/inference failure requires independent incident review before any recovery path;
- Validation/OOS remains closed;
- P&L remains unauthorized;
- paper/live trading remain unauthorized.

A completed empirical artifact must undergo independent post-execution review before interpretation, follow-up research decisions, or any later protected-sample proposal.

## Allowed implementation surface after specification approval

Only after independent approval may implementation:

- add `src/research_core/ams_dep_development_source.py`;
- modify `src/research_core/ams_dep_empirical_access.py` narrowly for the fixed adapter and execution-manifest lock;
- add `research/scripts/run_ams_dep_development_empirical_v1.py`;
- add `src/research_core/ams_dep_development_execution_lock.py` if needed for fixed manifest/claim validation;
- add `research/governance/ams_dep_development_execution_manifest_v1.json`;
- add `research/governance/ams_dep_development_implementation_freeze_v1.json`;
- add dedicated Development source/projection/claim/seed/inference/firewall tests;
- add `.github/workflows/ams-dep-development-empirical-v1.yml`.

Not allowed:

- `pyproject.toml` changes;
- frozen V2 numerical-core changes;
- canonical `ams_dep_pipeline.py` changes;
- market-state changes;
- data-ingestion/source-identity changes;
- release-gate semantic weakening.

Any need to change a prohibited/frozen path stops implementation and requires a prospective amendment and independent review.

## Authorization consequence

Approval of this revised specification authorizes **implementation only**.

It does not set:

`development_market_data_execution_authorized=true`.

After implementation, exact blob freeze and independent implementation review remain mandatory before a separate governance-only execution authorization may be considered.
