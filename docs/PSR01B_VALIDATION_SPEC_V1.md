# PSR-01B Validation Specification V1

**Registration ID:** `PSR01B-BOUNDED-VALIDATION-SPOT-V1`  
**Status:** `FROZEN_PENDING_INDEPENDENT_SPECIFICATION_REVIEW`  
**Repository head reviewed while preparing this draft:** `614859472715ac8dfa4489913ccb4a70d185412a`  
**Parent scientific registration:** `PSR01B-BOUNDED-DEVELOPMENT-SPOT-V1`, revision 4  
**Parent registration path:** `research/governance/psr01b_bounded_spec_v1.json`  
**Parent registration Git blob SHA-1:** `47c5379eeb4eae8c5890814c92e29b86bfddb23e`

## 1. Purpose and authority

This is a prospective **Validation-phase specification draft**, not an execution authorization. It extends the already frozen PSR-01B revision-4 scientific/statistical procedure into the protected Validation period without changing the method in response to Validation outcomes.

This draft does **not** authorize implementation, protected source access, empirical feature/model/forecast/P&L generation, OOS access, paper trading, live trading, leverage, derivatives execution, GitHub modification, claim creation, workflow dispatch, or any rerun.

The scientific claim remains bounded. Validation success, if later observed under separately authorized one-shot execution, would support a bounded declared-deviation mechanism validation claim. It would not establish exact replication of the source paper or reproduction of paper futures performance.

## 2. Exact scientific inheritance

Every scientific/statistical field of the parent revision-4 registration is inherited unchanged except the prospectively registered Validation phase/source/fold continuation and the governance/evidence adaptations explicitly enumerated here.

The following remain unchanged:

- OHLCV+TA+EGARCH feature definitions and the exact 28-column deployed order.
- 94 TA candidates, 10 selection groups, four three-calendar-month selection blocks, common four-block eligible rank universe, finite-pair threshold, Spearman ranking and lexical tie rules.
- Segmented EGARCH candidate orders `(1,1,1)`, `(2,1,1)`, `(1,1,2)`, `(2,1,2)`, their likelihood/reset/AIC contract, causal replay, and three EGARCH output features.
- XGBoost regressor, MSE selector, Optuna TPE, 50 trials, the complete search space, early stopping, deterministic trial tie rule and final refit.
- Training-only and train+validation target-standardization rules.
- `PAPER_FILL` and `PROJECT_GAP_PRESERVING` arms, including gap resets, forced liquidation, cash restart, and benchmark restart.
- Long-only `BASELINE_SIGN` and `COST_AWARE`, `c=0.001`, `lambda=2`, identical forecast vector per arm/fold, and the frozen forecast serialization/hash.
- `BUY_AND_HOLD` and `MOMENTUM_24H` contextual benchmarks.
- Fold metrics `fold_total_return`, `fold_ARC`, `fold_ASD`, `fold_SHARPE` and all consolidated metrics.
- Paired circular block bootstrap: primary 168h, diagnostics 24h/72h, 10,000 draws, no cross-fold/gap resampling, `n>=2L` inferential segment eligibility.
- Two-arm Holm family at alpha 0.05.
- Split endpoint rule and mandatory 744-hour artificial warmup/state boundary.
- Runtime: Ubuntu 24.04, Python 3.12.14, NumPy 2.2.6, SciPy 1.15.3, pandas 3.0.6, XGBoost 3.4.1, Optuna 5.0.0, arch 8.0.0, statsmodels 0.15.0; OPENBLAS/OMP/MKL/NUMEXPR thread counts all 1.
- No rescue after outcome.

### 2.1 Unchanged parent H2 criteria and Validation-phase tokens

The seven parent H2 criteria remain unchanged. The parent semantic classification remains internal and must be recorded exactly as:

- `BOUNDED_H2_REPLICATION`
- `BOUNDED_H2_NOT_REPLICATED`

The Validation phase adds an unambiguous terminal scientific token:

- parent H2 pass → `PSR01B_VALIDATION_BOUNDED_H2_REPLICATION`
- parent H2 fail, including a sample-driven `SCIENTIFIC_NON_REPLICATION` → `PSR01B_VALIDATION_BOUNDED_H2_NOT_REPLICATED`
- genuinely non-scientific technical terminal state → `PSR01B_VALIDATION_TECHNICAL_INDETERMINATE`

