# Source Review — Federal Reserve FOMC Statements V1

## Decision

Approved as the first deterministic event-intelligence source class for Foundation V1.

This approval is for source ingestion and point-in-time event construction only. It does not authorize a trading hypothesis, sentiment model, LLM interpretation, Validation/OOS access, paper trading, or execution.

## Source

Federal Reserve Board press-release pages that explicitly identify themselves as:

`Federal Reserve issues FOMC statement`

Official historical statement pages reviewed across scheduled and unscheduled meetings expose:
- the statement date;
- the FOMC-statement identity; and
- an explicit line such as `For release at 2:00 p.m. EST`, `2:00 p.m. EDT`, or a different explicit release hour for an emergency statement.

The Federal Reserve's year-specific FOMC press-release indexes are the discovery authority for the source list. This avoids selecting only statements with favorable market outcomes.

## Selection rule

For the Development manifest, include **every** Federal Reserve press-release entry titled `Federal Reserve issues FOMC statement` whose official release timestamp falls within:

`[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`

This includes unscheduled/emergency FOMC statements when they appear in the official FOMC press-release index and satisfy the same parser contract.

Do not include:
- economic projections;
- implementation notes as separate events;
- longer-run-goals reaffirmations;
- discount-rate or Board-only announcements;
- minutes;
- speeches;
- press conferences;
- third-party calendars or summaries.

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

If the page lacks an explicit release time, explicit EST/EDT zone, or the required FOMC-statement identity, the adapter rejects it.

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

No Validation or locked OOS FOMC events may be inspected for hypothesis selection, feature selection, parameter selection, or model design.

## Known limitations

- This V1 parser covers official FOMC statement pages with an explicit EST/EDT `For release at` line.
- A differently formatted future or historical page requires a versioned adapter/source-review update; the parser must not guess.
- The adapter records publication availability only; it does not classify policy stance, surprise, sentiment, or expected crypto impact.
- The existence of a timestamped FOMC statement does not imply a crypto trading edge.

## Next permitted step

Build a Development-only manifest of **all** qualifying FOMC statement pages discovered from the official year indexes, preserving each source URL, official release timestamp, raw-source hash, event ID, and deterministic dataset identity. The first analysis must be a preregistered descriptive event study, not a trading strategy backtest.
