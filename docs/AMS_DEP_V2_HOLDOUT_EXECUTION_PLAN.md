# AMS-DEP V2 reserved synthetic holdout execution plan

## Status

**PROPOSED HOLDOUT PATH — LOCKED — NO RESERVED HOLDOUT EXECUTION AUTHORIZED**

This document prepares the separately reviewed execution path required after the
verified V2 calibration PASS. It does not consume the reserved holdout seeds and
does not change the frozen scientific specification.

Calibration evidence:

- run: `35460656875`
- execution commit: `e348f2f2eb0ce3b5da243bea0d9bed4a2bbd4a18`
- aggregate artifact: `10609078170`
- verified ZIP SHA-256:
  `f1cbbe421c5d5636cdac519760b521881b153050cbe6038cc67ffc3ca26b0fbe`
- detailed review:
  `docs/research/AMS_DEP_V2_CALIBRATION_ARTIFACT_REVIEW.md`
- registered calibration screen: **PASS**

The controlling machine gate is deliberately unchanged while this path is
reviewed. Calibration PASS is evidence, not automatic authorization.

## Frozen scientific content remains unchanged

The following are not modified by this proposal:

- `research/experiments/ams_dep_synthetic_core_v2.json`
- `docs/AMS_DEP_V2_NUMERICAL_CONTRACT.md`
- `src/research_core/dependent_wild_bootstrap_v2.py`
- `src/research_core/ams_dep_v2_synthetic.py`
- `src/research_core/dependence_statistics.py`
- `research/scripts/run_ams_dep_v2_calibration_shard.py`
- `src/research_core/ams_dep_v2_aggregation.py`
- `research/scripts/aggregate_ams_dep_v2_calibration.py`
- `pyproject.toml`
- `.github/workflows/ams-dep-v2-frozen-calibration.yml`

The V2 holdout uses the same 11 DGPs, 2,000 outer replications per DGP, six-slot
Holm family, 4,999 requested inner draws, statistic/studentization,
restrictions, thresholds and invalid-draw policy. The only scientific input
change is the **already preregistered reserved holdout seed namespaces**.

## Two independent execution locks

Holdout execution requires both:

1. the existing `research/governance/ams_dep_release_gate_v1.json` to record:
   - `v2_synthetic_calibration_passed=true`;
   - `v2_holdout_execution_authorized=true`;

2. the separate
   `research/governance/ams_dep_v2_holdout_execution_addendum_v1.json` to be
   independently reviewed, hash-pinned, bound to a reviewed holdout-code commit
   that must be an ancestor of the execution commit, and explicitly changed
   from `DRAFT_LOCKED` to `AUTHORIZED`.

The addendum also requires:

- verified calibration artifact provenance;
- independent holdout-path review;
- seed-separation verification;
- artifact-integrity verification;
- duplicate-task-detection verification;
- explicit per-cell invalidity guard verification;
- reviewed holdout code commit ancestry plus exact pinned blob hashes;\n- reserved holdout namespace not previously consumed;
- market-data / Validation-OOS / P&L / paper / live permissions all false.

A PASS in the calibration report alone cannot satisfy these controls.

## Additive holdout implementation

Proposed files:

- `src/research_core/ams_dep_v2_holdout_gate.py`
- `research/scripts/run_ams_dep_v2_holdout_shard.py`
- `research/scripts/aggregate_ams_dep_v2_holdout.py`
- `tests/test_ams_dep_v2_holdout_gate.py`
- `tests/test_ams_dep_v2_holdout_runner.py`
- `tests/test_ams_dep_v2_holdout_aggregation.py`
- `.github/workflows/ams-dep-v2-holdout-preflight.yml`
- `.github/workflows/ams-dep-v2-frozen-holdout.yml`

These files are additive. They do not rewrite a frozen V2 file.

## Seed separation

The frozen V2 specification already preregistered distinct namespaces:

