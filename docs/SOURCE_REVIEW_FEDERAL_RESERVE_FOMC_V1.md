# Source Review — Federal Reserve FOMC Statements V1

## Decision

Approved as the first deterministic event-intelligence source class for Foundation V1.

This approval is for source ingestion and point-in-time event construction only. It does not authorize a trading hypothesis, sentiment model, LLM interpretation, Validation/OOS access, paper trading, or execution.

## Source

Federal Reserve Board historical FOMC statement pages.

Official historical statement pages reviewed across 2017, 2021, and 2026 consistently expose:
- the statement date; and
- an explicit line such as `For release at 2:00 p.m. EST` or `For release at 2:00 p.m. EDT`.

The Federal Reserve also maintains historical FOMC meeting pages linking statements and related materials.

## Historical-availability rule

For an accepted statement page:

`published_at = first_market_available_at = official "For release at" timestamp`

EST is interpreted as UTC-05:00 and EDT as UTC-04:00 exactly as stated on the source page.

The adapter does not infer a timestamp from:
- crawl time;
- file modification time;
- a modern "Last Update" field;
- the meeting date alone;
- the date portion of a URL.

If the page lacks an explicit release time and explicit EST/EDT zone, the adapter rejects it.

## Raw provenance

The exact raw payload is SHA-256 hashed.

The event ID is deterministic from:
- source identity;
- canonical source URL;
- parsed official release timestamp.

A later change to page bytes changes `raw_event_hash` and therefore changes the event-dataset identity even when the event ID remains stable.

## URL boundary

Foundation V1 accepts only HTTPS pages hosted by:
- `federalreserve.gov`
- `www.federalreserve.gov`

Redirects, mirrors, news summaries, scraped copies, and third-party calendars are not treated as authoritative source records.

## Initial research boundary

Any future Development ingestion using this source must remain inside:

`[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`

No Validation or locked OOS FOMC events may be inspected for hypothesis selection, feature selection, parameter selection, or model design.

## Known limitations

- This V1 parser covers statement pages with an explicit EST/EDT "For release at" line.
- Emergency announcements or differently formatted Federal Reserve releases require separate source review.
- The adapter records publication availability only; it does not classify policy stance, surprise, sentiment, or expected crypto impact.
- The existence of a timestamped FOMC statement does not imply a crypto trading edge.

## Next permitted step

After parser/fixture tests pass, build a Development-only manifest of FOMC statement metadata and raw-source identities. The first analysis must be descriptive event-study work, not a strategy backtest.
