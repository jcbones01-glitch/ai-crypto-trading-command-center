# D01–D03 Data-Source Feasibility Review

**Project:** AI Crypto Trading Command Center  
**Review date:** 2026-09-20  
**Scope:** Playbook data-source feasibility register only  
**Status:** COMPLETE FOR INITIAL QUALIFICATION — NO DATASET ADOPTED INTO THE RESEARCH PIPELINE BY THIS REVIEW

## Executive decision

This review qualifies the three data sources listed in the project research playbook without authorizing a market-data experiment, changing any frozen statistical protocol, accessing Validation/OOS, or authorizing paper/live trading.

| ID | Source | Initial decision | Main unresolved issue |
|---|---|---|---|
| D01 | Federal Reserve ALFRED/FRED API | **CONDITIONALLY FEASIBLE for low-frequency point-in-time macro research** | Vintage/release dates are date-level; exact intraday availability requires source-specific release-time qualification |
| D02 | Coin Metrics Community data / `coinmetrics/data` | **FEASIBLE for bounded non-commercial research snapshots, subject to metric-level point-in-time qualification** | CC BY-NC 4.0 licensing, changing coverage, and historical revision/availability semantics |
| D03 | Coin Metrics professional Market Data | **TECHNICALLY STRONG CANDIDATE; ACCESS/COMMERCIAL FEASIBILITY UNRESOLVED** | Exact entitlement, quote/cost, licensed uses, historical venue coverage, and raw-data storage burden |

The playbook requirement remains binding for every adopted dataset: record provider, endpoint/product, retrieval time, observation time, publication/availability time, revision policy, schema, units, identifiers, coverage, license, missing-data rules, immutable snapshot hash, and cost. Historical gaps must never be filled silently.

---

## 1. Repository and scope check

Current public default-branch snapshot observed during this review:

- Repository: `jcbones01-glitch/ai-crypto-trading-command-center`
- Default branch: `main`
- Latest default-branch commit observed: `7aa2da44f19474978854905caff1ea78e05ff540`
- Commit message: `ci: register frozen AMS-DEP V2 calibration workflow on default branch`
- `adaptive-markets-research` branch exists.
- Repository code search found no existing ALFRED integration and no substantive Coin Metrics data-source integration that would make D01–D03 duplicates of an already adopted source.

This review is source qualification only. It does not modify repository authority or the AMS-DEP release gate.

---

# D01 — Federal Reserve ALFRED

## Candidate use

Economic series as they were originally released and later revised, for future macro-state or event-context research.

This is a **data-source feasibility decision**, not approval of any macro trading signal.

## What ALFRED actually provides

ALFRED (Archival Federal Reserve Economic Data) adds a **real-time period** to FRED data so historical values can be queried as they were known at a past point in history.

Relevant API capabilities include:

- `fred/series/observations`
- `realtime_start`
- `realtime_end`
- `vintage_dates`
- output type for **initial release only**
- `fred/series/vintagedates`
- release metadata and release-date endpoints

The FRED API defines `vintage_dates` as dates when values were released or revised. The real-time-period interface is date-based (`YYYY-MM-DD`).

The API documentation also warns that source release dates **do not necessarily represent when data became available on FRED/ALFRED**.

Primary documentation:

- https://fred.stlouisfed.org/docs/api/fred/alfred.html
- https://fred.stlouisfed.org/docs/api/fred/realtime_period.html
- https://fred.stlouisfed.org/docs/api/fred/series_observations.html
- https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html
- https://fred.stlouisfed.org/docs/api/fred/release_dates.html
- https://fred.stlouisfed.org/docs/api/fred/release_tables.html

## Point-in-time assessment

### Supported

ALFRED can preserve an important distinction that ordinary revised macro datasets lose:

`observation period != first-known vintage != later revised vintage`

That makes it materially better than downloading today's revised CPI, payrolls, GDP, or other macro series and pretending those values were historically known.

### Not established by ALFRED alone

For an hourly or intraday crypto strategy, a date-level vintage is not sufficient to establish that a value was usable at a specific bar.

For example, a macro observation associated with a given calendar date cannot safely be aligned to a crypto bar merely because ALFRED says the vintage date is that day.

A causal intraday implementation would additionally require, for each selected economic release:

