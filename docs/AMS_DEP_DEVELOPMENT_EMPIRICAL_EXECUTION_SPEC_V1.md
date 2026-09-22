# AMS-DEP Development empirical execution specification V1

Status: **PROPOSED — PRE-OUTCOME — NOT AUTHORIZED FOR MARKET-DATA EXECUTION**

## Purpose

This specification defines the first outcome-producing AMS-DEP Development execution package after the independently accepted synthetic calibration, one-shot synthetic holdout, full-pipeline synthetic integrity certification, and separate empirical-release approval.

It freezes the source-acquisition inventory, production adapter behavior, numerical inference wiring, bootstrap seed namespace, output/provenance contract, and authorization workflow **before any empirical BTCUSDT/ETHUSDT archive is opened by this stage**.

This stage is not Validation/OOS, not a trading-strategy backtest, not P&L analysis, and not paper/live trading.

## Current governance state

Controlling branch at specification creation:

`adaptive-markets-research`

Controlling head:

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

## Frozen primary scientific contract

The execution must reuse without modification:

- `research_core.ams_dep_pipeline` canonical bundle verification, row construction, support, numerical-input and exact-join logic;
- `research_core.market_state.build_market_states`;
- `research_core.data_quality_treatment_v2.build_manifest` and `return_eligible`;
- `research_core.source_identity.source_identity` / `bind_source_identity`;
- `research_core.data_ingestion` archive parsing, dataset identity and content hashing;
- `research_core.dependence_statistics.primary_design`, `RESTRICTIONS`, `SLOTS`, and `holm_six`;
- `research_core.dependent_wild_bootstrap_v2.FixedOLS`, `ParzenGeometry`, `wald`, `restricted_components`, and `bootstrap_p_value`.

The bounded `engineering_fixture` is **not** the empirical inference method and must not be used to generate empirical p-values.

The old asymptotic `dependence_statistics.wald_zero` chi-square p-value is not the accepted V2 empirical inference method and must not be substituted.

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

No Validation archive month beginning 2022-01 or later may be requested or opened.

## Exact source inventory

For each asset, the source inventory is the deterministic monthly sequence from **2017-08 through 2021-12 inclusive**, exactly 53 monthly ZIP archives per asset.

Filename rule:

`{SYMBOL}-1h-{YYYY}-{MM}.zip`

Official archive URL must be generated only through the frozen `data_ingestion.archive_url(symbol, year, month)` helper.

The corresponding official checksum document is exactly:

`archive_url + ".CHECKSUM"`.

No caller may provide:

- a source URL;
- an archive path;
- a data root;
- a mirror;
- an alternate symbol;
- an alternate timeframe;
- an alternate month range.

The source adapter must create its own temporary local staging directory. No pre-existing arbitrary local archive directory may be injected through the public API or CLI.

## Acquisition and checksum rule

Each of the 106 expected ZIPs must be acquired from the exact official Binance Public Data URL and verified against its official `.CHECKSUM` before it is eligible for source construction.

The implementation must call the existing `download_archive(..., verify_checksum=True)` or an exactly behavior-preserving wrapper around it.

For every archive, the execution artifact must record:

- symbol;
- year/month;
- filename;
- official URL;
- official checksum value;
- independently computed local ZIP SHA-256.

Acquisition failure, checksum failure, missing archive, duplicate filename, unexpected archive, alternate host, or fallback mirror is a hard failure.

No partial-source inference is allowed.

## Registered treatment identities

The already frozen treatment-manifest identities remain:

- BTCUSDT:
  `1590cf8e69ed757eeb6701a218d561448beb2eb6ea09dcd0ae31d15a8f5197cf`;
- ETHUSDT:
  `d35bf21e309820abc88090bad29601adc1d1ea6b31dcddf0b80d510af4cf542f`.

The adapter must construct each bundle using the existing canonical `build_certified_bundle_from_archives` path and then call `verify_certified_bundle` with the production registered identity.

If the actual Development-only official archive set cannot reproduce the registered treatment identity, execution must hard-fail **before state construction, primary-row construction, DWB inference, or output interpretation**.

No identity may be changed after observing that failure. Any identity-contract correction requires a new versioned pre-outcome amendment and independent review.

## Protected partition firewall

Before any network request or source read, production execution must require all existing empirical release conditions including:

- `full_pipeline_synthetic_integrity_passed=true`;
- `separate_empirical_release_approved=true`;
- `development_market_data_execution_authorized=true`.

