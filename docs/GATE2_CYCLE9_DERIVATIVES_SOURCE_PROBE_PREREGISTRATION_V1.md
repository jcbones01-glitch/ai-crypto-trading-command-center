# Gate 2 Cycle 9 — Market-Ecology Data Source Probe Preregistration V1

## Status

**FROZEN PROSPECTIVE REGISTRATION — BEFORE DERIVATIVES SOURCE PROBE**

Cycle 9 begins a data-expansion phase motivated by the Adaptive Markets framework.

It does **not** test a trading strategy. It does not reopen HYP-0001 through HYP-0025 and does not use Cycle 8 state observations to select a profitable rule.

The purpose of this first Cycle 9 subgate is narrower: verify whether the intended public derivatives sources are sufficiently reproducible and well-formed to justify building a certified market-ecology dataset.

## Motivation

The existing research program has tested many price/OHLCV-only hypotheses without a Development-to-Validation promotion.

The Adaptive Markets framework suggests that changing market ecology may matter. Funding and futures-vs-spot pricing are direct observable features of derivatives-market positioning and carrying pressure that are not contained in spot OHLCV alone.

This does not imply that these variables predict returns.

## Candidate source

Primary source:

- Binance Data Collection: `https://data.binance.vision/`
- Market: USD-M Futures (`futures/um`)
- Symbols: `BTCUSDT`, `ETHUSDT`

Candidate archive families:

1. Monthly 1-hour futures klines:
   `data/futures/um/monthly/klines/{SYMBOL}/1h/{SYMBOL}-1h-{YYYY-MM}.zip`

2. Monthly funding-rate archives:
   `data/futures/um/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{YYYY-MM}.zip`

For every accepted ZIP, the corresponding `.CHECKSUM` object is mandatory.

If an expected archive path does not exist, the probe records failure. It must not silently substitute an API response, third-party mirror, different exchange, different contract family, or different frequency.

## Probe months

The source probe is fixed to:

- `2021-01`
- `2021-06`

for both BTCUSDT and ETHUSDT and for both archive families.

Total expected source objects before checksum objects: **8 ZIP archives**.

This probe period is chosen only to verify source structure and is not a strategy sample or a parameter-selection sample.

## Required source checks

For each of the 8 registered ZIP archives:

1. archive downloads successfully;
2. matching `.CHECKSUM` downloads successfully;
3. checksum verifies exactly;
4. ZIP contains exactly one non-directory data member;
5. data member decodes as UTF-8 text;
6. header/schema is recorded exactly as supplied;
7. row count is greater than zero;
8. first and last raw rows are recorded;
9. timestamp field(s) are identified without guessing;
10. timestamps parse monotonically;
11. duplicate primary timestamps are counted;
12. timestamp unit/format is recorded;
13. malformed-row count is recorded;
14. numeric funding/price fields needed for later normalization are parseable on sampled rows.

No row may be repaired, forward-filled, interpolated, or deleted merely to make the probe pass.

## Kline-specific checks

For futures 1-hour klines:

- identify open-time and close-time columns;
- verify open times are exact UTC-hour boundaries;
- verify strictly increasing open times;
- verify OHLC values are positive;
- verify low <= open/close <= high;
- verify volume is non-negative;
- record whether timestamp precision is milliseconds or microseconds;
- record exact source column count and header.

The probe does not yet certify full historical continuity.

## Funding-specific checks

For funding-rate archives:

- record exact source column names;
- identify the funding timestamp column;
- identify the funding-rate column;
- record any supplied funding-interval field;
- verify funding timestamps are strictly increasing;
- count duplicate funding timestamps;
- verify funding-rate values parse as finite decimals;
- record observed spacing between consecutive funding timestamps;
- do not assume an 8-hour interval if the source explicitly supplies another interval.

Schema differences between registered months/symbols must be surfaced explicitly.

## Research firewall

Cycle 9 source probing is data infrastructure only.

It must not:

- access spot Validation or locked OOS for strategy evaluation;
- calculate strategy P&L;
- create buy/sell signals;
- rank funding-rate thresholds;
- test basis trades;
- test carry trades;
- condition a strategy on AMS-V1 states;
- infer profitability from funding sign or futures basis;
- authorize paper/live execution.

## Artifact requirements

The probe artifact must contain:

- executing commit SHA;
- checked-out commit SHA;
- this preregistration SHA-256;
- source URL for every archive;
- checksum URL and checksum result;
- archive SHA-256;
- internal ZIP member name;
- exact header/schema;
- raw row count;
- malformed-row count;
- duplicate-timestamp count;
- first/last parsed timestamp;
- timestamp unit/format;
- source-specific validation fields;
- per-archive pass/fail;
- overall status;
- explicit `validation_or_oos_accessed: false`;
- explicit `strategy_pnl_calculated: false`;
- explicit `strategy_signals_generated: false`.

## Completion rule

The only allowed statuses are:

- `DERIVATIVES_SOURCE_PROBE_PASS`
- `DERIVATIVES_SOURCE_PROBE_FAIL`

PASS requires all 8 registered ZIP archives and all 8 checksum objects to pass every mandatory source check.

A failure is a legitimate result and does not authorize changing months, symbols, paths, or source families after seeing the failure.

If PASS, the next permitted step is a **separate prospective full-history ingestion/certification protocol**.

If FAIL, the reason must be recorded before any alternative source is considered.

## Evidence classification

The probe produces **FACT / DATA-QUALITY OBSERVATION** only.

It produces no trading-edge evidence.

## Final status

**FROZEN REGISTRATION. THE REGISTERED SOURCE PROBE MAY NOW BE IMPLEMENTED EXACTLY AS SPECIFIED.**