Final scientific evidence records both `parent_h2_classification` and `validation_result_token` where applicable. For a technical-indeterminate attempt, `parent_h2_classification` is JSON `null`; a technical failure must never masquerade as an H2 result.

H2 passes only if **all seven** parent criteria pass in both missing-data arms:

1. all-record observed mean net-return differential > 0;
2. primary 168h inference-universe observed mean net-return differential > 0;
3. at least two primary-inference-eligible contiguous segments, each `n>=336`;
4. Holm-adjusted primary one-sided p-value <= 0.05;
5. cost-aware turnover < baseline turnover;
6. cost-aware completed trades >= 20;
7. all-record cost-aware Sharpe - baseline Sharpe > 0.

### 2.2 Separate practical BUY_AND_HOLD gate

For each missing-data arm, all-record COST_AWARE Sharpe must be strictly greater than all-record BUY_AND_HOLD Sharpe.

Machine inequality: `all-record COST_AWARE Sharpe > all-record BUY_AND_HOLD Sharpe`

The practical gate passes only if that strict inequality holds in **both** `PAPER_FILL` and `PROJECT_GAP_PRESERVING`.

- PASS token: `PSR01B_VALIDATION_PRACTICAL_BENCHMARK_PASS`
- FAIL token: `PSR01B_VALIDATION_PRACTICAL_BENCHMARK_FAIL`

If BUY_AND_HOLD Sharpe is unavailable in either arm, the practical gate fails. If COST_AWARE Sharpe is unavailable, the practical gate also fails. On any scientific terminal path, the practical token is PASS only if both arm inequalities are established; otherwise it is FAIL. On a `TECHNICAL_INDETERMINATE` terminal path, the practical token is JSON `null` because no scientific/practical judgment is valid.

This gate is separate from the original H2 claim and cannot change the H2 classification or Validation H2 token.

A future OOS specification may be **considered only** if all three conditions hold:

1. `validation_result_token == PSR01B_VALIDATION_BOUNDED_H2_REPLICATION`;
2. `practical_benchmark_token == PSR01B_VALIDATION_PRACTICAL_BENCHMARK_PASS`;
3. Validation evidence has been persisted, independently audited, and governance-closed.

These conditions do **not** authorize OOS access, implementation, or execution.

## 3. Validation folds and stochastic continuation

The registered source interval is **[2020-08-31T00:00:00Z, 2024-01-01T00:00:00Z)**. The protected Validation evaluation interval is **[2022-01-01T00:00:00Z, 2024-01-01T00:00:00Z)**. Any timestamp at or after 2024-01-01T00:00:00Z is prohibited.

| Fold | fold_index | train start | validation start | test start | test end |
|---:|---:|---|---|---|---|
| 12 | 11 | 2020-10-01T00:00:00Z | 2021-10-01T00:00:00Z | 2022-01-01T00:00:00Z | 2022-04-01T00:00:00Z |
| 13 | 12 | 2021-01-01T00:00:00Z | 2022-01-01T00:00:00Z | 2022-04-01T00:00:00Z | 2022-07-01T00:00:00Z |
| 14 | 13 | 2021-04-01T00:00:00Z | 2022-04-01T00:00:00Z | 2022-07-01T00:00:00Z | 2022-10-01T00:00:00Z |
| 15 | 14 | 2021-07-01T00:00:00Z | 2022-07-01T00:00:00Z | 2022-10-01T00:00:00Z | 2023-01-01T00:00:00Z |
| 16 | 15 | 2021-10-01T00:00:00Z | 2022-10-01T00:00:00Z | 2023-01-01T00:00:00Z | 2023-04-01T00:00:00Z |
| 17 | 16 | 2022-01-01T00:00:00Z | 2023-01-01T00:00:00Z | 2023-04-01T00:00:00Z | 2023-07-01T00:00:00Z |
| 18 | 17 | 2022-04-01T00:00:00Z | 2023-04-01T00:00:00Z | 2023-07-01T00:00:00Z | 2023-10-01T00:00:00Z |
| 19 | 18 | 2022-07-01T00:00:00Z | 2023-07-01T00:00:00Z | 2023-10-01T00:00:00Z | 2024-01-01T00:00:00Z |