1. originating agency;
2. official scheduled release time;
3. timezone;
4. actual release timestamp where available;
5. publication delay or ingestion lag rule;
6. handling of rescheduled, delayed, corrected, or unscheduled releases;
7. proof that the strategy cannot observe the value before the chosen availability timestamp.

The source-agency release timestamp should control when it is more precise than ALFRED's date-level vintage metadata.

## Revision policy requirement

For any future ALFRED feature, freeze one of these interpretations **before testing**:

- first-release value only;
- latest value known as of decision timestamp;
- revision size as a separately defined feature.

Do not mix first releases and revised values implicitly.

## D01 adoption gate

**Decision: CONDITIONALLY FEASIBLE.**

D01 may advance to a **series-specific qualification specification**, but not directly to strategy testing.

Minimum next artifact:

`D01_ALFRED_SERIES_QUALIFICATION_V1`

For each proposed series it must contain:

- FRED series ID;
- source agency;
- observation frequency;
- release ID;
- earliest usable vintage;
- first-release retrieval rule;
- exact source release time and timezone;
- conservative availability lag;
- revision treatment;
- missing-release treatment;
- immutable raw-response hash;
- causal join rule to crypto timestamps.

### Stop conditions

Do not adopt a series if:

- only today's revised history can be reconstructed;
- exact timing matters but only a calendar date is known;
- the release schedule or timezone is ambiguous;
- historical source definitions changed and cannot be versioned;
- missing observations would require silent forward-filling;
- the chosen feature definition is selected after observing strategy performance.

---

# D02 — Coin Metrics Community Data

## Candidate use

Network activity, supply, and related crypto-asset metrics for bounded research.

Primary sources:

- Community archive repository: https://github.com/coinmetrics/data
- Coin Metrics API v4 documentation: https://docs.coinmetrics.io/api/v4/
- Coin Metrics documentation repository/product overview: https://github.com/coinmetrics/docs-website

## What the free repository provides

The `coinmetrics/data` repository states:

- data are generated using the free Community tier;
- `csv/<coin>.csv` contains all available free metrics for an asset;
- archives are updated daily;
- layout/file-format stability is attempted but **not guaranteed**;
- available assets and metrics may change;
- the data are provided under **CC BY-NC 4.0**.

This means the GitHub repository is usable as a research source, but a future experiment must pin an exact Git commit or downloaded archive hash. Referring only to `master` is not reproducible enough.

## API-level strengths

The current API exposes reference/catalog metadata including:

- metric names;
- descriptions;
- units;
- data types;
- frequencies;
- asset coverage;
- minimum and maximum available times;
- experimental flags.

For reviewable network metrics, the time-series API can expose metric status such as `flash`, `reviewed`, or `revised`, and examples include a corresponding status timestamp.

That metadata is useful for provenance.

## Point-in-time problem

A current CSV archive containing a historical metric is **not automatically proof that the exact same value was available to a researcher on that historical date**.

Before using any network metric predictively, the project must distinguish:

1. blockchain event/observation time;
2. metric interval end;
3. Coin Metrics calculation/publication time;
4. review/revision time;
5. the value currently returned for that historical interval.

For metrics that may be retrospectively recalculated because of methodology changes, chain reorganizations, data corrections, improved parsing, or review, today's historical series could differ from the series that was available at the historical decision time.

The Community archive by itself does not establish a universal historical "as-known-at-the-time" interface equivalent to ALFRED.

Therefore point-in-time validity must be qualified **metric by metric**.

## Licensing assessment

The free GitHub archive explicitly uses **CC BY-NC 4.0**.

That is a material constraint because this project's long-run objective includes profit-oriented trading.

This review does **not** make a legal determination about whether a particular internal research activity is commercial or non-commercial. It records the license mismatch as an adoption gate.

A future production/commercial workflow must use a license that clearly permits the intended use.

## D02 adoption gate

**Decision: FEASIBLE FOR BOUNDED RESEARCH SNAPSHOTS; NOT YET QUALIFIED FOR PRODUCTION OR POINT-IN-TIME PREDICTION.**

Minimum next artifact:

`D02_COINMETRICS_COMMUNITY_METRIC_QUALIFICATION_V1`

For every candidate metric:

- metric ID;
- exact definition;
- unit;
- frequency;
- BTC/ETH availability;
- min/max time;
- experimental/reviewable status;
- calculation window;
- observation-time meaning;
- status/revision timestamp fields;
- known methodology revisions;
- historical point-in-time reconstruction method;
- Community archive commit SHA or raw-response hash;
- license;
- missing-data rule;
- permitted research use.

