# Market ecology: selective data expansion

Status: source-selection MODEL / proposed plan. No new dataset is certified by this document. No paid source, account, credentials or exchange execution connection is authorized.

## Priority and research value

The first return-dependence diagnostic needs only existing certified spot data and unchanged AMS-V1. Additional series must answer a stated mechanism question rather than expand feature search indiscriminately.

| Input | Mechanism / incremental value | Main certification risks | Decision |
| --- | --- | --- | --- |
| Spot OHLCV and derived realized volatility | Information incorporation and changing variance; existing diagnostic baseline | Closing trades differ from midquotes; one venue/USDT; continuity loss | Reuse certified identities; no new collection |
| Bid/ask quotes, trades, depth | Separate bounce/staleness from efficient-price dependence; measure executable liquidity | Historical reconstruction, sequence gaps, snapshots versus updates, quote age, receipt versus exchange time, licensing/storage | Highest scientific priority for microstructure attribution; first perform source/coverage review, not bulk collection |
| Perpetual funding settlements | Carry and leverage-demand pressure, not direct participant identity | Settled versus predicted rate, publication/availability time, changing settlement intervals, contract start, missing archives | Continue only the existing separately registered Cycle 9 source probe; no return joins yet |
| Perpetual/spot premium; dated futures basis | Relative valuation and arbitrage frictions | Synchronized executable versus last prices, mark/index differences, contract expiry/roll, contract multiplier | Review with funding; label perpetual premium separately from dated annualized basis |
| Open interest | Change in outstanding exposure, ambiguous long/short intent | Contract/coin/USD units, historical coverage, revised snapshots, changing multipliers | Defer ingestion until funding/basis certification and a specific mechanism justify it |
| Liquidations | Forced flow under leverage stress | Partial/censored feeds, aggregation, outages, vendor coverage changes | Defer; incompleteness could create false regime changes |
| Options implied volatility | Forward-looking priced uncertainty | Model/quote dependence, stale/zero bids, timestamp, underlying/index, expiry/delta convention | Defer pending historical quote quality, license and cost review |
| Skew and term structure | Tail insurance and horizon-specific uncertainty | Strike/expiry selection, interpolation, rolling maturities, sparse ETH history | Defer; version construction rules before any return linkage |

These priorities are design judgments, not verified claims that a vendor offers complete free history. Historical start/end, revisions, reproducible downloads, licensing and actual costs remain **UNVERIFIED** until a source review captures evidence. Do not buy data or move Development boundaries to accommodate a convenient vendor.

## Existing source work

`gate2-cycle9-market-ecology-data` at `5a0da61a4e18469dcdce10e35f69e2bf9defbf15` already freezes a Binance USD-M monthly funding and 1-hour futures-kline source probe: BTCUSDT/ETHUSDT × January/June 2021 × two archive families, eight ZIPs plus checksums. Preserve that preregistration on its branch. A probe verifies sampled objects, not full history, availability-at-decision-time, tradability or causal positioning claims. No probe result was inferred merely from the existence of this branch.

Separate event-intelligence work includes FOMC/CPI source handling and Issue #38's Employment Situation blocker. Those are event timing datasets, not direct participant-population measures. Preserve source certification and timing-manifest freeze before returns are linked. This phase does not merge or rerun that work.

## Dataset certification gate

Every additional dataset requires a versioned source-review record and independent certification comparable to Gate 1A:

1. Stated mechanism, exact fields and intended estimand; alternatives and confounders.
2. Venue, product, symbols, contract specifications, unit definitions, timezone and timestamp precision.
3. Verified first/last availability, coverage per asset, missing/duplicate/out-of-order records and structural schema changes.
4. Raw immutable payloads, observed source URLs, retrieval UTC timestamps, checksums, source/license terms, parser version and deterministic normalized identity.
5. Separate event time, publication/availability time and acquisition time; historical revisions/vintages. A recent download does not prove when a field was historically observable. Unknown availability blocks use as a predictor; a documented conservative delay is an explicit research assumption, not repaired history.
6. Expected interval/calendar/sequence rules appropriate to the instrument; objective break/exclusion policy. No silent repair, forward fill, backfill or timestamp compression.
7. Development-only acquisition allowlist and partition checks before fetch/read; no future observations or future contract universe used to initialize Development.
8. Causal as-of joins with preregistered maximum staleness and units; no nearest-future joins. Report unmatched observations. Funding settlement cannot be used before its established availability.
9. Synthetic parser, malformed input, tamper, time-unit, DST if relevant, availability and boundary tests; deterministic offline replay without network fallback.
10. Certification artifact containing source/object hashes, complete quality ledger, coverage, cost/license evidence, limitations, tests, code SHA and independent decision.

Statuses: `SOURCE_REVIEW_PENDING` → `PROBE_ELIGIBLE` → `PROBED_NOT_CERTIFIED` → `CERTIFIED_FOR_DECLARED_USE` or `REJECTED/INSUFFICIENT`. Certification for timing or descriptive analysis is not certification for forecasting or fills. Never impute prelaunch history; smaller common coverage requires its own prospective analysis and cannot silently replace the existing data identity.

No return linkage until the source choice, data transformations and research protocol are frozen. No claim that funding, volume or open interest directly measures the number or type of market participants. Ecological explanations remain hypotheses unless independently measured.
