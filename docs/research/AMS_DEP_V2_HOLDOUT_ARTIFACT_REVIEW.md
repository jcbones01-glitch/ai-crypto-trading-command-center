# AMS-DEP V2 detailed holdout artifact review — 2026-09-21

Status: **HOLDOUT ARTIFACT CONTENT VERIFIED; REGISTERED SYNTHETIC SCREEN PASS; GOVERNANCE TRANSITION PENDING INDEPENDENT REVIEW**.

This review resolves the content-audit blocker recorded after run 35529411234. It is an arithmetic/provenance audit of the aggregate holdout results supplied from the completed GitHub Actions artifact. It is not an independent rerun of the 659,868,000 requested inner bootstrap draws, not empirical market evidence, and not authorization to access Development market data, Validation/OOS, strategy P&L, paper trading or live trading.

## Evidence and provenance

- Workflow run: `35529411234` — **SUCCESS**.
- Execution branch: `ams-dep-v2-holdout-prep`.
- Execution / one-shot claim commit: `80d0fb5a90a6c4dc02073605159c38f520ad3410`.
- Aggregate job: `106443566096` — **SUCCESS**.
- Aggregate log reports both:
  - `AMS_DEP_V2_HOLDOUT_SCREEN=PASS`
  - `AMS_DEP_V2_HOLDOUT_PASS`
- GitHub aggregate artifact: `10655486394`, `ams-dep-v2-holdout-results`, 979668 bytes.
- GitHub upload log reports artifact ZIP SHA-256:
  `0208861fc4dbeed2d6dda1a6b574678eb59957e628f1a521ba6c56227ef5435d`.
- The user supplied the two extracted aggregate members through connected Google Drive:
  - `summary.json`, 66946 bytes;
  - `outer_results.jsonl.gz`, 975761 bytes.
- Independently calculated `summary.json` SHA-256:
  `ad66d2a8b153e9e98209e82dbb475de4a7714d178233e0ebb0d7d6a749a01ebd`.
- Independently calculated compressed outer-ledger SHA-256:
  `089b5be7b049090a22be17c04b266e0247c384df58f06ee3a2090bfb795cbb5d`.
  This exactly matches `summary.json.outer_ledger_sha256`.
- Summary classification:
  `FROZEN_AMS_DEP_V2_SYNTHETIC_HOLDOUT`.
- Summary execution commit and one-shot claim SHA both equal
  `80d0fb5a90a6c4dc02073605159c38f520ad3410`.
- Summary one-shot claim ref:
  `refs/tags/ams-dep-v2-holdout-execution-claimed-v1`.
- Execution-manifest SHA-256:
  `3d20b86f25ac5d3bdf938b4c4832269429da0495300a3c4c6d2ccaceaa073dba`.
- Frozen-spec SHA-256:
  `e1af75d54163e7fcc02edf498e44510bbe51a8b9b054bd8af8319cecd8dcdd58`.
- Freeze-manifest SHA-256:
  `a41b494c2b9c50803f01a2dc5c8f2cc8ce7bba4f0486e7774af89f8dee5aa279`.
- Summary declares:
  - main holdout gate authorized: true;
  - addendum holdout authorized: true;
  - holdout accessed: true;
  - calibration accessed: false;
  - market data accessed: false;
  - Validation/OOS accessed: false;
  - strategy P&L calculated: false;
  - empirical release authorized: false.
- The summary contains exactly 128 shard-ledger digest names, `shard_000.jsonl.gz` through `shard_127.jsonl.gz`.

The original GitHub artifact ZIP bytes were not independently rehashed in this review because the supplied Drive material consisted of the two extracted members rather than the original ZIP container. The GitHub upload log is therefore the source for the ZIP digest above. This does not affect the independent content hash and arithmetic checks on the two supplied members.

## Independent arithmetic checks

A standalone audit, without importing the production summarizer, checked:

1. Exactly 22000 unique DGP/outer coordinates:
   11 registered DGPs × outer indices 0–1999.
   No duplicates, omissions or extra coordinates were found.
2. Exactly six ordered primary slot records per outer family, totaling 132000 slot tests.
3. Every case name matches its registered DGP index and every slot order is:
   `BTC_DEP, BTC_TIME, BTC_STATE, ETH_DEP, ETH_TIME, ETH_STATE`.
4. Every available raw p-value lies on the registered 1/5000 grid.
5. All 22000 six-test Holm adjustments and reject decisions were independently recomputed. Mismatches: **0**.
6. Ledger availability flags were checked against raw-p availability. Mismatches: **0**.
7. All 219 reported count/denominator/rate/Wilson-interval metric objects were independently recomputed from the outer ledger to tolerance 1e-14. Mismatches: **0**.
8. Registered null-slot and power-slot assignments were read from the frozen V2 specification.
9. The registered point-estimate thresholds were applied independently:
   - family false-rejection rate <= 7.5%;
   - registered power >= 80%;
   - original invalidity <= 1%;
   - pooled bootstrap invalidity <= 1%;
   - explicit per-case/per-slot maximum per-outer bootstrap invalidity <= 1%.