The seed sequence is a continuation, not a reset. `fold_index = fold - 1`, so folds 12–19 use indices 11–18. Model/Optuna/XGBoost coordinates therefore continue prospectively through indices 11–18. The bootstrap coordinate remains exactly `[bootstrap_root,block_hours,arm_index]`, intentionally has no fold/phase coordinate, and is therefore intentionally reused across Development and Validation; this is frozen parent behavior, not a reset or Validation tuning choice. The parent roots and paths remain:

- model root `2026092401`;
- bootstrap root `2026092402`;
- Optuna `[model_root,1,arm_index,fold_index]`;
- trial XGBoost `[model_root,2,arm_index,fold_index,trial_index]`;
- final XGBoost `[model_root,3,arm_index,fold_index,selected_trial_index]`;
- bootstrap `[bootstrap_root,block_hours,arm_index]`.

## 4. Source identity and acquisition

Source remains Binance Public Data, BTCUSDT Spot, 1h, UTC, monthly kline ZIPs. The archive inventory is exactly the 41 monthly archives from **2020-08 through 2023-12 inclusive**: `BTCUSDT-1h-2020-08.zip`, `BTCUSDT-1h-2020-09.zip`, `BTCUSDT-1h-2020-10.zip`, `BTCUSDT-1h-2020-11.zip`, `BTCUSDT-1h-2020-12.zip`, `BTCUSDT-1h-2021-01.zip`, `BTCUSDT-1h-2021-02.zip`, `BTCUSDT-1h-2021-03.zip`, `BTCUSDT-1h-2021-04.zip`, `BTCUSDT-1h-2021-05.zip`, `BTCUSDT-1h-2021-06.zip`, `BTCUSDT-1h-2021-07.zip`, `BTCUSDT-1h-2021-08.zip`, `BTCUSDT-1h-2021-09.zip`, `BTCUSDT-1h-2021-10.zip`, `BTCUSDT-1h-2021-11.zip`, `BTCUSDT-1h-2021-12.zip`, `BTCUSDT-1h-2022-01.zip`, `BTCUSDT-1h-2022-02.zip`, `BTCUSDT-1h-2022-03.zip`, `BTCUSDT-1h-2022-04.zip`, `BTCUSDT-1h-2022-05.zip`, `BTCUSDT-1h-2022-06.zip`, `BTCUSDT-1h-2022-07.zip`, `BTCUSDT-1h-2022-08.zip`, `BTCUSDT-1h-2022-09.zip`, `BTCUSDT-1h-2022-10.zip`, `BTCUSDT-1h-2022-11.zip`, `BTCUSDT-1h-2022-12.zip`, `BTCUSDT-1h-2023-01.zip`, `BTCUSDT-1h-2023-02.zip`, `BTCUSDT-1h-2023-03.zip`, `BTCUSDT-1h-2023-04.zip`, `BTCUSDT-1h-2023-05.zip`, `BTCUSDT-1h-2023-06.zip`, `BTCUSDT-1h-2023-07.zip`, `BTCUSDT-1h-2023-08.zip`, `BTCUSDT-1h-2023-09.zip`, `BTCUSDT-1h-2023-10.zip`, `BTCUSDT-1h-2023-11.zip`, `BTCUSDT-1h-2023-12.zip`. Only accepted normalized rows in **[2020-08-31T00:00:00Z, 2024-01-01T00:00:00Z)** may enter the experiment.

The phase-adapted manifest boundaries are frozen explicitly: Development is **[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)**, Validation is **[2022-01-01T00:00:00Z, 2024-01-01T00:00:00Z)**, and OOS begins at **2024-01-01T00:00:00Z**. The Validation implementation must never read, enumerate, inspect, select, infer from, or fall back to the OOS partition. Rows/events earlier than **2020-08-31T00:00:00Z** that physically exist in the August 2020 archive are outside the registered PSR source interval and cannot enter returned PSR rows, anomaly treatment, state, features, or fold-12 warmup propagation.

### 4.1 Historical overlap

For overlapping archives 2020-08 through 2021-12, use the exact SHA-256 identities already registered by the parent Development revision-4 specification. A different identity is not acceptable. Execution evidence must still identify and preserve the exact bytes actually used.

### 4.2 Protected 2022-2023 archives and permanent raw-byte evidence

