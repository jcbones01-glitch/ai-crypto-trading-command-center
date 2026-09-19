# Gate 2 Cycle 9 — Derivatives Full-History Development Certification Protocol V1

## Status

**FROZEN PROSPECTIVE DATA-CERTIFICATION PROTOCOL — BEFORE FULL-HISTORY ACQUISITION**

This protocol follows the successful preregistered Cycle 9 source probe. It
defines the only permitted full-history acquisition/certification procedure
for the first derivatives market-ecology dataset.

It is data infrastructure only. It does not test predictability, a strategy,
funding thresholds, basis trades, AMS-V1 conditioning, P&L, or execution.

## Scientific purpose

The completed OHLCV-only Development program produced no promoted strategy.
The Adaptive Markets research direction requires observable market-ecology
variables that are economically distinct from spot OHLCV.

This certification therefore adds two source families:

1. USD-M futures 1-hour market prices/volume;
2. USD-M perpetual funding-rate observations.

These data may later support separately preregistered questions about leverage,
carrying pressure, futures-vs-spot pricing, and changing market ecology. Their
existence does not imply predictive value.

## Source contract

Official source only:

- host: `https://data.binance.vision/`
- market family: `data/futures/um/monthly`
- symbols: `BTCUSDT`, `ETHUSDT`

Registered archive patterns:

### 1-hour futures klines

`data/futures/um/monthly/klines/{SYMBOL}/1h/{SYMBOL}-1h-{YYYY-MM}.zip`

### Funding rates

`data/futures/um/monthly/fundingRate/{SYMBOL}/{SYMBOL}-fundingRate-{YYYY-MM}.zip`

Every accepted ZIP requires its matching `.CHECKSUM`. No API fallback,
third-party mirror, alternate exchange, alternate contract family, daily
archive substitution, or frequency substitution is allowed.

## Calendar scope and source-native availability discovery

The certification calendar is every UTC calendar month intersecting the
existing Development partition:

`[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`.

Therefore the deterministic monthly path scan is:

- first candidate month: `2017-08`;
- last candidate month: `2021-12`;
- 53 candidate months per symbol/source family.

There are four independent source streams:

- BTCUSDT kline;
- BTCUSDT funding;
- ETHUSDT kline;
- ETHUSDT funding.

The project must **not guess or manually enter a launch month**.

For each stream:

1. request the registered monthly ZIP path in chronological order;
2. a genuine HTTP-not-found response before the first accepted archive is
   classified `PRE_SOURCE_AVAILABILITY`;
3. the first ZIP whose ZIP and checksum objects both exist and pass checksum
   verification defines that stream's source-native first archive month;
4. after the first accepted archive, every subsequent calendar month through
   2021-12 must have both ZIP and checksum objects and pass all mandatory
   checks;
5. any missing/unverifiable month after first availability is
   `INTERIOR_COVERAGE_FAILURE` and fails that stream;
6. redirects or transient network errors are not treated as historical
   nonavailability. Retry deterministically three times; if unresolved, record
   `SOURCE_ACCESS_FAILURE` and fail rather than relabel it pre-availability.

This rule is frozen before the availability scan and prevents hindsight
selection of a convenient history start.

## Partition firewall

Only rows with timestamps strictly inside Development may enter the certified
normalized dataset.

- No archive path after `2021-12` may be requested.
- Kline open time must be < `2022-01-01T00:00:00Z`.
- Funding `calc_time` must be < `2022-01-01T00:00:00Z`.
- No Validation/OOS spot or derivatives observations may be read for this
  certification.

If a registered Development archive unexpectedly contains a row outside the
allowed partition, that row is not silently retained or clipped. The archive
is flagged and certification fails pending a separately reviewed source
explanation.

## Kline normalization and integrity contract

The successful source probe observed headerless 12-column monthly kline CSVs.
V1 therefore freezes the source column order as:

1. `open_time`
2. `open`
3. `high`
4. `low`
5. `close`
6. `volume`
7. `close_time`
8. `quote_asset_volume`
9. `number_of_trades`
10. `taker_buy_base_asset_volume`
11. `taker_buy_quote_asset_volume`
12. `ignore`

For every kline row:

- exactly 12 columns;
- open/close timestamp precision identified and preserved;
- open time exactly on a UTC-hour boundary;
- open timestamps strictly increasing within each archive;
- no duplicate open timestamps within or across accepted archives;
- OHLC strictly positive;
- `low <= open <= high` and `low <= close <= high`;
- base/quote/taker volumes non-negative;
- trade count parses as a non-negative integer;
- all required numeric fields finite;
- close time must be later than open time and before the next nominal hourly
  open;
- malformed rows are certification failures, not repair candidates.

No interpolation, forward fill, backfill, candle synthesis, outlier deletion,
or timestamp rounding is permitted.

## Funding normalization and point-in-time contract

The successful source probe observed the explicit header:

`calc_time,funding_interval_hours,last_funding_rate`.

For every accepted funding archive:

- header must identify the timestamp, interval, and funding-rate fields
  unambiguously;
- all rows must have the source header's column count;
- `calc_time` precision is preserved exactly;
- timestamps strictly increase within and across accepted archives;
- no duplicate `calc_time`;
- funding rate parses as a finite decimal;
- funding interval parses as finite and strictly positive;
- all observed interval values are recorded by month;
- all exact inter-record spacings are recorded.

