# Decisions Log (owner decisions, append-only)

| Date | Decision | Decided by | Status |
|---|---|---|---|
| 2026-09-28 | Close PSR-01B before Validation. Its 2022+ BTCUSDT holdouts are released for new research and can no longer be treated as clean for PSR-01B. | Owner | **Decided.** The formal governance record is drafted in `drafts/PSR01B_CLOSEOUT_DRAFT.md` and awaits approval to commit it as `research/governance/psr01b_program_closeout_v1.json`. |
| 2026-09-28 | Adopt the owner/creator roles: the creator (Claude) proposes and builds only what the owner authorizes. | Owner | **Active.** |
| 2026-09-28 | Current phase is learning plus paper trading only. No real money, leverage or derivatives. | Owner (confirmed by situation) | **Active.** |
| 2026-09-28 | Research legitimate traders and evidence, and store it in `knowledge/`. | Owner | **Done** (this folder). |

## Project status
| Project | State |
|---|---|
| PSR-01B (BTC XGBoost/EGARCH replication) | Development certified (Issue #110). Validation never executed; the implementation review (Issue #112) found blockers. Being **closed**. |
| H-ST1 (short-horizon order-flow idea) | **Draft only** (`drafts/HST1_SPEC_DRAFT.md`). Parked until the owner decides. |
| Paper-trading learning setup | **Proposed** (see `05_twelve_month_plan.md`). Awaiting owner approval. |

## Awaiting the owner's decision
1. Approve committing the PSR-01B closeout record?
2. Approve building the paper-trading learning setup (Alpaca paper account + one simple trend-following strategy)?
3. Keep or shelve the H-ST1 draft?
