# AMS-DEP V2 holdout result intake — 2026-09-21

Status: **HOLDOUT ARTIFACT CONTENT VERIFIED; REGISTERED SYNTHETIC SCREEN PASS; GOVERNANCE TRANSITION PENDING INDEPENDENT REVIEW**.

## Verified evidence

- PR #53 merged into adaptive-markets-research at `68b0f1c69169eaf2532315a8416c2766f4331215`.
- [Run 35529411234](https://github.com/jcbones01-glitch/ai-crypto-trading-command-center/actions/runs/35529411234) executed on `ams-dep-v2-holdout-prep` at `80d0fb5a90a6c4dc02073605159c38f520ad3410`; attempt 1; completed successfully at 2026-09-21 17:36:16 UTC.
- Both job-list pages checked: 130 jobs, all successful, comprising preflight, 128 shards and aggregate.
- Aggregate job `106443566096` logs `AMS_DEP_V2_HOLDOUT_SCREEN=PASS` and `AMS_DEP_V2_HOLDOUT_PASS`.
- Its final successful screen asserts per-cell invalidity PASS, holdout accessed true, calibration/market-data/Validation-OOS access false, strategy P&L false and empirical authorization false. These are workflow assertions, not independent forensic proof.
- Durable claim `refs/tags/ams-dep-v2-holdout-execution-claimed-v1` exists and points to the execution commit. The one-shot opportunity has been consumed; do not dispatch, rerun, reset or delete the claim.
- All ten original frozen file blobs and all thirteen execution-manifest safety blobs match at both execution and reviewed integration head. Current main-gate SHA-256 matches the authorized execution manifest.
- [Results artifact 10655486394](https://github.com/jcbones01-glitch/ai-crypto-trading-command-center/actions/runs/35529411234/artifacts/10655486394): `ams-dep-v2-holdout-results`, 979668 bytes, two uploaded files according to job log.
- GitHub metadata and upload log agree on ZIP SHA-256 `0208861fc4dbeed2d6dda1a6b574678eb59957e628f1a521ba6c56227ef5435d`.

## Artifact content audit completed

The user supplied the two extracted aggregate members through connected Google Drive: `summary.json` and `outer_results.jsonl.gz`. The detailed audit is recorded in [AMS_DEP_V2_HOLDOUT_ARTIFACT_REVIEW.md](AMS_DEP_V2_HOLDOUT_ARTIFACT_REVIEW.md).

Independent checks established:

- compressed outer-ledger SHA-256 exactly matches the summary;
- exact 22000 DGP/outer records and 132000 six-slot tests;
- no duplicate, missing or extra DGP/outer coordinates;
- all raw p-values on the registered 1/5000 grid;
- all 22000 Holm families independently recomputed with zero mismatches;
- all 219 reported summary metric objects independently recomputed to tolerance 1e-14 with zero mismatches;
- all registered null-FWER, power and invalidity criteria pass;
- every per-case/per-slot maximum bootstrap invalid fraction is zero;
- execution/claim provenance matches commit `80d0fb5a90a6c4dc02073605159c38f520ad3410`.

The original GitHub ZIP container itself was not supplied to Drive, so its GitHub-reported SHA-256 remains provenance from the Actions upload log rather than an independently recalculated ZIP-container hash. The two supplied member files were independently hashed and audited.

## Remaining governance work

1. Obtain an independent review of the detailed holdout artifact audit.
2. If accepted, perform a narrowly scoped post-holdout governance closeout that records `v2_synthetic_holdout_passed=true` and closes the one-shot execution state as consumed.
3. Do not rerun, reset or delete the durable claim.
4. Do not alter the frozen V2 method, thresholds, DGPs or seeds in response to the holdout result.
5. Full-pipeline synthetic integrity, separate empirical-release approval and Development market-data authorization remain separate later gates.
6. Market data, Validation/OOS, strategy P&L, paper trading and live trading remain locked.

## Governance snapshot

The main gate still records `v2_synthetic_holdout_passed=false` and `full_pipeline_synthetic_integrity_passed=false`; all empirical/trading permissions remain false. The addendum's pre-execution `reserved_holdout_seeds_consumed=false` is a historical snapshot and must not override the live durable claim. This intake leaves the gate, addendum, execution manifest and claim unchanged, preserving execution provenance. A later explicit closeout must account for actual consumption without erasing that provenance.