Before the durable real Validation claim and successful post-create claim verification, there may be no `HEAD`, `GET`, checksum request, or equivalent metadata/byte request to a protected 2022-2023 source URL.

On the first successful verified acquisition of a protected archive, those bytes and their SHA-256 are latched for the remainder of the one-shot attempt. The archive may not be redownloaded after success or replaced by later upstream bytes.

**Permanent protected-interval consumption boundary:** after atomic real-claim creation and successful post-create verification, the **first protected 2022–2023 source or checksum request permanently consumes the full protected Validation interval [2022-01-01T00:00:00Z, 2024-01-01T00:00:00Z)** for PSR-01B Validation V1, even if no archive bytes are ultimately accepted. After that first protected request, operator cancellation, runner loss/cancellation, timeout, workflow termination, infrastructure failure, artifact/evidence failure, or any other non-scientific terminal path is terminal `PSR01B_VALIDATION_TECHNICAL_INDETERMINATE`; the one-shot attempt remains consumed, no rerun/second claim/alternate request sequence/OOS progression is permitted, and all independently recoverable request/evidence material must be preserved with explicit permanent evidence gaps for anything unrecoverable.

For **every registered archive actually used**, immutable evidence persists:

- filename;
- byte length;
- SHA-256;
- official checksum value;
- exact HTTPS source URL;
- the exact raw ZIP bytes used.

The local execution namespace freezes:

- raw directory: `research/experiments/psr01b_validation_v1/raw_source`
- manifest: `research/experiments/psr01b_validation_v1/raw_source_manifest.json`
- package: `research/experiments/psr01b_validation_v1/psr01b_validation_raw_source_v1.tar`

The package contains the exact accepted ZIP files under their registered filenames. Final evidence binds the package SHA-256/byte length, manifest SHA-256, and every per-archive SHA-256/checksum/source URL.

Because protected 2022-2023 identities cannot be preregistered without contaminating Validation, hashes alone are not sufficient. Governance closeout is forbidden until the raw-source package, or an exact byte-identical equivalent, is copied from the ephemeral runner to a **separately immutable, non-expiring evidence object/store** and that stable identifier plus SHA-256 is bound into closeout evidence. An expiring Actions artifact alone is insufficient.

No raw row with timestamp at or after `2024-01-01T00:00:00Z` may enter treatment output, state, features, fitting, forecasting, returns, metrics or inference.

### 4.3 Transport/retry policy — inherited Development behavior, explicitly frozen

Validation retains the reviewed Development transport loop:

- archive URL: exact registered **HTTPS** Binance Public Data URL only;
- checksum URL: `archive URL + ".CHECKSUM"`;
- `urllib.request.urlopen` timeout: **60 seconds** for archive and checksum requests;
- maximum attempts: **4**;
- retry delays: **5s, 15s, 45s**;
- retry HTTP **429** and **500–599**;
- retry `URLError`, `TimeoutError`, `socket.timeout`, `ConnectionError`;
- other HTTP 4xx are nonretryable;
- malformed checksum document is nonretryable;
- official checksum or deterministic identity/contract mismatch is nonretryable;
- delete any partial destination before every retry and after every failed attempt;
- ZIP/member validation uses the pinned existing scanner/archive-security rules;
- truncated/corrupt ZIP is a source/integrity `TECHNICAL_INDETERMINATE` terminal failure;
- redirect handling is exactly the pinned Python 3.12.14 `urllib.request.urlopen` behavior; no ad hoc operator/manual redirect handling, URL substitution or alternate mirror is allowed;
- the source-acquisition ledger records **every archive request and every checksum request attempt** with archive name, attempt number, request kind, exact URL, outcome/HTTP status or exception type, and acceptance status.

There is no Validation-specific change to Development retry count or delays.

## 5. Phase-safe row-treatment linkage

The frozen Development normalizer blob is `8c257290ff04e726b53cafa433596311dcec32c4` at `src/research_core/ams_dep_treatment_aware_normalization_v2.py`.

