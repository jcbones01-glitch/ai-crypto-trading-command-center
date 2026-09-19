# Source Review — BLS Consumer Price Index Releases V1

## Decision

Approved as the second deterministic macro-event source class for Event Intelligence Foundation V1.

This approval covers official release identity and point-in-time publication semantics only. It does not authorize CPI-value extraction, surprise calculations, text sentiment, an LLM classification, a trading hypothesis, Validation/OOS access, paper trading, or execution.

## Source

U.S. Bureau of Labor Statistics Consumer Price Index archived news releases.

Discovery authority:

`https://www.bls.gov/bls/news-release/cpi.htm`

The official archive provides historical CPI releases by year. Release pages identify themselves as `Consumer Price Index News Release` and state an explicit embargo-until timestamp.

## Point-in-time rule

For an accepted archived CPI release:

`published_at = first_market_available_at = official embargo-until timestamp`

The adapter accepts timezone markers:
- `EST` as UTC-05:00;
- `EDT` as UTC-04:00;
- `ET` using the historical U.S. Eastern offset for the release date via `America/New_York`.

The timestamp is not inferred from the archive filename, crawl time, revision date, or a current webpage timestamp.

## Discovery rule

Only official BLS HTML archive links whose path matches:

`/news.release/archives/cpi_YYYYMMDD.htm`

and whose link label identifies a Consumer Price Index release are eligible.

PDF links, current-release aliases, non-CPI BLS releases, third-party calendars, and mirrored pages are excluded from V1 discovery.

## Development selection rule

From the complete official CPI archive discovery, include every event whose certified embargo timestamp falls inside:

`[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`

The expected Development count is frozen at **52** before linking CPI events to crypto returns:

- September–December 2017 releases: 4;
- 2018: 12;
- 2019: 12;
- 2020: 12;
- 2021: 12.

If deterministic discovery/parser output does not equal 52, the manifest workflow must fail and the mismatch must be diagnosed rather than changing the expected count to fit observed output.

## Raw provenance and revisions

The exact retrieved archive page bytes are SHA-256 hashed.

The BLS archive explicitly warns that data in archived releases may have been revised in subsequent releases. Some individual archived releases also state that the page was later reissued to correct tables.

Accordingly, a present-day archived page hash makes the **current archive representation** auditable, but does not prove that every byte or numeric value matches what market participants saw at the historical release instant.

Foundation V1 therefore certifies:
- release identity;
- official embargo timestamp;
- canonical archive URL;
- raw archive-page hash as retrieved.

It does **not** certify historical text/numeric vintage for:
- actual-vs-forecast surprise;
- inflation value extraction;
- sentiment;
- LLM interpretation;
- hawkish/dovish categorization.

Those require a separate versioned vintage review.

## Event identity

The deterministic event ID is SHA-256 over:
- source identity;
- canonical source URL;
- certified embargo timestamp.

If BLS later changes archived bytes without changing the original release identity, the event ID stays stable while `raw_event_hash` and downstream dataset identity change.

## URL boundary

Only HTTPS pages hosted by:
- `bls.gov`
- `www.bls.gov`

are authoritative for this adapter.

## Next permitted step

After adapter tests pass, build and certify a Development-only CPI event manifest from the complete official archive index. Do not calculate crypto returns until that event set is frozen.
