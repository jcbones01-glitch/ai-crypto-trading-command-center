# Gate 2 Event Intelligence Foundation V1

## Purpose

Establish a deterministic, point-in-time-safe external-event data foundation for future crypto research.

This foundation follows the Cycle 7 result `NO_DEVELOPMENT_PROMOTION` for the current OHLCV-only research family. It does not authorize a new trading strategy and does not reinterpret or rescue any rejected hypothesis.

## Current scope

Foundation V1 may build:
- immutable event records;
- deterministic raw-payload hashes;
- source and source-version provenance;
- event, publication, and first-market-availability timestamps;
- point-in-time availability filters;
- tests preventing future-information leakage;
- deterministic dataset identity for event collections;
- adapters for explicitly approved public historical sources after source-specific review.

Potential future source classes include macroeconomic releases, crypto regulation, crypto-specific operational events, geopolitical events, and derivatives/market-structure data.

## Explicitly out of scope

Foundation V1 does not permit:
- Validation data access;
- locked OOS data access;
- LLM-generated trading decisions;
- autonomous research promotion;
- paper trading;
- exchange credentials;
- live execution;
- leverage;
- direct event-to-order rules;
- tuning HYP-0023, HYP-0024, HYP-0025, or any earlier rejected hypothesis.

## Point-in-time contract

Every event record must preserve, at minimum:

- `event_id`
- `event_type`
- `region`
- `assets`
- `event_time`
- `published_at`
- `first_market_available_at`
- `source_id`
- `source_version`
- `raw_event_hash`

Optional AI classification metadata must be all-or-none and versioned:

- `classification_model`
- `classification_prompt_version`
- `classification_timestamp`
- `information_cutoff`

Historical availability is governed by `first_market_available_at`, not by when the event happened and not by when a modern database later ingested or revised it.

## Leakage rules

A historical research run at time `T` may consume an event only when:

`first_market_available_at <= T`

Later revisions, corrected releases, post-event summaries, and retrospective classifications may not silently replace the information actually available at `T`.

Raw source identity and raw hashes must remain auditable.

## Development sequence

1. Define and test the event schema.
2. Define point-in-time filtering and deterministic event-dataset identity.
3. Select one source class and document its historical availability semantics.
4. Implement a deterministic source adapter with fixtures.
5. Verify revisions/vintages cannot leak future information.
6. Run descriptive event studies only.
7. Create new falsifiable hypotheses only after descriptive evidence is recorded.
8. Preregister any strategy hypothesis before treating a backtest as evidence.

## AI boundary

An Oxford-Analytica-style or TradingAgents-style analyst may be introduced only after deterministic source ingestion is trustworthy.

The AI layer may transform a point-in-time event set into structured analysis, but it may not bypass:

`FACT → EVENT → ANALYSIS → HYPOTHESIS → PREREGISTRATION → TEST → VALIDATE → RISK DECISION`

AI output is not a trading order.

## Foundation completion criteria

Foundation V1 is complete only when:
- schema and timestamp validation tests pass;
- deterministic hashing is tested;
- point-in-time filtering is tested against future leakage;
- at least one source adapter has explicit historical-availability semantics and reproducible fixtures;
- dataset identity is deterministic;
- no Validation/OOS data has been used for strategy design;
- no execution capability has been introduced.