The complete parent Development project-local normalization/scanner/archive/source import closure and its exact Git blob SHA-1 map are frozen in the JSON `row_treatment_contract.required_blob_sha1`, inherited from parent revision 4. Every pinned parent module must remain byte-identical. Validation-specific phase adaptation must be implemented only in **new wrapper/adapter code** that calls the pinned parent modules without editing their registered semantics. The exact new wrapper/adapter inventory must itself be frozen and independently reviewed before any protected Validation source access. No wrapper/adapter may read, enumerate, inspect, select, infer from, or fall back to an OOS partition.

The prior idea of simply changing the Development constants, partition selector and names is insufficient because the Validation source interval spans pre-2022 historical rows plus 2022-2023 protected rows.

### 5.1 Chosen machine-enforceable rule: Design B — timestamp-directed registered partition

For every localized scanner `DataQualityEvent` with `parsed_timestamp` inside the registered source interval:

1. Compute `affected = hour(parsed_timestamp)` exactly as the frozen normalizer does.
2. Compute the exact frozen `event_id(event)`.
3. If `2020-08-31T00:00:00Z <= affected < 2022-01-01T00:00:00Z`, select **exactly one** manifest partition named `development`.
4. If `2022-01-01T00:00:00Z <= affected < 2024-01-01T00:00:00Z`, select **exactly one** manifest partition named `validation`.
5. Partition cardinality must be exactly one.
6. The event is treatment-linked iff an exclusion in that selected partition satisfies `start <= affected < end` and the exact frozen event ID is in `exclusion.anomaly_ids`.
7. An in-interval localized anomaly without such linkage hard-fails source integrity; it is never silently accepted.
8. A timestamp at/after `2024-01-01T00:00:00Z` hard-fails before treatment or any scientific use.
9. The adapter must never inspect, select, infer from, or fall back to an OOS partition.
10. Rows physically present before 2020-08-31 in the August 2020 archive cannot enter returned PSR source rows or propagate state across the mandatory fold-12 warmup boundary.

For pre-2022 events, the event-ID/exclusion test is therefore the **same frozen Development rule against the Development partition**. For 2022-2023 events the same rule is applied prospectively against the Validation partition. No treatment rule is chosen from observed Validation contents.

This remediation is explicitly **not** characterized as only five AST substitutions.

## 6. Mandatory synthetic/fault-injection tests before any implementation freeze

Implementation must prove, without protected data:

- **Pre-boundary equivalence:** synthetic events at 2021-12-31 22:00 and 23:00 produce the same linkage/rejection result as frozen Development semantics.
- **Boundary dispatch:** 2021-12-31 23:00 selects Development; 2022-01-01 00:00 and 01:00 select Validation.
- **Validation linkage:** synthetic 2022 and 2023 events obey the identical event-ID/exclusion-window rule.
- **Hard end:** 2024-01-01 00:00 and later fail before row use, feature/state propagation, model input, forecast, return or scientific classification.
- **No historical-side distortion:** paired synthetic anomalies on opposite sides of the boundary prove that only the registered partition changes; scanner classification, event ID, exclusion-membership rule, rejected-row accounting and normalization semantics remain identical.
- **No OOS access:** fault injection proving no OOS partition can be read, enumerated, inspected, selected, inferred from, or used as fallback. Instrument an OOS sentinel that raises on any such access and exercise pre-boundary, Validation, missing-link and hard-end paths; the sentinel must never be touched.
- **Operator-log outcome suppression:** synthetic-only fault injection with recognizable sentinel empirical values across Optuna, XGBoost, arch, statsmodels, feature/model selection, fold/test return/P&L, H2-progress and practical-gate paths. Capture stdout/stderr/workflow-visible logs and fail if any forbidden sentinel empirical value/pattern is emitted; required final synthetic evidence may retain the values.

## 7. Failure taxonomy and complete undefined-metric semantics

The accepted governing principle remains: if source integrity, frozen implementation identity, runtime identity and execution integrity are valid, and the frozen scientific procedure cannot produce a required component on the observed Validation sample, classify `SCIENTIFIC_NON_REPLICATION`. Reserve `TECHNICAL_INDETERMINATE` for source/infrastructure/runtime/implementation-invariant/transport/provenance/evidence failures that prevent a fair scientific execution.

A sample-driven scientific failure maps to parent H2 `BOUNDED_H2_NOT_REPLICATED` and Validation token `PSR01B_VALIDATION_BOUNDED_H2_NOT_REPLICATED`. A technical terminal state maps only to `PSR01B_VALIDATION_TECHNICAL_INDETERMINATE`, with `parent_h2_classification=null`.

