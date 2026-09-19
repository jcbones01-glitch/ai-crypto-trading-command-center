# Adaptive Markets phase: repository reconciliation

Classification: FACT (repository metadata) and MODEL (proposed research design).
Inspection date: 2026-09-19. This is a point-in-time record, not a moving assertion about branch heads.

## Verified starting state

| Object | Verified state | Consequence |
| --- | --- | --- |
| `main` | `06b10145688cd8baca470e4bf0dc5bff8f40702d` | PR #2 is merged; preserve the completed OHLCV program |
| PR #2 | Merged; recorded HYP-0001–HYP-0025 closure; Cycle 7 `NO_DEVELOPMENT_PROMOTION` | No failed strategy rescue and no Validation eligibility |
| `gate2-research-foundation` | `7d6002f1bbadadea1caf9fae0ef80d7e46e98295` | Existing integration base for this additive phase |
| PR #39 | Merged into research foundation | AMH framework already exists; extend it |
| PR #40 / #41 | Merged into research foundation | AMS-V1 implementation and certification already exist |
| `gate2-cycle9-market-ecology-data` | `5a0da61a4e18469dcdce10e35f69e2bf9defbf15` | Separate frozen derivatives source-probe registration; do not duplicate or change it |
| `gate2-event-intelligence-foundation` | `a1a7952ea2bc89d477bfff0eb2cf0d0f952d4eac` | Separate event-source work, not implicitly integrated here |
| Issue #38 | Open; Employment Situation first-party bundle blocker | Preserve its timing-before-returns boundary |

Branch inventory also includes `adaptive-markets-framework`, `gate1-ci-verification`, `gate2-cycle8-certification`, and `gate2-cycle8-market-state`. At inspection, PR search returned #1, #2, #39, #40, #41 and no open PR. Numerous historical Gate 2 bookkeeping issues remain open; an open issue is not authorization to reopen a rejected hypothesis. No bulk issue closure was performed.

## Evidence checked and limits

Cycle 8 workflow [35432480012](https://github.com/jcbones01-glitch/ai-crypto-trading-command-center/actions/runs/35432480012) tested commit `246d344807b2e9c88972e57e14f632e5d05c7f70`. API job steps report success. Job `105869418910` logs independently report **137 passed** and `STATE_LAYER_READY`. Artifact metadata reports ID `10580994439`, digest `sha256:a761bdcd44fd2d9e5aea47776524c2ae730cd000c6afdc09111aaaf4b39cf407`, not expired at inspection. This reconciliation checked metadata, logs, implementation, preregistration and committed certification; it is not a new independent recomputation of the archived state statistics.

The Cycle 8 certification reports 22,116 complete-state observations of 38,179 bars per asset, across 28 continuity segments. Its 57.93% complete-state coverage makes warm-up selection and sample composition material limitations. Source partitions, dataset identities and the frozen state definition remain unchanged.

The PR #2 record reports Cycle 7 workflow `35423704263`, HYP-0023/24/25 rejection and no protected-data access. This pass preserves that historical conclusion; it does not rerun all 25 hypotheses or independently recertify their economics.

Read the actual workflows before execution: legacy experiments are manual dispatch; Cycle 8 has narrowly filtered push/PR triggers. Documentation work must not trigger a new empirical study. No workflow was dispatched by this phase.

## New branch and deliverables

`adaptive-markets-research` starts at the inspected research-foundation SHA, not the older main and not the unmerged event/probe branches. A PR targets `gate2-research-foundation`, following PRs #39–#41. Integration into main remains a separate review decision.

- Extend `ADAPTIVE_MARKETS_FRAMEWORK.md`; do not replace historical protocols.
- Add `MARKET_STATE_RESEARCH_PROTOCOL.md` for diagnostic versus confirmatory evidence.
- Add `MARKET_STATE_DEPENDENCE_PREREGISTRATION_V1.md` as an explicit **draft, execution-blocked** statistical design.
- Add `MARKET_ECOLOGY_DATA_PLAN.md` with prioritized certification requirements.
- Add `EDGE_LIFECYCLE_PROTOCOL.md` with distinct authority and lifecycle controls.

No empirical dependence estimates, trading signals, strategy P&L, protected prices/returns, credentials, paper trading or live trading are produced. Reading partition dates in protocol metadata is not reading protected market observations.

## Next gate

Independent statistical review must resolve and freeze the draft's finite-sample calibration and numerical implementation contract. Then implement and test on synthetic data, record the preregistration hash and independent release decision, and only then permit one Development-only diagnostic run. Positive diagnostics cannot promote a strategy. The proposer may implement but may not sign its own release/approval.

## Verification of this documentation increment

- Local Python 3.12 environment installed the repository's declared development dependencies.
- Full existing suite: **137 passed in 1.86 seconds**. This is software regression evidence, not statistical or data certification.
- Eight changed paths are Markdown documentation only; all relative Markdown links in them resolve, and `git diff --check` passes.
- No source code, tests, workflows, historical preregistrations or certification files were changed. AMS-V1 and legacy strategy code are byte-for-byte unchanged from the integration base.
- No new GitHub empirical workflow was dispatched. Documentation paths do not match the Cycle 8 empirical trigger filter.
- Current research status: **DESIGN_DRAFT / NO_EMPIRICAL_EXECUTION**. Validation/OOS observations accessed by this increment: **NO**. No source acquisition, return dependence estimates or new trading evidence was generated.
