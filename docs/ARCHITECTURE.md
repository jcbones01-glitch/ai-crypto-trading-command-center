# Architecture

## V0 pipeline

`Configuration -> Data Contract -> Strategy Specification -> Backtest Engine -> Metrics -> Research Provenance`

V0 is intentionally research-only. External connections and credential handling are outside scope.

## Gate 1 historical-data pipeline

`Binance Public Data -> Raw Archive -> Normalization -> Data Validation -> Dataset Identity -> Dataset Metadata -> Research-Ready Dataset`

Gate 1 is historical-data infrastructure only. It does not create trading signals, strategies, benchmarks, backtests, performance results, or execution capability.

### Source and scope

The initial source is Binance Public Data (`data.binance.vision`) for Spot BTCUSDT and ETHUSDT 1-hour klines. Internal symbols are normalized to `BTC/USDT` and `ETH/USDT`. No authentication is required.

**Data availability does not imply research suitability.** Archive existence must be followed by actual schema, financial, temporal, duplicate, ordering, and missing-interval validation.

### Raw vs normalized

Raw source rows/archives are preserved separately from the normalized `MarketBar` representation. Normalization is deterministic and does not overwrite raw source records. `MarketBar` contains only timestamp, canonical symbol, OHLC, and volume, with financial values represented by `Decimal`.

### Time convention

Binance kline timestamps are interpreted as bar-open timestamps. Gate 1 detects supported millisecond and microsecond integer timestamps rather than blindly assuming one unit, then normalizes them to timezone-aware UTC datetimes. Only exact UTC hourly boundaries are accepted.

### Validation

Gate 1 rejects malformed rows, unsupported symbols, invalid decimals, non-positive OHLC values, negative volume, invalid OHLC relationships, duplicate timestamps, out-of-order timestamps, non-hourly timestamps, and mixed timestamp precision. Missing hourly intervals are reported explicitly as data-quality events and are not filled or manufactured.

### Dataset identity and metadata

A normalized content hash is SHA-256 over canonicalized normalized rows. `dataset_id` is SHA-256 over the normalization version plus canonical normalized content. It is independent of machine, path, clock, and randomness. Metadata records source, source symbol, canonical symbol, market, timeframe, timezone, boundaries, row count, timestamp unit, normalization version, validation status, normalized content hash, and source checksum/identity when available.

### Pre-registered research partitions

- Development: `[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`
- Validation: `[2022-01-01T00:00:00Z, 2024-01-01T00:00:00Z)`
- OOS: `[2024-01-01T00:00:00Z, 2026-01-01T00:00:00Z)`

The OOS interval is metadata/protocol only in Gate 1. It is locked against strategy development, parameter selection, feature selection, hypothesis modification, and model selection.

BTC and ETH must use common research boundaries. If actual validation finds different valid starts, the common start is moved forward deterministically to the first objectively verified common valid timestamp and the reason is recorded; asset-specific windows are not selected independently.

### Storage and limitations

Large historical archives are external to Git and local data directories are ignored. Synthetic fixtures are for tests only and are never research evidence.

Binance data represents Binance market data and should not automatically be generalized to the entire crypto market. Gate 1 does not establish strategy profitability or market edge.

## Current causal backtest accounting model

Gate 2 uses a deterministic **spot** model. A target position is a fraction of portfolio equity between 0 and 1. A signal generated from bar `t` is executed at the **open** of bar `t + execution_delay_bars`; same-bar execution is prohibited. The supported research delays are one or two bars.

- Buy fills use `open * (1 + slippage_rate)`.
- Sell fills use `open * (1 - slippage_rate)`.
- Commission is proportional to gross fill value.
- Position changes change exposure; they are not themselves trade P&L.
- Realized trade P&L is recorded only for quantities sold, matched FIFO to entry lots, including allocated entry and exit fees.
- Open quantities remain unrealized and are marked to the final close.
- Equity includes cash plus marked-to-market asset value after transaction costs.

This is a research accounting model, not an exchange simulator. It does not model full order-book state, market impact, liquidity limits, partial fills, latency, or every exchange-specific fee rule. Those limitations must be addressed before any execution authorization.

## Gate 2 event-intelligence foundation

After the OHLCV-only Development family ended with `NO_DEVELOPMENT_PROMOTION`, the next research foundation broadens the information set without weakening evidence standards.

`Raw External Event -> Source Provenance -> Point-in-Time Availability -> Event Dataset Identity -> Descriptive Event Study -> New Preregistered Hypothesis`

The first foundation layer is deterministic and agent-free. Every historical event must preserve publication and first-market-availability semantics, raw payload identity, source version, and a deterministic dataset identity. A historical run may not consume an event before `first_market_available_at`.

LLM or agent analysis is a later transformation over already certified point-in-time data. It cannot convert an event directly into an authorized trade and it cannot bypass preregistration, Validation/OOS locks, risk gates, or execution controls.

## Long-term separation of responsibilities

`Certified Data -> Research/Agents -> Hypothesis -> Evidence Gates -> Model Registry -> Strategy Intent -> Risk Governor -> Execution Adapter -> Exchange`

Research components may propose. Evidence gates determine eligibility. A future risk governor may constrain approved intent. A deterministic execution adapter may eventually translate approved intent into orders. No layer is allowed to silently inherit authority from the layer above it.

## Design rule

Keep analysis, quantitative calculation, validation, risk, and later operational components separated so each can be tested independently.