10. All 11 cases independently pass the frozen screen.
11. The compressed outer ledger contains exactly 22000 JSONL records and its byte hash exactly matches the summary.

## Family false-rejection rates

Each row uses 2000 holdout replications and the frozen true-null subset. The registered decision rule uses the point estimate <= 7.5%; Wilson intervals are reported as diagnostics, not substituted for the frozen threshold.

| Scenario | False rejections | Rate | 95% Wilson interval |
|---|---:|---:|---:|
| iid_null | 75/2000 | 3.75% | 3.00–4.68% |
| heteroskedastic_null | 87/2000 | 4.35% | 3.54–5.33% |
| garch_null | 62/2000 | 3.10% | 2.43–3.95% |
| stable_ar | 114/2000 | 5.70% | 4.77–6.80% |
| time_ar | 94/2000 | 4.70% | 3.86–5.72% |
| state_ar | 109/2000 | 5.45% | 4.54–6.53% |
| student_t5_null | 66/2000 | 3.30% | 2.60–4.18% |
| volatility_break_null | 85/2000 | 4.25% | 3.45–5.23% |
| irregular_null | 73/2000 | 3.65% | 2.91–4.56% |
| asynchronous_null | 82/2000 | 4.10% | 3.32–5.06% |

Every point estimate is below the frozen 7.5% ceiling. Every listed marginal Wilson upper limit is also below 7.5%, though that stronger observation is not the preregistered decision rule.

## Registered power

| Registered alternative | Target slots | Rejections per slot | Holdout power |
|---|---|---:|---:|
| stable_ar | BTC_DEP, ETH_DEP | 2000/2000 each | 100% each |
| time_ar | BTC_TIME, ETH_TIME | 2000/2000 each | 100% each |
| state_ar | BTC_STATE, ETH_STATE | 2000/2000 each | 100% each |

All six registered targets exceed the frozen 80% floor. These values describe only the specified synthetic alternatives and do not imply market predictability.

## Invalidity

Across all 66 case/slot cells:

- original-fit invalidity: 0/2000 in every cell;
- pooled bootstrap invalidity rate: 0 in every cell;
- maximum per-outer bootstrap invalid fraction: 0 in every cell;
- any-original-invalid-family rate: 0 for every DGP.

The explicit maximum-invalidity rule therefore passes independently, not merely through the frozen generic summarizer.

## Bid-ask bounce diagnostic

The frozen specification assigns no null-FWER or power success criterion to `bid_ask_bounce`; it remains a measurement-effect diagnostic.

Holdout rejections:

- BTC_DEP: 2000/2000;
- BTC_TIME: 22/2000;
- BTC_STATE: 20/2000;
- ETH_DEP: 2000/2000;
- ETH_TIME: 28/2000;
- ETH_STATE: 27/2000.

Do not reinterpret these diagnostic results as a trading signal.

## What this review does not prove

The aggregate artifact does not contain the 128 underlying shard ledgers or the inner bootstrap draws. The 128 shard-ledger hashes listed in the summary cannot be independently rehashed from the two supplied aggregate members, and the 659,868,000 requested inner draws cannot be regenerated from this artifact alone.

The successful aggregate workflow did download all 128 shard artifacts and its guarded aggregator checked exact shard coverage, hashes, coordinates, execution commit, one-shot claim, dependency versions and access/provenance flags before producing the supplied aggregate artifact. This independent review validates the aggregate ledger and summary; it is not a second full numerical execution.

Access flags remain provenance declarations supported by the guarded workflow, not forensic proof of every runtime operation.

## Decision and next gate

The supplied artifact content supports **PASS of the unchanged AMS-DEP V2 reserved synthetic holdout screen**.

The one-shot claim exists and the reserved holdout opportunity is consumed. The holdout must not be dispatched, rerun, reset, or regenerated.

This review does **not** automatically authorize empirical AMS-DEP execution. Under the existing release gate, the remaining explicit blockers include:

- `full_pipeline_synthetic_integrity_passed=false`;
- `separate_empirical_release_approved=false`;
- `development_market_data_execution_authorized=false`.

Validation/OOS, strategy P&L, paper trading and live trading remain false and must remain separately gated.

The next action should be an independent review of this holdout artifact audit and a narrowly scoped post-holdout governance closeout. Only after that review should the machine gate record `v2_synthetic_holdout_passed=true` and the one-shot execution state be closed as consumed. Full-pipeline synthetic integrity remains the next scientific/engineering gate after accepted holdout PASS.