It must also require a separate execution manifest to be in an authorized state and bind the reviewed implementation candidate.

Validation/OOS must remain false.

No source adapter may request data for 2022-01 or later.

## New execution-manifest layer

Implementation must add:

`research/governance/ams_dep_development_execution_manifest_v1.json`.

Before independent implementation review it must be:

- `status=DRAFT_LOCKED`;
- `development_execution_authorized=false`;
- `first_empirical_execution_executed=false`;
- reviewed implementation commit unset;
- exact implementation blob pins recorded after implementation freeze.

Before the first empirical execution, independent review must approve the implementation/freeze. A later governance-only transition may then set:

- `status=AUTHORIZED_FOR_FIRST_DEVELOPMENT_EXECUTION`;
- reviewed implementation commit equal to the frozen candidate;
- independent implementation review true;
- `development_execution_authorized=true`.

The canonical release gate and the execution manifest must both authorize before source acquisition.

## Canonical first empirical runner

The first outcome-producing runner must be a new versioned script:

`research/scripts/run_ams_dep_development_empirical_v1.py`.

It must run **both assets in one execution**. Selective BTC-only or ETH-only execution is not permitted for the first primary six-test family.

The runner may accept an internal output path for workflow plumbing, but must expose no user-controlled:

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
- Validation/OOS option;
- P&L/trading option.

## Canonical sample and support

For each asset, after bundle verification the runner must call the frozen canonical primary sample builder.

The frozen semantics remain:

- predictor `x_t = log(C_t/C_(t-1))`;
- target `y_t = log(C_(t+1)/C_t)`;
- state at `t`;
- availability/year at `t+1h`;
- `t-1`, `t`, `t+1` in the same certified segment;
- all endpoints inside Development;
- 744-bar warm-up reset per certified segment;
- complete AMS-V1 state required;
- no time compression/interpolation;
- exact volatility mapping only.

Accounting must retain:

`candidate_rows = accepted_rows + rejected_rows`.

All five registered inventory digests must be emitted.

Support remains:

- at least 5,000 accepted rows per asset;
- all 15 year × volatility-state cells emitted;
- at least 200 rows per cell;
- at least 10 distinct UTC availability dates per cell.

If an asset fails support, all three primary slots for that asset are unavailable. The slots remain in the six-test family as unavailable entries; no threshold lowering or sample rescue is permitted.

## Exact V2 empirical DWB

For every supported asset/hypothesis, use:

- `numerical_inputs(sample)`;
- `ParzenGeometry(hours, segments)`;
- `FixedOLS(design)`;
- observed statistic from `wald(model.fit(target, geometry), hypothesis)`;
- null-imposed fitted/residual components from `restricted_components`;
- exactly 4,999 requested dependent-wild-bootstrap draws;
- invalid draws never redrawn;
- invalid draws count as exceedances;
- p-value from frozen `bootstrap_p_value`.

Hypothesis order per asset:

1. DEP
2. TIME
3. STATE

Asset order:

1. BTCUSDT
2. ETHUSDT

## Empirical bootstrap seed namespace

Empirical bootstrap root is prospectively frozen as:

`2026092201`.

This is distinct from the V2 synthetic roots:

- engineering: `2026092001`;
- calibration: `2026092002`;
- holdout: `2026092003`.

For `ParzenGeometry.multipliers`, the exact seven-coordinate pre-segment seed path is:

`[2026092201, 2, 4294967295, 4294967295, asset_index, hypothesis_index, bootstrap_index]`.

Then the unchanged V2 implementation appends `segment_ordinal`.

Indices are zero-based:

- asset_index 0=BTCUSDT, 1=ETHUSDT;
- hypothesis_index 0=DEP, 1=TIME, 2=STATE;
- bootstrap_index 0..4998.

No rerolls, alternate roots, mutable RNG streams, draw substitutions, or seed changes after result exposure are allowed.

## Original-fit and bootstrap-invalidity policy

If the original unrestricted fit/restriction statistic cannot be computed for a slot, that slot is unavailable:

- `raw_p=null`;
- `available=false`;
- it remains in the six-slot family.

For an available slot, invalid bootstrap draws are retained under the frozen conservative rule.

The artifact must report:

- observed Wald;
- requested draws;
- invalid draws;
- invalid fraction;
- raw p-value.

If any available slot has `invalid_fraction > 0.01`, the run is classified:

`EMPIRICAL_INFERENCE_VALIDITY_FAIL`.