**Do not round funding timestamps to 00:00/08:00/16:00.** The source probe
observed millisecond offsets from nominal funding boundaries. For future
point-in-time work, a funding observation is unavailable until its exact
certified raw `calc_time`.

No assumption that the historical interval is always 8 hours is allowed; use
the source-supplied interval field and surface any historical change.

## Cross-archive continuity and overlap checks

For each stream, after all archives are validated:

- concatenate only for certification checks, preserving archive provenance;
- require global timestamp ordering;
- require zero duplicate primary timestamps;
- report every calendar gap.

### Klines

After source-native availability begins, expected cadence is hourly. Report:

- expected hours between first and last accepted timestamps;
- observed unique hourly opens;
- missing-hour count and exact gap spans.

A missing hourly bar is not automatically repaired and causes
`CONTINUITY_FAILURE` for V1 certification.

### Funding

Do not impose an assumed fixed 8-hour cadence. Instead:

- compare adjacent `calc_time` using exact millisecond timestamps;
- compare observed spacing with the source-supplied interval applicable to the
  observation;
- permit millisecond-level boundary offsets while preserving them;
- flag any spacing incompatible with the source-supplied interval for source
  review.

## Raw provenance requirements

For every candidate month and stream, record:

- canonical ZIP URL;
- canonical checksum URL;
- availability classification;
- HTTP/source outcome;
- archive SHA-256 when downloaded;
- checksum text and verification result;
- internal ZIP member;
- exact source header/schema state;
- raw row count;
- malformed row count;
- duplicate count;
- first/last timestamp;
- timestamp precision;
- source-specific validation summary;
- pass/fail and failure reason.

The certification must retain the complete pre-availability scan record, not
only successful months.

## Deterministic normalized representation

If and only if a source stream passes all checks, produce a canonical
normalized record sequence.

### Kline canonical fields

- `symbol`
- `market = USD_M_FUTURES`
- `open_time`
- `close_time`
- `open`
- `high`
- `low`
- `close`
- `volume`
- `quote_asset_volume`
- `number_of_trades`
- `taker_buy_base_asset_volume`
- `taker_buy_quote_asset_volume`
- `source_archive_sha256`
- `source_member`

### Funding canonical fields

- `symbol`
- `market = USD_M_FUTURES`
- `calc_time`
- `funding_interval_hours`
- `last_funding_rate`
- `source_archive_sha256`
- `source_member`

Decimal source values are serialized canonically from parsed decimal values,
without binary-float reformatting. Timestamps serialize as UTC ISO-8601 with
their observed precision represented deterministically.

## Dataset identities

Create SHA-256 identities at three levels:

1. **stream source-manifest identity** — canonical metadata for every candidate
   month, including pre-availability records and every accepted archive hash;
2. **stream normalized-data identity** — canonical normalized rows in primary
   timestamp order;
3. **combined Cycle 9 derivatives identity** — canonical tuple of the four
   stream manifest/data identities plus this certification protocol SHA-256.

The identities must be stable under rerun against byte-identical source
objects and must change if source bytes, accepted records, or certification
metadata changes.

## Certification outputs

The workflow artifact must contain:

- executing commit SHA;
- checked-out commit SHA;
- protocol path and SHA-256;
- complete candidate-month source ledger;
- per-stream first source-native archive month;
- per-stream accepted archive count;
- per-stream exact first/last timestamp;
- all archive SHA-256 hashes;
- all checksum verification results;
- schema/timestamp/interval observations;
- continuity/gap reports;
- normalized row counts;
- stream manifest identities;
- stream normalized-data identities;
- combined dataset identity;
- explicit firewall fields:
  - `validation_or_oos_accessed: false`
  - `strategy_pnl_calculated: false`
  - `strategy_signals_generated: false`
  - `strategy_thresholds_searched: false`
- one final status.

## Completion status

Only these final statuses are allowed:

- `DERIVATIVES_DEVELOPMENT_DATASET_CERTIFIED`
- `DERIVATIVES_DEVELOPMENT_DATASET_CERTIFICATION_FAILED`

Certification requires all four streams to pass source availability,
checksums, schema, row integrity, Development partition, duplicate and
continuity rules.

A failure is legitimate evidence. Do not alter the calendar, symbols, source
families, integrity requirements, or source-native start rule after observing
a failure.

## What certification does not authorize

Even a PASS does **not** authorize:

- testing whether funding predicts returns;
- calculating futures basis and ranking thresholds;
- selecting high/low funding regimes;
- conditioning failed HYP-0001–HYP-0025 strategies on derivatives data;
- accessing Validation/OOS;
- paper/live trading.

After certification, any transformation such as futures basis, funding
pressure, open-interest state, or leverage-state proxy requires a separately
versioned feature specification. Any predictive/trading use requires a new
economic mechanism and prospective hypothesis registration.

## Andrew Lo / Adaptive Markets role

This dataset expansion implements the market-ecology side of the Adaptive
Markets research program: obtain observable information about changing market
structure and participant incentives before asking whether predictability
varies with those conditions.

The protocol does not assume that derivatives variables create an edge.
Null, unstable, or non-predictive findings remain valid outcomes.

## Final authorization

**THE FULL-HISTORY DEVELOPMENT DATA ACQUISITION/CERTIFICATION MAY BEGIN EXACTLY
AS SPECIFIED ABOVE. NO PREDICTIVE OR STRATEGY TEST IS AUTHORIZED.**
