# Decisions Log (owner decisions, append-only)

| Date | Decision | Decided by | Status |
|---|---|---|---|
| 2026-09-28 | Close PSR-01B before Validation. Its 2022+ BTCUSDT holdouts are released for new research and can no longer be treated as clean for PSR-01B. | Owner | **Decided.** See the 2026-09-28 closeout-record entry below. |
| 2026-09-28 | Adopt the owner/creator roles: the creator (Claude) proposes and builds only what the owner authorizes. | Owner | **Active.** |
| 2026-09-28 | Current phase is learning plus paper trading only. No real money, leverage or derivatives. | Owner (confirmed by situation) | **Active.** |
| 2026-09-28 | Research legitimate traders and evidence, and store it in `knowledge/`. | Owner | **Done** (this folder). |
| 2026-09-28 | Build the free paper-trading setup (Alpaca paper, monthly 10-month trend rule on SPY/EFA/IEF/VNQ/DBC). | Owner | **Built** on branch `claude/pensive-feynman-98imr1`. The owner still needs to create an Alpaca paper account, add the two GitHub secrets, and approve merging the workflow to `main`. See `07_paper_trading_setup.md`. |
| 2026-09-28 | Alpaca paper secrets added. Merge the paper-trading system directly into `main` (Option B). | Owner | **Done.** Fast-forwarded `main` to `3850397`. Next step: the first dry run. |
| 2026-09-28 | First dry run (Actions run 36376517117). | Owner | **Success.** Alpaca paper account, prices and positions read correctly. Plan: 20% each in SPY, EFA, VNQ, DBC; IEF below its 10-month average, so 20% cash. |
| 2026-09-28 | First paper submit (run 36376975006). | Owner | **4 paper orders accepted** ($20,000 each of DBC, EFA, SPY, VNQ), placed ~12:16 AM New York time, so they fill at the next market open. Fills to be confirmed in the Alpaca dashboard. |
| 2026-09-28 | Creator fix: refuse `submit` while earlier orders are still pending (prevents accidental double orders). | Owner (approved plan) | **Done.** 9 tests passing. |
| 2026-09-28 | Build a monthly report: paper account vs. just holding SPY, from 2026-09-28. | Owner | **Built.** Runs at the end of every workflow run (new `report` mode runs it alone); shown on the run's summary page. 11 tests passing. |
| 2026-09-28 | Commit the PSR-01B closeout record. | Owner | **Done.** `research/governance/psr01b_program_closeout_v1.json`, with a plain-language summary in `08_psr01b_closeout.md`. Issue #112 closed with a link. |

## Project status
| Project | State |
|---|---|
| PSR-01B (BTC XGBoost/EGARCH replication) | Development certified (Issue #110). Validation never executed. **Closed** 2026-09-28 (`research/governance/psr01b_program_closeout_v1.json`); 2022+ BTCUSDT data released for new research. |
| H-ST1 (short-horizon order-flow idea) | **Draft only** (`drafts/HST1_SPEC_DRAFT.md`). Parked until the owner decides. |
| Paper-trading learning setup | **Running, month 1** (started 2026-09-28; paper-only, monthly SPY comparison report, 11 tests passing). Next rebalance: first trading days of October (after September's monthly close). |

## Awaiting the owner's decision
1. Keep or shelve the H-ST1 draft?