### Preferred first-pass rule

Do **not** bulk-ingest hundreds of metrics and search for winners.

Select a small mechanism-driven set from literature first, preregister the set, and count every tested metric in the global experiment/search ledger.

### Stop conditions

Do not adopt a metric if:

- its historical value can incorporate later information and this cannot be reconstructed;
- definition/version changes cannot be identified;
- availability timing is incompatible with the proposed prediction horizon;
- coverage is sparse or changes materially across the test period without an explicit missingness rule;
- the license does not permit the intended use;
- the metric is selected solely because it performed well in a broad retrospective screen.

---

# D03 — Coin Metrics Professional Market Data

## Candidate use

This is the most relevant data family for:

- **R02** order-flow / liquidity replication;
- **R03** cross-venue fragmentation diagnostics;
- **R04** futures/carry research;
- future execution-quality and market-microstructure studies.

Primary documentation:

- https://docs.coinmetrics.io/api/v4/

## Technically relevant capabilities

The current API documentation exposes or describes:

### Market reference data

Market identifiers can include:

- exchange;
- market type (`spot`, `future`, `option`);
- base and quote asset;
- derivative symbol;
- listing time;
- expiration time;
- contract size;
- margin asset;
- price/amount increments;
- maker/taker fees where available;
- experimental-data flag.

### Trades

`/timeseries/market-trades`

Relevant fields include market, event time, unique identifier, amount, price, side, and ingestion/database timing fields.

### Quotes

`/timeseries/market-quotes`

Top-of-book bid/ask prices and sizes are available. The documentation supports raw and downsampled quote/order-book granularity.

### Order books

`/timeseries/market-orderbooks`

The API documents raw order-book data and state-reconstruction behavior, including snapshot/update handling. For an R02-style order-flow replication, this class of data is materially closer to the needed event process than periodic candles.

### Derivatives information

Current market/catalog interfaces include support for data classes such as:

- futures markets;
- funding rates;
- open interest;
- liquidations;
- market metrics;
- contract prices;
- index/mark prices;
- derivative listing and expiration metadata.

This is potentially useful for R04, but perpetual funding and dated-futures basis remain distinct quantities.

## Coverage qualification

The API provides catalog endpoints that can return market-specific minimum and maximum times.

That means historical coverage can be tested **before purchasing/launching an experiment** if the relevant catalog information is exposed.

However, documentation showing that Coin Metrics supports a data type is not proof that:

- our exact desired market is covered for the whole required sample;
- our credentials include it;
- the required raw granularity is included;
- historical depth is sufficient;
- the data can be redistributed or processed in the intended AI workflow.

The API explicitly returns authorization errors when supplied credentials do not include a resource.

## Access and cost

The documentation distinguishes:

- Community HTTP API — free/community;
- professional HTTP API — paid;
- professional WebSocket API — paid.

No verified public fixed price for the exact institutional package required by this project was established in this review.

Therefore **cost remains UNKNOWN until a quote/order form is obtained**.

Do not insert a guessed subscription price into the project budget.

## License and AI-use gate

Paid data use is controlled by Coin Metrics' then-current Master Terms plus the applicable Order Form.

The project should not assume that a general institutional data license automatically permits:

- feeding raw vendor data into third-party AI systems;
- model training;
- redistribution;
- autonomous execution infrastructure;
- derived-data publication.

Before purchase/adoption, obtain written terms for the exact intended use.

This is especially important for an AI-assisted trading system.

## Storage/compute burden

Raw order books and high-frequency trades can be large.

The API's support for raw data establishes technical availability, **not** that the project can economically store and process a multi-year, multi-venue history.

Before purchase, perform a bounded vendor-approved sample download and record:

- bytes per market-day;
- rows/events per market-day;
- compression ratio;
- download time;
- parsing time;
- reconstructed-book memory/CPU requirements;
- expected total storage for the frozen sample.

Extrapolate only from the measured pilot.

## D03 use-specific qualification

### For R02 — order flow

Require exact confirmation of:

- BTC and/or ETH spot venue(s);
- event/update order-book history;
- snapshot initialization;
- update ordering;
- exchange/event time;
- database/collection time;
- bid/ask price and size changes;
- trade prints where needed;
- duplicate/gap semantics;
- continuous coverage for a preregistered pilot interval.

