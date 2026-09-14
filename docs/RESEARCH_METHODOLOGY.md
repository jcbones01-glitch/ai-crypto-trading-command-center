# Research Methodology

## Evidence hierarchy

Keep these categories separate:

- FACT — externally verifiable information.
- OBSERVATION — a measured pattern in data.
- HYPOTHESIS — a falsifiable proposed explanation or edge.
- MODEL — formal rules used to test a hypothesis.
- BACKTEST RESULT — output from a defined historical simulation.
- LIVE RESULT — observed trading result from paper/live execution.
- OPINION — judgment that is not itself evidence.

## Research loop

`Observation → Hypothesis → Research → Strategy Specification → Backtest → Validation → Robustness → Paper Trading → Deployment`

## Gate 1 data protocol

The pre-registered V1 historical window is `[2017-08-17T00:00:00Z, 2026-01-01T00:00:00Z)`, partitioned chronologically into development `[2017-08-17, 2022-01-01)`, validation `[2022-01-01, 2024-01-01)`, and locked OOS `[2024-01-01, 2026-01-01)`.

The source is Binance Public Data Spot 1-hour BTCUSDT and ETHUSDT. The source archive remains raw; normalized rows become canonical `MarketBar` objects. Binance timestamp precision is detected as milliseconds or microseconds and normalized to UTC. Only exact hourly bar-open timestamps are accepted.

**Data availability does not imply research suitability.** A dataset is research-ready only after actual ingestion passes schema, financial, temporal, duplicate, ordering, and missing-interval validation. Missing intervals are explicit failures; no forward-filling or synthetic bars are permitted. Duplicate and out-of-order records are rejected.

The normalized dataset receives a deterministic SHA-256 content hash and a dataset ID incorporating the normalization protocol version. Metadata records the exact source identity/checksum when available, source and canonical symbols, boundaries, row count, validation status, and hashing information.

BTC and ETH remain aligned to common boundaries. If their objectively verified valid starts differ, the common start moves forward to the first verified common timestamp and the reason is recorded; the assets are not independently windowed.

The OOS partition is protocol metadata only in Gate 1. No strategy work, performance analysis, benchmark analysis, or model selection may consume OOS results in this gate.

## Required controls

Research must explicitly consider look-ahead bias, data leakage, survivorship bias, overfitting, curve fitting, unrealistic fills, transaction costs, slippage, sample size, and multiple testing.

V0 does not claim to solve every validation problem; it establishes explicit inputs and boundaries so those controls can be added without changing the research record format.

## Cost discipline

Transaction costs and slippage are explicit inputs. A profitability evaluation must not silently assume zero costs or zero slippage.

## Reproducibility

Every experiment should record its hypothesis, strategy/version, dataset identity and date range, timeframe, parameters, cost/slippage assumptions, code/version identifier, metrics, conclusion, and research decision.

## Scope boundary

Gate 1 stops at a validated historical data foundation. It does not create strategies, signals, benchmarks, backtests, performance results, trading connectivity, credentials, or execution functionality.

Binance data represents Binance market data and should not automatically be generalized to the entire crypto market.
