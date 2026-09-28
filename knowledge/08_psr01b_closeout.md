# PSR-01B Program Closeout (committed)

**Machine-readable record:** `research/governance/psr01b_program_closeout_v1.json` (committed 2026-09-28 with owner approval).

**Decision owner:** repository owner (jcbones01-glitch)
**Decision date:** 2026-09-28
**Decision:** Close the PSR-01B program before Validation. Release the protected BTCUSDT 2022+ intervals for new research, and record honestly that they are no longer clean holdouts.

## 1. Final state being closed
| Item | State |
|---|---|
| Development V2 | Executed once (run 36297773808). `BOUNDED_H2_REPLICATION` certified under Issue #110. Evidence commit `7ba09ce`; closeout `6148594`. |
| Development interpretation | Beat its registered baseline. **Underperformed buy-and-hold** in both arms. Not an exact paper replication. Not Validation or OOS evidence. |
| Validation V1 spec | Approved at `e6f20db` (Issue #111). |
| Validation V1 implementation | Candidate `d90f41b`. Review under Issue #112 returned `REQUIRE_CHANGES_BEFORE_PSR01B_VALIDATION_V1_REHEARSAL` (B1–B3). A freeze (`95fe970`) and a remediation commit (`17974e0`) were later pushed to the implementation branch, but the remediation was **never independently reviewed, rehearsed or executed**. (Corrected from the draft, which said "never remediated".) |
| Validation claim `refs/tags/psr01b-validation-one-shot-claim-v1` | **Never created.** |
| Protected 2022–2023 Validation and 2024+ OOS data | No Validation execution run exists in the Actions history. Push-triggered "Validation Bounded Engineering" runs are declared synthetic-offline; their data access was not re-audited for this record. |

## 2. What closing means
1. **No PSR-01B Validation result exists.** PSR-01B ends with Development-only evidence. No claim of validated, out-of-sample or tradable performance may be made for it.
2. **The holdouts are released.** From this decision on, BTCUSDT data from 2022-01-01 onward may be used by new, separately registered research.
3. **Released holdouts cannot come back.** Once any new project uses BTCUSDT 2022+ data, no future PSR-01B-family registration (renamed, successor, retry or rescue) may present those periods as untouched confirmatory Validation or OOS evidence. Any later PSR-01B-style use of them is exploratory only.
4. **The certified record stays as it is.** The Development evidence, certifications, claim tags, anchors and rulesets remain historical record. None of them is modified or deleted.
5. **Safety rulesets stay.** Keep ruleset 24086205 (Validation claim lock) and the anchor rulesets active. This prevents an accidental claim that could be misread as a real Validation run.
6. **No authorization is granted.** Closing PSR-01B authorizes no trading, leverage or derivatives.

## 3. Governance record (added)
- Set `status: PROGRAM_CLOSED_BEFORE_VALIDATION` in a new file, `research/governance/psr01b_program_closeout_v1.json`.
- Link Issues #104–#112 and set:
  - `validation_executed: false`
  - `validation_claim_created: false`
  - `protected_intervals_released: ["2022-01-01..2024-01-01", "2024-01-01.."]`
  - `released_intervals_confirmatory_reuse_by_psr01b_family: false`
- Close Issue #112 with a comment that links the closeout. Leave Issues #111 and #110 as historical record.