- bootstrap engineering: `2026092001`
- bootstrap calibration: `2026092002`
- bootstrap holdout: `2026092003`
- data calibration: `2026092102`
- data holdout: `2026092103`

Preparation tests compare these registered values and runner routing only.
They **do not instantiate an RNG with the holdout roots**.

The runner can reach `simulate_case(..., data_root=holdout)` or the holdout
bootstrap root only after both authorization locks pass.

## Task geometry

The frozen holdout workload is:

- 11 DGPs;
- 2,000 outer replications per DGP;
- 2 assets;
- 3 hypotheses;
- 132,000 outer-slot tasks;
- 128 deterministic shards;
- 32 shards with 1,032 tasks;
- 96 shards with 1,031 tasks;
- 659,868,000 requested bootstrap draws total.

Task assignment remains:

`task_index % 128 == shard_id`.

Preparation tests enumerate all 132,000 coordinates without simulating data.

## Artifact integrity

Each holdout shard records:

- compressed ledger SHA-256;
- uncompressed ledger SHA-256;
- ordered-coordinate SHA-256;
- executing commit;
- frozen manifest SHA-256;
- frozen specification SHA-256;
- holdout addendum SHA-256;
- environment versions;
- access/firewall declarations.

Aggregation rehashes the compressed and uncompressed ledgers, reconstructs the
coordinate hash, rejects duplicate task IDs, verifies exact task coordinates
and DGP identity, and requires complete 132,000-task coverage.

## Registered per-cell invalidity rule

The calibration artifact audit identified that the frozen generic summarizer
reports `per_outer_max` but does not itself include that maximum in its
`calibration_screen_pass` boolean.

The holdout wrapper does **not modify the frozen summarizer**. Instead it applies
the already registered rule explicitly after summarization:

- every case/slot `per_outer_max <= 0.01`.

The overall holdout screen requires both:

1. the unchanged frozen summary screen; and
2. the explicit per-cell maximum-invalidity screen.

This is implementation of an existing registered criterion, not a new
post-calibration threshold.

## Workflow behavior

### Preparation workflow

`.github/workflows/ams-dep-v2-holdout-preflight.yml`

May run on pull requests or manually. It performs tests and static/frozen
integrity checks only. It does not run a holdout shard.

### Execution workflow

`.github/workflows/ams-dep-v2-frozen-holdout.yml`

Manual dispatch only. It requires the exact confirmation:

`FROZEN_V2_HOLDOUT`

Before shard fan-out, it calls the dual authorization verification. With either
lock closed, the workflow stops before reserved RNG use.

No market-data loader is present.

## Result handling

If the authorized holdout later executes:

- PASS or FAIL must be retained;
- no rerolling of seeds;
- no threshold relaxation;
- no change to DGPs or family;
- no calibration-informed method change inside V2;
- no use of holdout to rescue a changed V2;
- no automatic empirical release.

A holdout PASS would still leave:

- full-pipeline synthetic integrity;
- separate empirical-release approval;
- Development market-data authorization;
- Validation/OOS;
- strategy P&L;
- paper/live trading

under later, separate gates.

## Required independent decision

Before any reserved holdout execution, an independent review should inspect the
actual branch and return exactly one:

- `AUTHORIZE_V2_SYNTHETIC_HOLDOUT_EXECUTION`
- `REQUIRE_CHANGES_BEFORE_HOLDOUT_EXECUTION`
- `REJECT_V2_HOLDOUT_EXECUTION_PATH`

Only the first decision, followed by the explicit machine-governance update and
hash/commit pinning, may open the runner.

Until then:

**NO RESERVED HOLDOUT EXECUTION.**


## Issue #54 remediation — post-review candidate

The first independent review returned
`REQUIRE_CHANGES_BEFORE_HOLDOUT_EXECUTION`. The statistical holdout design was
not rejected. Three execution/governance blockers were identified and are
remediated in the next candidate.

### 1. State-aware release tests

`tests/test_ams_dep_release_gate.py` no longer hard-codes the historical
calibration-only state as the only passing state.