The deterministic nonfinite-forecast rule remains unchanged:

- correct one-dimensional shape + exact test-origin length + prior integrity gates passed + normal model return + any nonfinite forecast element → `SCIENTIFIC_NON_REPLICATION`;
- wrong shape/length/alignment, structural exception, runtime corruption or deterministic implementation invariant failure → `TECHNICAL_INDETERMINATE`.

### 7.1 Exhaustive metric-unavailability rules

`NaN` and `Infinity` are forbidden everywhere. JSON `null` is permitted only for the explicitly allowed mathematical ASD/Sharpe-unavailability cases below. No unavailable metric may be silently dropped from a required criterion.

| Metric/state | Required behavior | H2 effect | Practical effect |
|---|---|---|---|
| fold ASD unavailable | serialize `fold_ASD=null` | none directly | none |
| fold Sharpe unavailable | serialize `fold_SHARPE=null`; descriptive only | none directly if required consolidated H2 quantities remain valid | none |
| consolidated BASELINE_SIGN ASD/Sharpe unavailable | serialize permitted ASD/Sharpe as `null` | criterion 7 false → scientific non-replication → Validation H2 NOT_REPLICATED | none directly |
| consolidated COST_AWARE ASD/Sharpe unavailable | serialize permitted ASD/Sharpe as `null` | criterion 7 false → scientific non-replication → Validation H2 NOT_REPLICATED | practical FAIL because required COST_AWARE Sharpe is unavailable |
| consolidated BUY_AND_HOLD ASD/Sharpe unavailable | serialize permitted ASD/Sharpe as `null` | H2 separately classified | practical FAIL |
| consolidated MOMENTUM_24H ASD/Sharpe unavailable | serialize permitted ASD/Sharpe as `null` | no direct change | no direct change |
| any nonfinite fold metric not covered by permitted ASD/Sharpe null semantics | forbidden | technical indeterminate | no valid practical judgment |
| any nonfinite consolidated metric not covered by permitted ASD/Sharpe null semantics | forbidden | technical indeterminate | no valid practical judgment |
| invalid/nonfinite fold or consolidated total return/ARC | forbidden | technical indeterminate | no valid practical judgment |
| any nonfinite registered return | forbidden | technical indeterminate | no valid practical judgment |
| any registered return with `1+r <= 0` | forbidden | technical indeterminate | no valid practical judgment |
| impossible/nonfinite equity, peak or drawdown state | forbidden | technical indeterminate | no valid practical judgment |

An isolated unavailable **fold Sharpe** does not by itself fail H2 because fold Sharpe is descriptive and not one of the seven H2 criteria.

Registered strategy returns derive from `exp(realized_log_return)-1` plus explicit registered costs. A nonfinite return, `1+r<=0`, invalid total-return/ARC state, or impossible equity/accounting state is therefore a mathematical/implementation integrity failure and is `TECHNICAL_INDETERMINATE`, not an empirical H2 judgment.

### 7.2 Retained scientific classifications

The accepted scientific classifications remain:

- no eligible candidate in a required TA group because of registered sample eligibility → `SCIENTIFIC_NON_REPLICATION`;
- all registered EGARCH orders unavailable because of valid-sample numerical failure → `SCIENTIFIC_NON_REPLICATION`;
- valid-sample zero/nonfinite target standard deviation → `SCIENTIFIC_NON_REPLICATION`;
- no eligible training or inner-validation rows after registered causal/data-treatment rules → `SCIENTIFIC_NON_REPLICATION`;
- insufficient primary 168h inference support → `SCIENTIFIC_NON_REPLICATION`;
- required consolidated BASELINE_SIGN/COST_AWARE Sharpe unavailable → H2 criterion 7 false and `SCIENTIFIC_NON_REPLICATION`;
- BUY_AND_HOLD Sharpe unavailable → practical FAIL, with H2 separately classified;
- MOMENTUM_24H Sharpe unavailable → descriptive benchmark unavailable, with no direct H2/practical effect.

Every post-claim terminal state consumes the single attempt. No rerun is authorized. After the first protected source/checksum request, cancellation, runner loss, timeout, workflow termination, infrastructure loss or inability to finalize local evidence is specifically `TECHNICAL_INDETERMINATE`, permanently consumes the protected Validation interval, and makes the attempt ineligible for OOS progression. No scientific H2/practical judgment may be inferred from that terminal path.

