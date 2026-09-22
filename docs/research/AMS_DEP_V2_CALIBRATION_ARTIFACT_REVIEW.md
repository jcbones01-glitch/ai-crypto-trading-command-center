# AMS-DEP V2 detailed calibration artifact review — 2026-09-20

Status: **CALIBRATION ARTIFACT VERIFIED; REGISTERED SYNTHETIC SCREEN PASS**.

This completes the artifact review previously blocked by HTTP 403 in PR #52. It is an arithmetic/provenance audit of the supplied synthetic results, not a new independent design ratification, a full numerical rerun, or empirical trading evidence.

## Evidence and provenance

- Run: [35460656875](https://github.com/jcbones01-glitch/ai-crypto-trading-command-center/actions/runs/35460656875).
- Execution commit: `e348f2f2eb0ce3b5da243bea0d9bed4a2bbd4a18`.
- Reviewed PR #52 head before this documentation update: `91640aea1a13604861720f72af691cc7b915c8ff`.
- Reviewed integration branch head: `d3a2a5c6722de44e00980d36be4d307973c04fa1`.
- Artifact ID: `10609078170`; ZIP length: 980720 bytes.
- ZIP SHA-256 independently calculated: `f1cbbe421c5d5636cdac519760b521881b153050cbe6038cc67ffc3ca26b0fbe`. Matches the live GitHub artifact metadata and prior intake.
- ZIP CRC and nested gzip decompression succeeded. Exactly two members: `summary.json` and `outer_results.jsonl.gz`.
- Compressed outer ledger SHA-256: `7ba91246314f32d17226f763635306e67a2b7fa4bdacba77cc28e68621125836`; matches summary.
- Frozen specification SHA-256: `e1af75d54163e7fcc02edf498e44510bbe51a8b9b054bd8af8319cecd8dcdd58`; matches repository bytes.
- Freeze manifest SHA-256: `a41b494c2b9c50803f01a2dc5c8f2cc8ce7bba4f0486e7774af89f8dee5aa279`; matches repository bytes.
- All ten registered frozen Git blob hashes match at the execution commit, reviewed PR head and integration head.

## Independent arithmetic checks

A standalone standard-library audit, without importing the production summarizer, checked:

1. Exactly 22000 unique DGP/outer coordinates: 11 registered cases × indices 0–1999, with no duplicates, omissions or extra coordinates.
2. Six ordered slot records per outer, totaling 132000 slot records; case/index correspondence and availability consistency.
3. Raw p-value range and 1/5000 grid; Holm adjusted p-values and rejection decisions recomputed for all 22000 families.
4. All 219 reported count/denominator/rate/Wilson-interval objects recomputed from the ledger, agreeing to numerical tolerance 1e-14.
5. Original-invalid counts, family invalidity, pooled inner invalidity and each case/slot's maximum per-outer invalid fraction.
6. Null and power slot assignments and decision thresholds read from the frozen configuration; every case passes, including the separately checked maximum-invalidity criterion.
7. Summary identifies calibration, 128 shards, 132000 tasks, 22000 outer records, and all 128 expected shard-hash names. It declares holdout, market data, Validation/OOS access and empirical authorization false.

The aggregate ZIP does not contain the 128 underlying shard ledgers or bootstrap draws. Their listed hashes cannot be independently rehashed from this ZIP; raw p-values and model fits cannot be regenerated from it. This review validates the outer ledger and summary, not an independent rerun of 659868000 inner draws. Access flags are provenance declarations, supported by the guarded runner; they are not a forensic proof of every runtime operation.

## Family false-rejection rates

Each row uses 2000 replications and the frozen true-null slot subset, including partially false families in the AR cases. The registered screen uses the point estimate <= 7.5%; intervals are reported for uncertainty, not substituted as a new decision rule.

| Scenario | False rejections | Rate | 95% Wilson interval |
|---|---:|---:|---:|
| iid_null | 77/2000 | 3.85% | 3.09–4.79% |
| heteroskedastic_null | 85/2000 | 4.25% | 3.45–5.23% |
| garch_null | 85/2000 | 4.25% | 3.45–5.23% |
| stable_ar | 104/2000 | 5.20% | 4.31–6.26% |
| time_ar | 89/2000 | 4.45% | 3.63–5.44% |
| state_ar | 101/2000 | 5.05% | 4.17–6.10% |
| student_t5_null | 80/2000 | 4.00% | 3.23–4.95% |
| volatility_break_null | 77/2000 | 3.85% | 3.09–4.79% |
| irregular_null | 82/2000 | 4.10% | 3.32–5.06% |
| asynchronous_null | 85/2000 | 4.25% | 3.45–5.23% |

Every listed upper confidence limit is also below 7.5%, though that is not the registered pass criterion. Intervals are marginal Monte Carlo intervals, not simultaneous bounds over all scenarios or guarantees for real markets.

## Power and diagnostics

| Registered alternative | Target slots | Rejections per slot | Power per slot | 95% Wilson interval |
|---|---|---:|---:|---:|
| stable_ar | BTC_DEP, ETH_DEP | 2000/2000 | 100% | 99.8083–100% |
| time_ar | BTC_TIME, ETH_TIME | 2000/2000 | 100% | 99.8083–100% |
| state_ar | BTC_STATE, ETH_STATE | 2000/2000 | 100% | 99.8083–100% |

All six targets exceed the registered 80% floor. These are powers against the specified alternatives only; observed 100% does not establish population power of exactly 100% or sensitivity to smaller effects.

Bid-ask bounce has no registered true-null or power screen. DEP rejects 2000/2000 for both synthetic assets. TIME rejects 28/2000 (BTC) and 26/2000 (ETH); STATE rejects 27/2000 (BTC) and 29/2000 (ETH). Retain this as a measurement-effect diagnostic, not a trading-signal discovery.

Across all 66 case/slot cells, original invalidity is 0/2000; bootstrap invalidity is 0/9998000 requested draws per cell. Every per-outer invalid fraction is zero. The pooled draw count is an accounting quantity; bootstrap dependence means its Wilson interval should not be interpreted as an independent-draw assurance.

## Implementation caveat retained

The frozen `ams_dep_v2_aggregation.summarize` reports `per_outer_max` but does not include it in `calibration_screen_pass`; its invalidity conditions use original and pooled bootstrap rates. This review independently applies the registered per-outer/cell <=1% rule to every record. All are zero, so the omission does not change this calibration outcome. Do not silently modify the frozen implementation in response to these results. Any future execution review must check the per-cell maximum explicitly; any proposed result-affecting change must follow the existing version/freeze policy.

## Decision and next stage

The submitted aggregate artifact supports **PASS of the unchanged V2 synthetic calibration screen**. The ZIP download blocker is resolved. Recommend proceeding to preparation and separate authorization of the reserved synthetic holdout with the same scientific specification, 2000 replications per DGP, reserved holdout seed namespaces, six-slot family and unchanged thresholds.

The existing runner is explicitly calibration-only; this report is not a runnable holdout release. A separately reviewed guarded holdout execution path and explicit authorization are required before consuming any reserved seeds. Preserve the calibration freeze and evidence, verify holdout-only seed routing and complete task coverage, and include the explicit per-cell invalidity check. Apply the frozen change policy to any proposed implementation modification before execution.

The machine gate remains unchanged: calibration-passed is still false pending a separately reviewed evidence/governance transition, and holdout-authorized remains false. This report does not authorize holdout execution. No market-data outcomes, Validation/OOS, P&L or trading were accessed or authorized during this review. Full-pipeline integrity and separate empirical approval remain later gates even if holdout passes.
