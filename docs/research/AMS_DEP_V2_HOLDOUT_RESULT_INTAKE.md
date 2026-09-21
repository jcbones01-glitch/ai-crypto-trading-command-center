# AMS-DEP V2 holdout result intake — 2026-09-21

Status: **WORKFLOW-REPORTED HOLDOUT PASS; DETAILED ARTIFACT AUDIT PENDING**.

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

## Download limitation

The connector returned a ZIP file reference, but fetching its temporary download URL returned HTTP 403. The ZIP bytes, summary.json and outer_results.jsonl.gz were not read in this review. No independently verified numerical rates, outer coverage, local ZIP integrity or full holdout audit are claimed. The supplied calibration ZIP is a different artifact and cannot substitute for the holdout ZIP.

## Remaining audit

1. Obtain the original holdout ZIP and verify bytes against the GitHub digest above.
2. Verify summary execution commit, suite, frozen spec/manifest/addendum identities, execution-bundle/claim provenance, counts and access flags against execution-commit source.
3. Verify outer-ledger digest and exact 11-DGP × 2000-outer × six-slot coverage. Independently recompute Holm decisions, false-rejection rates, registered powers, original and bootstrap invalidity, per-cell maxima and Wilson intervals where the ledger permits.
4. Retain all diagnostics and adverse findings. Do not change the frozen method or thresholds after viewing holdout outcomes.
5. Document the reviewed holdout result before any governance transition. If evidence is missing or inconsistent, preserve the blocker; no automatic rerun.
6. Full-pipeline synthetic integrity and separate empirical-release approval remain required after any accepted holdout PASS. No market-data, Validation/OOS, P&L, paper or live release follows from this workflow success.

## Governance snapshot

The main gate still records `v2_synthetic_holdout_passed=false` and `full_pipeline_synthetic_integrity_passed=false`; all empirical/trading permissions remain false. The addendum's pre-execution `reserved_holdout_seeds_consumed=false` is a historical snapshot and must not override the live durable claim. This intake leaves the gate, addendum, execution manifest and claim unchanged, preserving execution provenance. A later explicit closeout must account for actual consumption without erasing that provenance.
