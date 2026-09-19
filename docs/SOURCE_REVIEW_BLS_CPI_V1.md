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

## Accessibility audit and offline replay — 2026-09-19

Verified branch before this change: `e74444dbbd9b63af3b8677967c2ea70243611ab5`.
Main: `06b10145688cd8baca470e4bf0dc5bff8f40702d`.
Run `35424851836`, job `105848909233`: all 13 parser/scope tests passed;
initial archive-index acquisition failed with HTTP 403 before count checks.
Foundation run `35424851842` succeeded at the same commit.

Official historical calendar pages are available to the web reading service:

- https://www.bls.gov/schedule/2017/home.htm
- https://www.bls.gov/schedule/2018/home.htm
- https://www.bls.gov/schedule/2019/home.htm
- https://www.bls.gov/schedule/2020/home.htm
- https://www.bls.gov/schedule/2021/home.htm

The 2018 calendar explicitly specifies Eastern Time and CPI times of 08:30 AM.
These are useful discovery/cross-check resources. A schedule entry is not by
itself proof of actual publication or of when that schedule was first known.
No calendar-derived event is certified by this audit. A direct ordinary HTTPS
request for the 2018 calendar from this environment also returned HTTP 403.
No access-control evasion was attempted.

### Implemented reproducibility path

The manifest builder now defaults to offline replay from
`research/sources/bls_cpi_v1/inventory.json`. Each inventory response records
`url`, relative `path`, exact raw-byte `sha256`, timezone-aware `retrieved_at`,
and `acquisition_method`; the inventory version is `bls-cpi-raw-snapshot-v1`.
The bundle must preserve the official archive index and every discovered
2017–2021 CPI release HTML response. The same existing parser, 60 candidate
count, 52 Development count and boundaries remain in force. Source hashes
are checked before parsing; missing/tampered sources fail with no network
fallback. Inventory SHA-256 is included in output provenance. Explicit
`--live-audit` preserves the optional original live acquisition route.

Hashes verify byte integrity, not first-party authenticity: acquisition must
be independently reviewed before freezing/certifying a real bundle. Synthetic
fixtures and web-service-extracted text must never be labeled raw BLS HTML.
Current status: **BLOCKED_SOURCE_ACQUISITION**. No raw bundle, certified CPI
manifest, dataset ID, or CPI return results have been produced. The engineering
path is implemented; first-party source acquisition remains unresolved.

### Pre-return methodology issue

CPI at 08:30 Eastern occurs at 12:30 or 13:30 UTC, off the hourly market grid.
Do not floor to the containing hourly candle and call it a post-release return.
Before any CPI returns are viewed, preregister either a separately certified
finer-grained data method or a next-hour-open study explicitly excluding the
first 30 minutes. The latter cannot test immediate release volatility and is
not directly comparable to the FOMC release-aligned first-hour statistic.
This audit does not preregister either alternative. Source certification must
come first. Validation/OOS, paper and live trading remain locked.

## Source acquisition resolved: browser DOM representation

The official BLS index and all 60 linked 2017–2021 CPI release pages were
successfully opened in the cloud browser, without challenges, fingerprint
changes, alternate proxies, or third-party mirrors. The earlier ordinary
HTTP client failure did not apply to this browser session.

A new explicitly versioned representation is accepted for timing-only work:
`bls-cpi-dom-snapshot-v1`. The index is its rendered `main.outerHTML`; each
release is its rendered `main.innerText`, serialized to UTF-8. These are
**browser-derived representations, not original HTTP response bytes**.
Each capture records the observed official URL, retrieval time, transformation,
and hash. `raw_event_hash` in the generic event schema hashes the preserved
representation bytes; it does not claim to hash the server response. Event
`source_version` is `bls-cpi-rendered-text-v1` to make this distinction part
of dataset identity. The original raw-HTML adapter remains supported.

This representation preserves the exact visible release identity and embargo
statement needed for timing-only certification. The parser does not interpret
numeric values or prose. All 60 linked candidate pages pass the explicit
embargo parser; 52 fall within Development (4/12/12/12/12 by release year).
No source count or timestamp was inferred from crypto returns. Raw/DOM snapshot
hashes do not prove historical text vintage; previous restrictions remain.

The complete capture inventory and representations live under
`research/sources/bls_cpi_v1/`. Missing files encountered during file persistence
were reacquired from the same official URLs before completing the bundle.
The final bundle's every hash was checked before manifest generation.