It now verifies stage invariants:

- calibration authority remains valid;
- holdout authority may open only when calibration PASS is true;
- a properly authorized synthetic holdout fixture is accepted;
- Development market data, Validation/OOS, strategy P&L, paper and live trading
  remain closed;
- empirical execution remains blocked.

The holdout-specific current-state tests are likewise stage-aware. Therefore a
legitimate governance transition no longer makes the execution workflow fail
merely because it is no longer in the old locked state.

### 2. Durable one-shot execution claim

The static `reserved_holdout_seeds_consumed` field is no longer the sole
one-shot mechanism.

The execution workflow now uses the GitHub create-ref API through
`research/scripts/claim_ams_dep_v2_holdout.py` to atomically create exactly:

`refs/tags/ams-dep-v2-holdout-execution-claimed-v1`

The claim is created:

1. after explicit user confirmation;
2. after both authorization locks and the final execution bundle verify;
3. after all state-aware non-RNG safety tests pass;
4. immediately before shard fan-out.

GitHub ref creation is create-once: a second creation of the fixed ref fails.
The workflow also declares a repository-wide holdout concurrency group with
`cancel-in-progress: false` to serialize simultaneous attempts.

Tests cover:

- first claim succeeds;
- sequential second claim fails;
- two simultaneous claims yield exactly one winner;
- the claim ref cannot be changed by CLI input;
- the workflow contains concurrency control and creates the claim before the
  shard job.

The claim ref and exact claimed commit SHA are passed to every shard, recorded
in every shard summary, checked against the remote Git ref before reserved RNG
use, and rechecked by aggregation.

A shard can run only when its checkout HEAD equals the SHA stored in the durable
claim tag.

### 3. Complete authorization hash boundary

A final execution bundle is introduced:

`research/governance/ams_dep_v2_holdout_execution_manifest_v1.json`

Before execution it must be changed from `DRAFT_LOCKED` to `AUTHORIZED`
through the governance-only post-review transition.

The final manifest binds:

- the authorized main release-gate SHA-256;
- the reviewed holdout code commit;
- the fixed one-shot claim ref;
- exact Git blob hashes for all safety-critical runtime/test/workflow
  dependencies.

The required safety set explicitly includes the previously omitted:

- `src/research_core/release_gate.py`;
- `tests/test_ams_dep_release_gate.py`.

It also includes the holdout gate, execution-bundle verifier, claim script,
runner, aggregator, holdout safety tests and both holdout workflows.

The authorized addendum must store the SHA-256 of the final execution manifest.
The execution manifest intentionally does not hash the addendum, avoiding a
circular hash dependency. Instead, the create-once claim tag binds the exact
execution commit containing both the authorized addendum and the already-hashed
execution manifest.

`research/scripts/build_ams_dep_v2_holdout_execution_manifest.py` is provided
to construct the final manifest after an independent authorization decision and
after the main gate/addendum are moved to their authorized state. The builder
performs no simulation or RNG work.

### Additional defense-in-depth hardening

The remediation also strengthens two secondary findings from the first review:

- `_run_slot()` now requires an authorization context that can be produced only
  after the full authority bundle and one-shot claim verify;
- aggregation now checks shard classification, both authorization flags,
  Python/NumPy/SciPy versions, BLAS thread count, execution-manifest hash,
  one-shot claim ref/SHA, and that the common execution commit equals the
  claimed commit.

Mutable GitHub action references and the hosted runner image remain an explicit
reproducibility limitation for this candidate; the core Python/numerical
environment and scientific files remain pinned as before.

### Remediation boundary

These changes still do **not** authorize execution.

Until a new independent review returns
`AUTHORIZE_V2_SYNTHETIC_HOLDOUT_EXECUTION`, the main release gate remains
closed and the addendum remains `DRAFT_LOCKED`. The execution manifest also
remains `DRAFT_LOCKED`.

No reserved holdout RNG should be instantiated during remediation or review.