## 8. Exact result, incident, evidence and outcome-suppression contract

The Validation execution namespace is frozen as:

`research/experiments/psr01b_validation_v1`

Exact runtime evidence paths are:

- `research/experiments/psr01b_validation_v1/result.json`
- `research/experiments/psr01b_validation_v1/result.json.reservation`
- `research/experiments/psr01b_validation_v1/terminal_incident.json`
- `research/experiments/psr01b_validation_v1/raw_source/`
- `research/experiments/psr01b_validation_v1/raw_source_manifest.json`
- `research/experiments/psr01b_validation_v1/psr01b_validation_raw_source_v1.tar`

`result.json.reservation`, `result.json`, and `terminal_incident.json` are exclusive-create/no-overwrite paths. The incident path is independent of the result path.

### 8.1 Deterministic order

Future runtime order is exactly:

1. PRE_SOURCE result/evidence-path reservation;
2. atomic real Validation claim creation;
3. post-create real-claim verification;
4. protected source acquisition;
5. scientific execution;
6. `result.json` write **only if scientifically completed**;
7. `terminal_incident.json`/provenance finalization;
8. artifact upload using GitHub Actions `if: always()` or equivalent.

A technical terminal state must not fabricate H2 metrics or a scientific `result.json`.

### 8.2 Required terminal incident fields

At minimum `terminal_incident.json` records:

- execution SHA;
- reviewed candidate SHA;
- run_id;
- run_attempt;
- actor;
- claim ref;
- claim tag-object SHA;
- claim target SHA;
- stage;
- terminal classification;
- Validation result token;
- whether source access occurred;
- every source acquisition attempt already made;
- every source hash obtained before failure;
- whether `result.json` exists;
- error type/message where applicable;
- Validation boundary status;
- OOS boundary status.

It never fabricates scientific metrics.

### 8.3 Required final scientific fields

Where applicable, final evidence records:

- `parent_h2_classification`;
- `validation_result_token`;
- `practical_benchmark_token`.

For a technical-indeterminate terminal state, `parent_h2_classification=null` and `practical_benchmark_token=null`.

### 8.4 Outcome suppression

Before immutable terminal evidence:

- no fold-level Validation test return or P&L in logs;
- no partial H2 status in logs;
- no partial practical-gate status in logs;
- no intermediate empirical result artifact;
- no operator-facing partial test metric intended to permit outcome-based cancellation;
- model/feature-selection details may be persisted in final registered evidence but **must not** be streamed as partial empirical outcome evidence;
- empirical progress/output from Optuna, XGBoost, arch and statsmodels must be configured, captured, suppressed or redacted so trial objectives/best values, losses/early-stopping values, EGARCH likelihood/AIC/fit summaries, statistical summaries and other protected empirical values do not reach operator-facing stdout/stderr/GitHub logs;
- synthetic/offline implementation testing must include the mandatory `OPERATOR_LOG_OUTCOME_SUPPRESSION` no-leak test described above; any forbidden sentinel leakage fails the gate;
- no cancellation, retry, runner-loss or failure path after the real claim can create a second real claim or second empirical Validation attempt.

Artifact upload must execute on success or failure using `if: always()` or equivalent and include all evidence paths that exist, including permanent-raw-source staging/binding material.

### 8.5 Runner-loss and permanent evidence-gap closeout

After the first protected Validation request, loss/cancellation of the runner or inability to finalize local result/incident/raw-source evidence is terminal `PSR01B_VALIDATION_TECHNICAL_INDETERMINATE`. The consumed real claim and attempt are never reopened. Governance must preserve independently recoverable run/attempt/actor/execution-SHA/claim provenance, source-request ledger material, source hashes/raw bytes and artifact/object identities that exist outside the lost runner. Any expected local object that cannot be recovered is recorded as an explicit **permanent evidence gap** with the last independently provable stage; it is never fabricated or reconstructed as if the runner produced it.