In that case raw mechanical p-values may be retained for audit, but no Holm rejection interpretation or promotion decision is valid. No rerun or method adjustment may rescue V1.

## Six-slot family

The family must be exactly:

1. BTC_DEP
2. BTC_TIME
3. BTC_STATE
4. ETH_DEP
5. ETH_TIME
6. ETH_STATE

If the inference-validity screen passes, feed exactly those six raw values, including `None` for unavailable slots, to frozen `holm_six`.

No slot dropping, family splitting, per-asset multiplicity, hypothesis reordering, or post-result additional primary test is allowed.

Alpha remains 0.05 as implemented by the frozen Holm procedure.

## Cross-asset scope

The runner must emit the exact accepted-predictor timestamp intersection count and SHA-256 digest using the already certified exact-join primitive.

Directed 1/6/24-hour BTC↔ETH lagged diagnostics remain:

`BLOCKED_PENDING_SEPARATE_CROSS_ASSET_LAG_INTEGRITY_SPEC`.

They must not execute.

## Numerical environment

First execution workflow must pin:

- Python 3.12.14;
- NumPy 2.2.6;
- SciPy 1.15.3;
- float64;
- one BLAS thread per worker.

No distributed bootstrap sharding is required for six empirical slots unless a later reviewed implementation demonstrates deterministic equivalence. If parallelism is used, seed coordinates must make results execution-order invariant.

## Output artifact

The first empirical artifact must contain at minimum:

### Execution provenance
- executing commit;
- current release-gate SHA-256;
- Development execution-spec SHA-256;
- execution registration SHA-256;
- implementation-freeze SHA-256;
- package versions;
- workflow run/job identifiers where available.

### Source provenance, per asset
- exact 53-filename expected inventory;
- exact 53-filename observed inventory;
- official URLs;
- official checksum values;
- local ZIP SHA-256 values;
- authoritative raw `source_identity(paths)`;
- manifest source identity;
- metadata source identity;
- stored and recomputed treatment-manifest identities;
- normalized dataset ID;
- normalized content hash;
- source/certification status.

### Sample provenance, per asset
- loaded/candidate/accepted/rejected counts;
- five inventory digests;
- rejection reason counts;
- all 15 support cells;
- support pass/fail.

### Inference provenance
- exact six slots;
- availability;
- observed Wald;
- 4,999 requested draws for available slots;
- invalid draw count/fraction;
- raw p-values;
- adjusted Holm p-values and reject flags only if inference-validity screen passes;
- exact hour/segment vector digests per asset;
- exact cross-asset intersection count/digest.

### Protected-access flags
The artifact must explicitly record:

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

This token means only that the preregistered Development dependence analysis executed with valid source/inference plumbing.

It is **not** a statement that any hypothesis is significant, economically useful, predictive, or profitable.

Source/integrity failure uses a hard nonzero exit and:

`AMS_DEP_DEVELOPMENT_EMPIRICAL_V1_INTEGRITY_FAIL`.

Bootstrap invalidity above the frozen 1% ceiling uses:

`EMPIRICAL_INFERENCE_VALIDITY_FAIL`.

## Post-execution rule

After the first valid empirical artifact exists:

- no result-affecting V1 code/spec/seed/source/sample/multiplicity change may be made in response to the outcomes;
- any material change creates V2 of the empirical execution package and requires a prospective independent review;
- Validation/OOS remains closed;
- P&L remains unauthorized;
- paper/live trading remain unauthorized.

The first artifact must undergo independent post-execution review before any interpretation, follow-up research decision, or later protected-sample proposal.

## Implementation surface after specification approval

Only after independent approval of this specification may implementation:

- add `src/research_core/ams_dep_development_source.py`;
- modify `src/research_core/ams_dep_empirical_access.py` only as needed to invoke the fixed adapter and execution-manifest lock;
- add `research/scripts/run_ams_dep_development_empirical_v1.py`;
- add the Development execution manifest/freeze;
- add dedicated source-adapter, seed-wiring, inference-runner and firewall tests;
- add a manual Development empirical workflow with explicit confirmation;
- update `pyproject.toml` only if required for already frozen runtime versions.

The frozen V2 numerical core and canonical AMS-DEP pipeline must not be changed.

## Authorization consequence

Approval of this specification authorizes **implementation only**.

It does not set:

`development_market_data_execution_authorized=true`.

After implementation, a new implementation freeze and independent review are mandatory before a separate governance-only execution authorization may be considered.