A quote-only snapshot series is not automatically equivalent to Cont/Kukanov/Stoikov event-level order-flow data.

### For R03 — fragmentation

Require:

- synchronized executable bid/ask data for every compared venue;
- venue/currency normalization;
- exact fees;
- venue-access assumptions;
- stale-quote filters;
- depth for intended size;
- inventory/transfer assumptions recorded separately from observed spreads.

### For R04 — dated carry

Require:

- dated futures, not merely perpetuals;
- exact listing and expiration metadata;
- synchronized spot and futures prices;
- contract multiplier/quote conventions;
- maturity calculation;
- constant-maturity construction rule;
- fees and roll handling;
- provenance for mark/index versus executable price.

Perpetual funding may be a separate future hypothesis, not a silent replacement.

## D03 adoption gate

**Decision: TECHNICALLY STRONG CANDIDATE; ACCESS/COMMERCIAL FEASIBILITY UNRESOLVED.**

Before any purchase or evidence-generating use, obtain:

1. exact product/SKU;
2. exact markets and fields;
3. catalog coverage export;
4. historical-depth confirmation;
5. granularity;
6. rate/download limits;
7. trial/pilot entitlement if available;
8. formal quote;
9. current license/order form;
10. written confirmation of permitted AI/internal-research use if needed;
11. measured storage/compute pilot;
12. immutable raw-data snapshot and hash design.

---

# Cross-source provenance schema

Every adopted dataset should produce a manifest at ingestion.

Minimum schema:

```yaml
dataset_id:
provider:
product:
endpoint:
source_version:
retrieved_at_utc:
raw_snapshot_sha256:

observation:
  event_time_field:
  event_timezone:
  availability_time_field:
  availability_timezone:
  minimum_causal_lag:
  publication_semantics:

revision:
  policy:
  initial_release_available:
  revisions_available:
  methodology_version:
  retrospective_recalculation_possible:

identity:
  assets:
  exchanges:
  markets:
  instruments:
  contract_expiries:

schema:
  frequency:
  units:
  columns:
  provider_metadata_fields:

coverage:
  start:
  end:
  known_gaps:
  discontinuities:

missing_data:
  policy: DROP
  imputation_authorized: false
  forward_fill_authorized: false

license:
  license_name:
  permitted_use:
  redistribution:
  ai_use:
  commercial_use:
  evidence_source:

cost:
  acquisition:
  recurring:
  storage_estimate:
  compute_estimate:

research_authority:
  authorized_partitions:
  prohibited_partitions:
  approved_experiments:
```

Unknown fields remain `UNKNOWN`; they must not be guessed.

---

# Recommended order of operations

## Phase D-A — free metadata qualification

No strategy testing.

1. D01: choose a small literature-motivated macro-series candidate list and map each to exact source-agency release timing.
2. D02: query Community catalogs for a small mechanism-driven BTC/ETH metric set; capture definitions, coverage, revisions/status metadata, license, and immutable snapshot hashes.
3. D03: use public/catalog metadata to draft the exact desired spot/futures/order-book market list and coverage requirements.

## Phase D-B — access/cost qualification

Still no strategy testing.

1. Request a Coin Metrics product/coverage quote for the exact D03 fields.
2. Confirm commercial and AI-assisted internal-research permissions in the governing terms/order form.
3. Obtain a bounded sample/trial if permitted.
4. Measure bytes/day, event counts, gaps, timestamp quality, and parser feasibility.

## Phase D-C — research preregistration

Only after a source passes qualification.

Create a new research object specifying:

- economic mechanism;
- exact fields;
- exact causal availability rule;
- frozen sample;
- baselines;
- statistical procedure;
- multiplicity family;
- robustness checks;
- rejection criteria;
- protected-data boundaries.

No dataset should be "adopted" merely because it contains many interesting variables.

---

# Final classification

**D01:** `CONDITIONALLY_FEASIBLE_LOW_FREQUENCY_POINT_IN_TIME`  
**D02:** `FEASIBLE_BOUNDED_RESEARCH_LICENSE_AND_PIT_UNRESOLVED`  
**D03:** `TECHNICALLY_FEASIBLE_ENTITLEMENT_COST_LICENSE_STORAGE_UNRESOLVED`

No new empirical edge has been established.

No dataset has been approved for Validation/OOS, paper trading, or live trading.

No repository file, workflow, release gate, frozen calibration rule, or protected result was changed or accessed by this review.