The canonical non-expiring Git raw-source evidence namespace is `research/experiments/psr01b_validation_v1/evidence/raw_source/`. Exact accepted protected ZIP bytes must be preserved there as immutable Git blobs, or in an exact byte-identical separately immutable non-expiring object/store whose stable identifier and SHA-256 are bound into closeout evidence. An expiring Actions artifact alone is insufficient. A consumed technical-indeterminate attempt is not eligible for OOS progression.

## 9. Complete one-shot governance lifecycle

The protected real claim remains:

`refs/tags/psr01b-validation-one-shot-claim-v1`

Before **any** real Validation source access, the lifecycle is exactly:

1. frozen Validation specification committed;
2. independent specification review and approval;
3. bounded Validation implementation only;
4. synthetic/offline tests;
5. fault-injection tests;
6. implementation freeze;
7. protected reviewed-candidate anchor;
8. protected future real Validation claim ruleset;
9. independent implementation + holdout-firewall review;
10. exact-head downloader-free PRE_SOURCE rehearsal using a run/attempt-specific throwaway rehearsal claim;
11. post-rehearsal unchanged-head independent recheck;
12. separate Validation execution-authorization review;
13. owner manual confirmation;
14. result/evidence-path reservation;
15. atomic creation of the protected real Validation claim;
16. post-create claim verification;
17. only then first protected Validation source/checksum request;
18. **ONE** empirical Validation execution.

### 9.1 Real-claim protection

Freeze all of the following:

- pre-existing real claim → **HARD STOP**;
- atomic creation binds the exact execution SHA;
- annotated claim provenance contains `run_id`, `run_attempt`, and `actor`;
- post-create ref target, tag-object, execution SHA, run/attempt or actor mismatch → **HARD STOP**;
- source access is forbidden until post-create verification passes;
- the protected claim ruleset prohibits update, deletion and non-fast-forward/replacement;
- no bypass actor is allowed;
- real-claim recreation is forbidden;
- every post-claim terminal state consumes the attempt;
- after successful post-create verification, the first protected 2022–2023 source/checksum request permanently consumes the full Validation interval for this program, even if no archive is accepted;
- cancellation/runner loss after that first protected request is terminal `PSR01B_VALIDATION_TECHNICAL_INDETERMINATE`, cannot be retried and cannot become OOS-eligible;
- no second real claim or second empirical Validation attempt exists.

### 9.2 PRE_SOURCE rehearsal

The exact-head PRE_SOURCE rehearsal uses a run/attempt-specific throwaway rehearsal claim that is distinct from the real claim. It is downloader-free, must never create the real claim, and must never issue any protected Validation source/checksum request or read Validation source bytes.

This draft still authorizes none of the lifecycle steps that constitute implementation or empirical execution.

## 10. Internal-consistency resolution

The final-freeze blockers are resolved prospectively without Validation/OOS access and without changing the accepted scientific/statistical design:

- phase-specific Validation tokens now coexist with the parent H2 classification, and technical failure cannot masquerade as H2;
- the full two-arm `COST_AWARE Sharpe > BUY_AND_HOLD Sharpe` practical gate is restored with separate PASS/FAIL tokens;
- metric unavailability is exhaustively machine-classified, with only registered ASD/Sharpe cases permitted as JSON `null`;
- the full 18-step governance lifecycle, real-claim protections and downloader-free rehearsal are frozen;
- exact result/reservation/incident paths, deterministic write order, always-run artifact upload and empirical outcome suppression are frozen;
- Development transport semantics are preserved with explicit HTTPS/checksum/60-second timeout/redirect/ledger rules, and the exact raw ZIP bytes used are required as permanent immutable evidence;
- the accepted folds 12–19, indices 11–18, source/Validation intervals, timestamp-directed Development/Validation treatment linkage, no-OOS fallback, revision-4 scientific/statistical procedure, 4-attempt 5/15/45 transport retry schedule, sample-driven scientific-failure principle, and one-shot/no-rescue principle are unchanged;
- Issue #111 remediation additionally freezes permanent interval consumption after first protected request, mandatory operator-log outcome suppression/no-leak tests, explicit phase-adapted manifest/archive/pinned-wrapper/OOS contracts, runner-loss permanent evidence-gap handling with a canonical non-expiring Git raw-source evidence namespace, and the intentional distinction between fold-index seed continuation and bootstrap-seed reuse.

**Freeze status:** `FROZEN_PENDING_INDEPENDENT_SPECIFICATION_REVIEW`
