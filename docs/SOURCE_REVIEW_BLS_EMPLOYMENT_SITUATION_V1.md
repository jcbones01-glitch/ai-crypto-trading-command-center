# Source Review — BLS Employment Situation Releases V1

## Decision

Approved as the third deterministic macro-event source class for Event Intelligence Foundation V1, **timing-only**.

This approval covers release identity and official embargo timing. It does not authorize payroll/unemployment value extraction, forecast surprise, revision analysis, NLP/LLM classification, a trading hypothesis, Validation/OOS access, paper trading, or execution.

## Official source

U.S. Bureau of Labor Statistics Employment Situation archived news releases.

Discovery authority:

`https://www.bls.gov/bls/news-release/empsit.htm`

The official archive exposes monthly Employment Situation HTML pages. Historical release pages identify themselves as `Employment Situation News Release` and state an explicit embargo-until timestamp. Reviewed examples include:

- 2017-10-06: `8:30 a.m. (EDT) Friday, October 6, 2017`
- 2020-01-10: `8:30 a.m. (EST) Friday, January 10, 2020`
- 2021-01-08: `8:30 a.m. (ET) Friday, January 8, 2021`

## Point-in-time rule

For an accepted release:

`published_at = first_market_available_at = official embargo-until timestamp`

Supported timezone markers:
- `EST` = UTC-05:00
- `EDT` = UTC-04:00
- `ET` = historical America/New_York offset for the release date

The release timestamp must come from the release body. It is not inferred from the archive filename, crawl time, schedule date, or a modern last-updated field.

## Discovery rule

Only official BLS HTML archive links whose path matches:

`/news.release/archives/empsit_YYYYMMDD.htm`

and whose link label identifies an Employment Situation release are eligible.

PDFs, current aliases, Employment Situation of Veterans, CPI releases, third-party calendars, mirrors, and search snippets are excluded from deterministic V1 discovery.

## Planned Development selection rule

Before any crypto returns are examined, the candidate-count rules are frozen as:

- 60 monthly Employment Situation releases across calendar years 2017–2021;
- 52 release events whose certified embargo timestamp falls in the existing Development window `[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`;
- expected Development yearly counts: 2017 = 4, 2018 = 12, 2019 = 12, 2020 = 12, 2021 = 12.

These counts derive from the monthly official archive structure and the pre-existing Development boundary. If reviewed source acquisition disagrees, the mismatch must be diagnosed before any count is changed.

## Historical-vintage limitation

BLS archive pages can be reissued or corrected after original publication. A reviewed 2020 Employment Situation page explicitly notes a later reissue correcting a table.

Therefore V1 may certify:
- release identity;
- official embargo timestamp;
- canonical official URL;
- hash of the preserved acquisition representation.

It does **not** certify that current archived numeric values or prose are byte-for-byte identical to the original release-time representation.

No payroll number, unemployment rate, revision, forecast surprise, sentiment, or LLM-derived feature is permitted without a separate historical-vintage review.

## GitHub Actions accessibility

The CPI source work established that ordinary GitHub-hosted HTTP requests to BLS may receive HTTP 403 while an interactive/cloud browser can view the same official pages.

Employment Situation V1 must not bypass BLS access controls and must not substitute third-party mirrors.

The reproducible acquisition design should mirror CPI:
1. acquire the official archive index and all 2017–2021 candidate pages through an allowed first-party browser session;
2. preserve an explicitly versioned representation and retrieval provenance;
3. hash every preserved representation;
4. replay offline in GitHub Actions with no automatic network fallback;
5. independently verify 60 candidate pages and 52 Development events before certifying the manifest.

Until that first-party source bundle exists and passes replay, status is:

`BLOCKED_SOURCE_ACQUISITION`

## Hourly-grid limitation

Employment Situation releases are at 08:30 Eastern, therefore xx:30 UTC relative to the hourly Binance bar grid.

Do not floor to the containing hourly candle and describe the result as post-release.

Any later hourly study must be separately preregistered and, unless finer-frequency data is certified first, should use the next full UTC hour as an explicit delayed anchor, excluding the first 30 minutes.

## Current authority

No crypto-return analysis has been performed for this event class.

No strategy promotion, Validation/OOS access, paper trading, live trading, leverage, or exchange credentials are authorized.
