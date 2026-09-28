# H-ST1 — Short-Horizon Order-Flow Imbalance (Spec DRAFT v0.1, not frozen)

> **SHELVED by the owner on 2026-09-28.** Kept for reference only. Do not build, freeze or run any part of it unless the owner reopens it (record that in `../06_decisions_log.md`).

**Status (when drafted):** DRAFT. Freeze it by committing it and recording the Git blob SHA-1 **before** any feature or model code touches data beyond what the sanity checks in §9 need.
**Scope:** research and paper trading only. **No live orders, no leverage, no real money.**

## 1. Hypothesis
When aggressive (taker) buy volume clearly outweighs taker sell volume over the last few minutes, the BTCUSDT perpetual price tends to keep moving in that direction for roughly the next 15 minutes, by more than the round-trip trading cost.

**Null hypothesis:** after realistic costs, trades triggered by order-flow imbalance earn no more than random entries with the same count, direction mix and holding time.

## 2. Instrument and data
- **Instrument:** Binance USDⓈ-M perpetual BTCUSDT. Paper trading at 1× notional, one position at a time, long or short.
- **Data:** Binance public data (data.binance.vision), futures UM:
  - `aggTrades`, used for the taker side (`is_buyer_maker`);
  - `klines_1m`;
  - `bookTicker` where available, otherwise a spread proxy (see §6);
  - `fundingRate`.
- **Integrity:** verify every monthly or daily file against its `.CHECKSUM` and record its SHA-256. Timestamps are UTC, and 1-minute bars are labelled by open time.

## 3. Periods (fixed now)
| Stage | Period | Use |
|---|---|---|
| Development walk-forward | 2023-01-01 → 2025-12-31 | Train on 3 months, test on the next 1 month, rolling monthly. This gives 33 test months. |
| Historical holdout (run once) | 2026-01-01 → 2026-08-31 | One run only, with the model and rules frozen after Development. |
| Forward paper trading | Live, 6–8 weeks after the holdout passes | The real test. |

Do **not** look at, plot or summarize any 2026 data until the Development stage finishes and its results are committed.

## 4. Features (exactly these 10; computed at minute close *t* using only data up to *t*)
1. OFI_1: (taker buy − taker sell volume) / total volume over the last 1 minute.
2. OFI_5: the same over 5 minutes.
3. OFI_15: the same over 15 minutes.
4. RET_1: log return over the last 1 minute.
5. RET_5: log return over the last 5 minutes.
6. RET_15: log return over the last 15 minutes.
7. VOL_60: standard deviation of 1-minute log returns over the last 60 minutes.
8. SPREAD: mean quoted spread in basis points over the last 5 minutes. If `bookTicker` is unavailable, use the high–low range proxy, applied the same way throughout.
9. HOUR: UTC hour, encoded as sin and cos. This counts as one feature, two columns.
10. FUND_MIN: minutes until the next funding timestamp, capped at 480.

## 5. Target and timing (look-ahead control)
- The signal is computed at the close of minute *t*.
- **Entry** is at the open of minute *t+1*. **Exit** is at the open of minute *t+16*.
- The target is `log(open[t+16] / open[t+1])`.
- The rows used for training must have targets that end before the training window closes. Drop any row whose target crosses a split boundary.

## 6. Cost model (pessimistic; verify against the real account's fee tier before freezing)
- Taker fee: **0.05% per side**.
- Spread cost: half the observed spread per side.
- Slippage: 1 extra tick plus 0.01% per side.
- Funding: charged or credited if a position is open at a funding timestamp.
- The total is expected to be about **0.12–0.15% per round trip**.

## 7. Models (exactly two, pre-registered)
- **M1: ridge regression.** Standardize features on the training window. Choose alpha from {0.1, 1, 10, 100} using the last month of each training window as an inner validation set. Then refit on the full training window.
- **M2: gradient-boosted trees** (XGBoost). Use a fixed configuration: depth 3, 300 trees, learning rate 0.05, subsample 0.8, colsample 0.8, fixed seeds. **No tuning.**
- **Seeds:** `SeedSequence([20260928, model_id, fold_index])`.

## 8. Trading rule
- Trade only when |predicted return| > **1.5 × expected round-trip cost** at time *t*.
- Go long if the prediction is positive and short if it is negative.
- Hold for exactly 15 minutes, with no overlapping positions. Signals that arrive while a position is open are ignored.
- No stop-loss, take-profit or trade sizing in version 1. Fixed notional.

## 9. Sanity checks allowed before the freeze (Development period only)
- File integrity and coverage (missing minutes).
- Feature distributions.
- **No** return or backtest calculations until the spec is frozen.

## 10. Success criteria (both models evaluated; Holm correction across the two)
A model **passes Development** only if **all** of these hold over the 33 test months:
1. At least 300 trades.
2. Total net P&L after all costs is greater than 0.
3. Net Sharpe (daily P&L, annualized with √365) is greater than 1.0.
4. It beats **random entry** (same trade count per month, same long/short mix, same 15-minute hold, 1,000 simulations) with a one-sided p ≤ 0.05 after Holm correction across M1 and M2.
5. At least 60% of test months are profitable.
6. Maximum drawdown is below 20% of notional.
7. It beats **doing nothing** (net P&L greater than 0, which is criterion 2).

**The historical holdout** (run once) must meet criteria 2, 3 and 5, plus at least 60 trades.

**Forward paper trading** (6–8 weeks) must meet at least 200 trades, net P&L greater than 0, and a realized cost per trade no worse than the assumed cost plus 25%.

## 11. Kill rules and no rescue
- If a model fails any criterion at any stage, it is **killed**.
- A failure is recorded as is. There is no re-tuning, feature change or period change on the same data.
- A new idea needs a **new spec** (H-ST2 and so on) and a new attempt-log entry.

## 12. Lightweight governance
1. Commit this spec and record its blob SHA-1 (the freeze).
2. One independent review of the spec before any backtest.
3. Keep an append-only `attempts_log.md`: date, spec hash, stage, outcome. Record every attempt, including failures.
4. One independent review of the Development results before the holdout is opened.
5. One review of the holdout before paper trading, and one after paper trading.
6. Any move to real money is a separate decision, starting small and without leverage.

## 13. Open decisions for the owner before the freeze
- [ ] Confirm the fee tier (0.05% taker assumed).
- [ ] Confirm perpetual futures (long and short) is acceptable for paper trading, or restrict to spot long/flat.
- [ ] Confirm the Development and holdout dates above.
- [ ] Choose the independent reviewer (Claude, ChatGPT, a person).
