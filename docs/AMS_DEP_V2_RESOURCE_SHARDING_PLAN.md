# AMS-DEP V2 resource and deterministic sharding plan

## Status

**ENGINEERING PLAN ONLY — DOES NOT RUN CALIBRATION OR HOLDOUT**

This plan addresses the conditional-review requirement for a feasible,
reproducible execution/sharding design without reducing the frozen statistical
workload.

It does not authorize V2 calibration. It does not instantiate calibration or
holdout random-number generators. It does not access BTC/ETH data.

## Verified engineering baseline

At branch commit `a0506138ee3033ad93b53b2c8a65ff4799aa9a11`:

- workflow: `AMS-DEP V2 Engineering Only`
- run: `35456463910`
- result: SUCCESS
- full suite: **178 passed**
- release-lock checks: **5 passed**
- artifact: `ams-dep-v2-engineering-only`
- artifact ID: `10588128224`
- artifact digest:
  `sha256:e054e13ed6582e5cb5048efbef108fda39ebd8cfc9122f50dfd4ea46202a79f0`

The bounded 10,000-row engineering timing remains a planning measurement, not
a calibration benchmark or statistical result.

## Fixed workload

The proposed V2 calibration has:

- 11 DGPs;
- 2,000 outer replications per DGP;
- 2 assets;
- 3 hypotheses per asset (DEP, TIME, STATE);
- 4,999 requested DWB draws per outer-slot.

Therefore:

- outer-slot tasks per suite:
  `11 * 2000 * 2 * 3 = 132,000`
- requested inner draws per suite:
  `132,000 * 4,999 = 659,868,000`
- calibration + unopened holdout requested draws:
  `1,319,736,000`

No reduction of B, DGP count, outer replications, assets, hypotheses or
release thresholds is permitted for resource reasons.

## Deterministic task coordinate order

Every outer-slot task is identified by the tuple:

`(dgp_index, outer_index, asset_index, hypothesis_index)`

with zero-based indices and canonical order:

1. DGP order exactly as committed in
   `research/experiments/ams_dep_synthetic_core_v2_proposed.json`;
2. outer replication 0..1999;
3. asset order BTC, ETH;
4. hypothesis order DEP, TIME, STATE.

Define the canonical integer task index:

`task_index = (((dgp_index * 2000) + outer_index) * 2 + asset_index) * 3 + hypothesis_index`

This definition is independent of execution order, worker count and machine.

## Fixed sharding proposal

Use **128 shards** for each suite.

Assignment:

`shard_id = task_index % 128`

This gives:

- 132,000 total slot tasks;
- 32 shards with 1,032 slot tasks;
- 96 shards with 1,031 slot tasks;
- maximum requested inner draws in one shard:
  `1,032 * 4,999 = 5,158,968`;
- minimum requested inner draws:
  `1,031 * 4,999 = 5,153,969`.

The mapping is deterministic and independent of the number of shards running
concurrently.

Calibration and holdout use the same coordinate-to-shard rule but different
already-reserved root namespaces.

## RNG invariance requirement

Sharding must never determine random numbers.

For each requested bootstrap draw, the RNG identity remains the full
prospectively committed coordinate:

`[root, 2, dgp_index, outer_index, asset_index, hypothesis_index, bootstrap_index, segment_ordinal]`

A worker receives coordinates; it does not own or advance a mutable shared RNG
stream.

Changing:
- worker count;
- shard scheduling;
- retry order;
- process order;
- host;
- concurrency

must not change the generated draw for any coordinate.

The task-planning script added with this document is forbidden from
instantiating `SeedSequence`, `PCG64`, `Generator`, or drawing any random
number. It only validates and hashes coordinate partitions.

## Retry semantics

A failed shard may be rerun in full because its tasks and each task's RNG
coordinates are deterministic.

Partial output must never be silently merged with a retry.

For each shard, a final result artifact must include:

- suite name;
- frozen-spec commit;
- shard count;
- shard ID;
- canonical task-index range/set digest;
- completed task count;
- requested draw count;
- original-fit invalid counts;
- bootstrap-invalid counts;
- per-slot exceedance totals sufficient to reconstruct p-values;
- source hashes;
- package versions;
- start/end timestamps;
- explicit `market_data_accessed: false`;
- explicit `validation_or_oos_accessed: false`.

The aggregation stage must reject:
- duplicate task indices;
- missing task indices;
- mixed spec commits;
- mixed package versions;
- mismatched shard-count definitions;
- task coordinate/digest mismatches.

## Calibration / holdout separation

The calibration suite and synthetic holdout suite are distinct research
events.

Sequence:

1. independent ratification / specification freeze;
2. authorize calibration only;
3. execute all calibration shards;
4. aggregate once;
5. apply unchanged release criteria;
6. retain pass or fail;
7. only if calibration passes unchanged, separately authorize holdout;
8. execute holdout with its reserved untouched roots;
9. apply the same required size/power/invalidity checks.

A calibration-driven code, DGP, seed, method or threshold change creates V3.
The V2 holdout cannot be used to rescue a failed or modified V2 calibration.

## Resource interpretation

The bounded engineering fixture suggests that this is a large but shardable
CPU workload.

A previous deterministic engineering extrapolation was on the order of
~600 serial CPU-hours per suite. Under ideal utilization, 128 roughly balanced
shards correspond to about one 128th of that work per shard. Actual runtime
must be measured on the intended runner before assuming a wall-clock duration.

No claim is made that:
- 128 workers are available;
- a hosted CI provider permits the required concurrency/duration;
- the workload is free;
- the engineering timing scales perfectly linearly.

Those are operational questions, not reasons to change the statistical design.

## Execution architecture

The future calibration runner should separate:

1. **planner** — validates frozen spec and emits coordinate partitions only;
2. **shard worker** — consumes one immutable task partition and produces one
   result artifact;
3. **aggregator** — verifies exactly-once coordinate coverage and computes
   registered case/slot rates and Wilson intervals;
4. **gate evaluator** — applies predeclared thresholds and records PASS/FAIL.

No worker may:
- alter spec;
- choose bandwidth;
- skip invalid draws;
- reroll seeds;
- access market data;
- access Validation/OOS;
- promote a method.

## Current authorization

This plan resolves engineering reproducibility and workload partitioning only.

The current machine gate remains blocked pending the exact independent
follow-up/freeze required by the conditional review.

**NO CALIBRATION RUN IS AUTHORIZED BY THIS DOCUMENT.**
**NO HOLDOUT RUN IS AUTHORIZED.**
**NO BTC/ETH EMPIRICAL EXECUTION IS AUTHORIZED.**
