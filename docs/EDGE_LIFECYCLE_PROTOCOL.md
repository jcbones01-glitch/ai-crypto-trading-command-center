# Edge lifecycle and separation of authority

Status: design contract for later gates; no operational agents or connectivity are created.

## Research lifecycle

Market ecology → mechanism → hypothesis → preregistration → certified data → Development test → regime/robustness analysis → Validation → locked OOS → paper trading → controlled live trading → edge-health monitoring → maintain / reduce / suspend / retire.

Every arrow is a gate, not automatic progression. Descriptive market-state certification is not strategy approval. No candidate from the closed HYP-0001–HYP-0025 family is reopened by this lifecycle. Existing strategy-specific frozen decisions remain controlling.

## Authority contract

**Researcher ≠ Approver ≠ Risk Manager ≠ Executor.** Separate prompts or labels on the same unrestricted agent do not implement this separation. Later engineering must enforce distinct identities/capabilities, restricted data access, immutable signed decisions and an execution allowlist. Today these are design requirements, not deployed access controls.

| Role | May produce | Must not do |
| --- | --- | --- |
| Market Ecology Agent | Source reviews, certified-state observations, mechanism evidence | Infer participant identity from unlabeled proxies or approve data it proposed |
| Hypothesis Agent | Versioned falsifiable hypotheses and failure conditions | Approve its own work, inspect protected data, modify promoted rules |
| Skeptic/Falsification Agent | Confounder analysis and prospective rejection tests | Add post-result rescue filters or approve deployment |
| Experiment/Preregistration Agent | Finite registered design, exposure/search ledger | Run unfrozen evidence or silently revise decisions |
| Deterministic Research Engine | Reproducible registered calculations | Select its own hypotheses or decide capital allocation |
| Statistical Audit Agent / independent approver | Audit implementation, inference and provenance; signed release or rejection | Approve a hypothesis it proposed; place orders |
| Risk Agent | Independent exposure ceilings, veto, reduce/suspend instructions within prior authority | Override failed scientific gates or silently relax limits |
| Edge-Health Monitor | Evidence and alerts under frozen monitoring policy | Retune, reapprove, automatically resurrect or deploy |
| Execution Agent | Only signed, authorized strategy/version orders within risk limits in a later gate | Research, parameter selection, self-approval or bypass risk veto |

No self-approval is achieved merely by a proposer writing a favorable review. Where no independent reviewer/capability exists, release remains pending. No external reviewer message or invitation is implied by this document.

## State transitions

`PROPOSED → PREREGISTERED → DEVELOPMENT_TESTED → VALIDATION_ELIGIBLE → VALIDATED → OOS_PASSED → PAPER_AUTHORIZED → LIVE_AUTHORIZED`.

Failures preserve their evidence and become `REJECTED`, `SUSPENDED` or `RETIRED` as appropriate. Each authorization is scoped to the exact strategy, parameters, data/execution versions, environment, risk budget and expiry/review date. A new scope requires a new signed decision; no permanent approval exists.

The research proposer may implement a draft but an independent approver releases evidence and advancement under the established gates. Paper/live transitions require the later explicit user authorization already required by the project. A docs PR, green CI, small p-value or source probe grants none.

## Monitoring contract required before paper authorization

Preregister metrics, expected distributions, state coverage, minimum effective sample, scheduled review frequency, fixed warning/action thresholds, multiplicity/sequential-testing method, expiry, data outage behavior and decision owner. Include net return, actual fees/spreads/slippage, drawdown and recovery, tail losses, turnover, exposure, signal frequency, fill/latency discrepancies, concentration and divergence from validated assumptions. Distinguish statistical alerts from deterministic operational/risk breaches.

Repeated monitoring consumes evidence. Freeze either a finite schedule with multiplicity control or a justified sequential method and its assumptions; repeated unadjusted 5% tests are prohibited. Report detection delay, false alarms, effective sample and state mix. With no observations while suspended, lack of further losses is not recovery evidence. Favorable postdeployment outcomes cannot be reused as clean OOS for a modified strategy.

## Permitted responses

| Decision | Required basis / constraint |
| --- | --- |
| Maintain | Still within unexpired authorization, data integrity and frozen risk/health bounds |
| Reduce | Only a predefined risk-budget reduction inside existing authorization; no automatic re-expansion |
| Suspend | Stop new exposure on integrity failure, hard-risk breach, expiry or specified degradation; later exit handling must be separately defined |
| Retire | Preserve evidence and disable authorization; no hidden deletion of poor results |
| Reconsider | New version or explicitly preregistered reactivation process, independent review and required fresh evidence; never automatic revival when a chart looks favorable |

An apparent reappearance of dependence is a new research observation. It cannot resurrect rejected OHLCV hypotheses, erase adverse results, reset test counts or unlock the old protected sample for parameter rescue. No live position management is performed in the current phase.
