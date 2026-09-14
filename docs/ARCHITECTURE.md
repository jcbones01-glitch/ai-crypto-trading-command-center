# Architecture

## V0 pipeline

`Configuration -> Data Contract -> Strategy Specification -> Backtest Engine -> Metrics -> Research Provenance`

V0 is intentionally research-only. External connections and credential handling are outside scope.

## Backtest accounting model

V0 uses a deterministic close-to-close **spot** model. A target position is a fraction of portfolio equity between 0 and 1. Position changes occur at bar closes.

- Buy fills use `close * (1 + slippage_rate)`.
- Sell fills use `close * (1 - slippage_rate)`.
- Commission is proportional to gross fill value.
- Position changes change exposure; they are not themselves trade P&L.
- Realized trade P&L is recorded only for quantities sold, matched FIFO to entry lots, including allocated entry and exit fees.
- Open quantities remain unrealized and are marked to the final close.
- Equity includes cash plus marked-to-market asset value after transaction costs.

This is a research accounting model, not an exchange simulator. It does not model bid/ask spread, market impact, liquidity limits, partial fills, latency, exchange-specific fee schedules, or order-book execution. Those limitations must be addressed before any real execution research.

## Design rule

Keep analysis, quantitative calculation, validation, and later operational components separated so each can be tested independently.
