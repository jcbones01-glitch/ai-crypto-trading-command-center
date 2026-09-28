# Paper-Trading Setup — Plain-Language Guide

**Fake money only.** This system can only connect to Alpaca's *paper* (practice) account. The code refuses any other address, and Alpaca's paper keys can't touch real money.

## What it does
Once a month it checks five funds:
- **SPY:** US stocks.
- **EFA:** foreign stocks.
- **IEF:** US government bonds.
- **VNQ:** real estate.
- **DBC:** commodities.

**The rule:** if a fund's latest monthly price is **above its average over the last 10 months**, hold it (20% of the account each). If it's below, keep that 20% in cash.

This is Meb Faber's well-known trend-following rule ([paper on SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=962461)). It was chosen because it is simple, public and well studied, which makes it good for learning. It is **not** a secret edge. Its main historical benefit was avoiding the worst of big crashes, and it can trail simply holding stocks during strong rising markets.

## One-time setup (about 15 minutes, no money needed)
1. **Create a free Alpaca account** at alpaca.markets using just an email. A paper account comes with $100,000 of fake money.
2. In Alpaca's **Paper Trading** dashboard, generate **API keys**. You get a *Key ID* and a *Secret Key*. Keep the secret private, and never paste it in chat.
3. In GitHub, open your repository, then go to **Settings → Secrets and variables → Actions → New repository secret** and add two secrets:
   - `ALPACA_PAPER_KEY_ID` = your Key ID
   - `ALPACA_PAPER_SECRET_KEY` = your Secret Key
4. Tell the creator (Claude) when that's done. The workflow must be on the `main` branch before GitHub shows a "Run workflow" button, and merging it there needs your approval.

## Running it each month
- **Actions → Paper Trade Monthly → Run workflow**:
  - `dry-run` shows what it *would* buy or sell. Nothing is placed.
  - `submit` places the **paper** orders.
- Start with `dry-run` to check everything works, then use `submit`.
- Run `submit` **once per month**. If earlier orders haven't filled yet (for example, you ran it at night or on a weekend), the system refuses to place new ones and the run shows red with a "blocked" message. That is a safety stop, not a crash: wait until the orders fill.
- Automatic monthly runs can be switched on later, with your approval.

## Where the code lives
| File | Role |
|---|---|
| `src/papertrade/config.py` | The five funds, the 10-month rule, and the paper-only lock |
| `src/papertrade/strategy.py` | The trend rule |
| `src/papertrade/rebalance.py` | Works out the orders; dry run by default |
| `src/papertrade/broker.py` | Talks to the Alpaca **paper** API only |
| `src/papertrade/backtest.py` | A simple history test, for learning |
| `tests/test_papertrade.py` | Safety and logic tests (9 passing) |
| `.github/workflows/paper-trade-monthly.yml` | The monthly button (manual for now) |

## Honest limits
- The Alpaca connection was **verified live on 2026-09-28**: the first dry run read the account and prices, and the first submit had 4 paper orders accepted. (The new pending-order check uses Alpaca's standard `/v2/orders?status=open` call; its first live use will be the next run.)
- Paper fills are idealized. Real trading has extra slippage.
- Monthly reports comparing results with simply holding SPY are the next thing to build, with your approval.
