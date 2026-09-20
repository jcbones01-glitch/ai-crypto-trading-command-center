# AMS-DEP V2 calibration result intake — 2026-09-20

Status at initial intake: **WORKFLOW-REPORTED PASS; DETAILED ARTIFACT REVIEW PENDING**.

Update: the supplied ZIP now matches GitHub’s digest and its outer ledger and numerical summaries have been checked. See the [completed detailed artifact review](AMS_DEP_V2_CALIBRATION_ARTIFACT_REVIEW.md). The historical intake below is retained; its download blocker and pending numerical checks are superseded by that review. Holdout remains unauthorized.

## Verified evidence

- [Run 35460656875](https://github.com/jcbones01-glitch/ai-crypto-trading-command-center/actions/runs/35460656875) completed successfully at 2026-09-20 16:37:55 UTC.
- Execution commit: `e348f2f2eb0ce3b5da243bea0d9bed4a2bbd4a18`.
- [Aggregate job 106111009278](https://github.com/jcbones01-glitch/ai-crypto-trading-command-center/actions/runs/35460656875/job/106111009278) logged 128 downloaded artifacts, `AMS_DEP_V2_CALIBRATION_SCREEN=PASS`, and `AMS_DEP_V2_CALIBRATION_PASS`.
- Its final screen asserted that holdout, market data and Validation/OOS were not accessed and empirical release was not authorized.
- Aggregate artifact: `ams-dep-v2-calibration-results`, ID `10609078170`, 980720 bytes.
- GitHub-reported ZIP SHA-256: `f1cbbe421c5d5636cdac519760b521881b153050cbe6038cc67ffc3ca26b0fbe`.
- All ten frozen file blob hashes matched the freeze manifest at both the execution commit and inspected current head `d3a2a5c6722de44e00980d36be4d307973c04fa1`.

The downloaded ZIP bytes were not independently hashed. The artifact service returned a file reference, but fetching its download URL from the review environment returned HTTP 403 (error 1010). No artifact content was inspected. The reported digest above is provenance metadata, not a completed local integrity check.

## Frozen decision rules inspected

The frozen configuration specifies 11 DGPs, 2000 outer replications each, six slots, 4999 requested bootstrap draws per available task, false-rejection ceiling 0.075, registered target-power floor 0.80, and invalidity ceiling 0.01. Bid-ask bounce is a measurement-effect diagnostic without a null/power pass criterion.

The aggregation script checks 128 shard ledgers and summaries, frozen-spec/manifest provenance, a single execution commit, unique task coordinates and exact expected task coverage before summarization. The expected totals are 132000 slot tasks and 22000 outer-result records. These totals follow from the frozen configuration; they have not yet been read from this run's summary artifact.

## Remaining review before holdout decision

1. Obtain the original ZIP and verify its bytes against the reported SHA-256.
2. Read summary.json; verify execution commit, frozen spec/manifest hashes, task and outer counts, shard count, suite and access flags.
3. Inspect each DGP's false-rejection rate and Wilson interval, each registered power target, original invalidity, pooled bootstrap invalidity and per-outer maximum invalidity.
4. Verify outer_results.jsonl.gz against the summary digest, exact DGP/outer coverage and six-slot records. Independently recompute summary quantities from that ledger where possible.
5. Retain all adverse findings, diagnostic-only results and finite-simulation uncertainty.
6. Only then document a holdout recommendation and request the separately required execution authorization.

No detailed numerical rates, independent reproduction, artifact integrity PASS, or holdout readiness are claimed by this intake.

## Authority

The live gate read at the inspected head still records calibration-passed false and holdout-authorized false. A workflow pass does not automatically mutate that gate. This documentation does not update the gate or open the reserved holdout. No empirical research or trading authorization is created.
