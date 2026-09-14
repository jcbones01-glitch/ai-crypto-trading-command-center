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
