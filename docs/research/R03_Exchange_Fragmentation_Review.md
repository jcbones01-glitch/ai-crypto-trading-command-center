# R03 — Exchange Fragmentation Review and Bounded Diagnostic Proposal

**Completed:** 2026-09-20  
**Project:** AI Crypto Trading Command Center  
**Scope:** literature applicability, cross-venue synchronization, currency normalization, execution constraints, data-source feasibility, and a bounded descriptive diagnostic proposal.  
**Authorization:** research/design only. No market-data experiment, Validation/OOS access, strategy P&L calculation, paper trading, live trading, release-gate change, AMS-DEP change, or repository mutation was performed.

## Decision memo

**R03 is complete as a market-fragmentation literature/applicability review and diagnostic design.**

Makarov & Schoar (2020) provides strong historical evidence that cryptocurrency markets can be materially segmented across venues and countries. In their 2017–2018 sample, cross-country Bitcoin price deviations were substantially larger and more persistent than within-country deviations, while crypto-to-crypto relative-price deviations were much smaller. Their evidence is consistent with limits to cross-border arbitrage capital, especially where fiat movement, market access, or capital controls constrain recycling.

For this project, the important lesson is **not** “trade every cross-exchange price difference.” It is the opposite: a price difference is not an executable arbitrage until simultaneity, account/venue access, quote freshness, bid/ask direction, depth, fees, currency conversion, inventory location, transfer/recycling constraints, and settlement timing are all demonstrated.

Makarov & Schoar explicitly try to reduce the stale-price problem in their historical arbitrage calculation by using transaction-level data and matching executable-direction trades at the second level rather than comparing arbitrary last prices. They also show why apparent textbook arbitrage can remain difficult: Bitcoin transfers took time, fiat transfers could take hours or days, shorting was unavailable on important premium venues in their sample, and pre-positioned inventory was needed for near-simultaneous buy-low/sell-high execution.

**Project decision:**

- Exchange fragmentation as a material confound for crypto research: **SUPPORTED.**
- Treating a cross-venue last-price difference as arbitrage: **UNSUPPORTED.**
- Same-currency, synchronized bid/ask dispersion as a descriptive diagnostic: **SUPPORTED IN PRINCIPLE.**
- Interpreting USD and USDT as identical without explicit conversion/basis treatment: **UNSUPPORTED.**
- Assuming historical 2017–2018 exchange fees, transfer times, venue access, or capital-control rules still apply today: **UNSUPPORTED.**
- A bounded current cross-venue diagnostic using point-in-time quotes/order books: **CONDITIONALLY FEASIBLE**, subject to data entitlement, venue/account accessibility, point-in-time fee schedules, and timing-quality checks.
- Arbitrage strategy P&L, paper trading, live execution, or automated capital movement: **NOT AUTHORIZED.**

## 1. Repository reconciliation and current authority

Repository checked through the connected GitHub account before completing R03:

- Repository: `jcbones01-glitch/ai-crypto-trading-command-center`
- Default branch: `main`
- Research branch used by PR #42: `adaptive-markets-research`
- PR #42: open draft; base `gate2-research-foundation`; head `adaptive-markets-research`
- PR #42 head observed during this review: `6431e9995ed3c904b673603b662506692d370539`
- Default-branch recent commit observed: `7aa2da44f19474978854905caff1ea78e05ff540`

Repository searches for `Makarov Schoar` and `exchange fragmentation` returned no direct implementation or literature module in the default-branch search scope. The PR #42 diff also contained no Makarov/Schoar reference and no exchange-fragmentation module. Generic references to statistical arbitrage and relative-value features are not equivalent to the R03 source or diagnostic proposed here.

The project's existing firewalls remain binding. R03 is a literature/design deliverable only and does not supersede the separate AMS-DEP synthetic-calibration authority, protected-sample locks, or trading prohibition.

## 2. Primary source and source-version note

### Published source

Igor Makarov and Antoinette Schoar, **“Trading and Arbitrage in Cryptocurrency Markets,”** *Journal of Financial Economics* 135(2), 293–319 (2020). DOI: `10.1016/j.jfineco.2019.07.001`.

Publication identity and final abstract were verified through the Journal of Financial Economics / ScienceDirect record and MIT Sloan. Detailed methodological extraction was performed from the openly accessible author-final/working-paper lineage (LSE Discussion Paper No. 782 / SSRN manuscript). The MIT repository identifies its open version as the author's final manuscript after peer review. Exact page pagination may differ from the publisher-formatted version; section references below are therefore the primary locators.

### Closely related corroborating source

Makarov & Schoar, **“Price Discovery in Cryptocurrency Markets,”** *AEA Papers and Proceedings* 109, 97–99 (2019), DOI `10.1257/pandp.20191020`.

This short follow-up reports that when crypto markets are more segmented, exchanges with large arbitrage spreads relative to the U.S. price become less important for global price discovery. That reinforces the project implication that an extreme local price should not automatically be treated as the best global reference price.

## 3. What Makarov & Schoar actually studied

### 3.1 Sample period, assets, exchanges, and sources

The detailed manuscript reports a principal sample covering **January 1, 2017 through February 28, 2018**, focused on the most liquid cryptocurrencies in that period: **Bitcoin (BTC), Ethereum (ETH), and Ripple/XRP**.

The principal Kaiko transaction dataset covered 17 large/liquid exchanges:

`Binance, Bitfinex, bitFlyer, Bithumb, Bitstamp, Bitbox, Bittrex, BTCC, BTC-e, Coinbase, Gemini, Huobi, Kraken, OkCoin, Poloniex, Quoine, Zaif`.

Additional exchange data from Bitcoincharts and direct exchange sources expanded the geographic analysis to **34 exchanges across 19 countries**. The data included transaction timestamps, prices and quantities, and, where available, trade-direction indicators. Kaiko also supplied minute-level order-book snapshots used for bid/ask-spread analysis.

### 3.2 Geographic/currency structure

The authors explicitly treated cryptocurrency trading as segmented by both **exchange and fiat currency/region** rather than assuming one globally frictionless market. Their regional groupings included China, Japan, Korea, the United States and Europe, with crypto-only venues treated separately. They converted major fiat prices using external foreign-exchange data, including JPY/USD, KRW/USD and EUR/USD rates.

This matters directly for the project: comparing two BTC prices quoted in different currencies is a joint claim about the crypto prices **and** the FX conversion used at that time. A cross-venue diagnostic must therefore preserve quote-currency identity and point-in-time conversion provenance.

### 3.3 Timestamp and data-quality issues were nontrivial

The paper documents several practical data issues that a replication must not ignore:

- Bithumb timestamps were recorded in local Korean time while most other exchange data were UTC;
- trade-direction fields for Bithumb and Quoine appeared reversed and were corrected after diagnostic checks;
- observations associated with exchange closures/system problems and stale/outlying prices were cleaned;
- the authors used exchange-specific information and robustness diagnostics rather than assuming every vendor field was correct.

**Project implication:** vendor-normalized data still require exchange-specific validation. A clean schema is not proof that timestamps, aggressor side, or market status are correct.

## 4. How the paper synchronized prices

### 4.1 Descriptive fragmentation index

For broad price-comparison figures, the authors formed a **minute-level volume-weighted average price (VWAP)** for each exchange. They then compared the maximum and minimum exchange prices within each minute and aggregated those deviations to daily measures.

That construction is useful for describing segmentation, but it is **not** an execution-price model. A VWAP from a one-minute bucket can combine trades that were not simultaneously available.

### 4.2 Arbitrage-profit construction was more demanding

For their historical arbitrage-profit calculation, the authors used a much narrower and more execution-aware construction over the high-liquidity/high-spread period **November 2017 through February 2018**:

- calculations were performed at the **second** level and then aggregated;
- they focused on seconds where the inter-regional price difference exceeded 2%;
- on the low-price venue/region, they used sell-initiated trading volume as evidence that one could buy at that price;
- on the high-price venue/region, they used buy-initiated trading volume as evidence that one could sell at that price;
- executable matched size was bounded by the smaller of the two relevant volumes;
- when multiple transactions occurred during a second, they used VWAP;
- an additional rule addressed unusually large spreads, with a bounded outstanding inventory assumption.

This design does not make every estimated historical dollar profit directly realizable, but it is materially stronger than subtracting two last-trade prices. It is the right conceptual precedent for this project: **evidence of contemporaneous executable-side liquidity is required.**

## 5. Historical evidence of fragmentation — and its limits

The paper reports economically large price segmentation during parts of 2017–2018. Cross-country deviations were generally much larger than within-country deviations. Korea and Japan exhibited especially large premiums over U.S. markets during parts of the late-2017/early-2018 boom, while U.S.–European differences were much smaller. Crypto-to-crypto relative-price deviations were smaller than fiat-crypto deviations.

The published abstract summarizes the broader findings: recurrent cross-exchange arbitrage opportunities, substantially larger cross-country than within-country deviations, smaller deviations between cryptocurrencies, and co-movement of country premia with Bitcoin appreciation.

These are **historical empirical findings**, not current expected returns and not evidence that comparable opportunities exist in 2026. Market structure, exchange access, stablecoins, institutional participation, fee schedules, market makers, APIs, custody, transfer rails and regulation have changed substantially since the sample.

The related AEA price-discovery paper adds an important qualification: when markets were segmented, high-premium exchanges became less influential in global price discovery. Therefore, a locally extreme price should not automatically define a global “true price.”

## 6. Why a visible spread may not be executable

### 6.1 Transfer and settlement latency

The paper's textbook example is: buy BTC in a low-price U.S. market, transfer it to Korea, sell it at the higher Korean price, convert KRW to USD, and repatriate the funds. The authors explain why this is not a riskless instantaneous loop: blockchain settlement and exchange crediting took time, while fiat transfers could take hours or days.

For a current project diagnostic, the relevant quantities are not the historical transfer times. They are **point-in-time current** exchange withdrawal status, blockchain/network settlement, deposit-credit rules, fiat/stablecoin conversion and withdrawal constraints, and any account-specific holds.

### 6.2 Short-sale limitations

The paper notes that only a few exchanges supported short selling, and major premium markets such as Korea/Japan in the sample did not provide the straightforward short leg needed to lock in a spread without inventory.

This project is currently spot-only/no-leverage. Therefore R03 must not rely on a short-sale or derivative hedge to turn a price discrepancy into an executable strategy.

### 6.3 Pre-positioned inventory

The authors discuss a more realistic simultaneous approach: hold fiat on the low-price exchange and BTC on the high-price exchange, then buy and sell concurrently. That removes much of the convergence risk **for the matched trade**, but inventory becomes unbalanced and eventually has to be recycled. The recycling leg can reintroduce transfer delays, price exposure, banking/capital-movement constraints, and operational risk.

For this project, a simultaneous cross-venue observation must therefore be classified separately from a fully recyclable arbitrage loop.

### 6.4 Fees and spread costs

The paper reports historical exchange/withdrawal/network costs from its sample period and argues that they were too small to explain the very large multi-percent deviations it documented. Those historical numbers must **not** be reused as current cost assumptions.

Any future diagnostic must snapshot and hash the exact fee schedule applicable to the chosen venue/account/tier at experiment start, including maker/taker fees, bid/ask spread, depth/slippage assumptions, withdrawal/network costs, conversion costs and any relevant deposit/withdrawal restrictions.

### 6.5 Market access and capital controls

The authors link cross-country segmentation to barriers in moving fiat capital and discuss historical Korean capital controls/account-access restrictions as an important example. These details are period- and jurisdiction-specific.

R03 therefore adopts the mechanism — **market accessibility and capital mobility can prevent arbitrage** — without treating any 2017–2018 legal rule as current. Current legal/account access must be requalified from current authoritative sources before an empirical execution claim is allowed.

## 7. R03 market-fragmentation checklist

Every cross-venue signal or apparent arbitrage must pass all applicable rows before being described as executable. Failing rows do not get silently imputed.

| Dimension | Required evidence | Failure classification |
| --- | --- | --- |
| Venue identity | Exact exchange/legal venue, market symbol, spot status | Unknown venue/instrument |
| Account accessibility | Account is legally and operationally available for the intended jurisdiction/account | Inaccessible venue |
| Asset comparability | Same base asset and economically equivalent settlement asset | Non-comparable asset |
| Quote currency | Exact quote asset preserved; USD, USDT, USDC, EUR, KRW, JPY etc. not conflated | Currency mismatch |
| FX/stablecoin conversion | Point-in-time conversion source and timestamp | Unpriced conversion risk |
| Event/quote time | Exchange time plus receive/collection time where available | Timing unverified |
| Clock normalization | Explicit UTC normalization; source timezone retained | Misaligned clocks |
| Quote freshness | Predeclared maximum age and no stale forward-fill | Stale quote |
| Market status | Venue online; no maintenance/halt/reconnect ambiguity | Non-live market |
| Side of market | Buy at ask, sell at bid; last/mid alone insufficient | Non-executable price |
| Depth | Size available at or through required levels | Phantom size |
| Fees | Applicable maker/taker tier and other transaction fees | Omitted cost |
| Slippage | Size-aware execution price, not top-of-book assumption for large notional | Unrealistic fill |
| Inventory | Fiat/quote inventory on buy venue and base asset on sell venue if simultaneous spot | Missing inventory |
| Transfer path | Deposit/withdrawal enabled, network identified, credit rules known | Impossible transfer |
| Recycling | Feasible path to restore inventory without assuming instant settlement | Non-recyclable loop |
| Withdrawal/network costs | Point-in-time amount/currency/network-specific cost | Omitted transfer cost |
| Banking/fiat constraints | Current transfer, banking and account limits if fiat movement is required | Capital-mobility constraint |
| API/data provenance | Provider, endpoint, retrieval time, source time, schema/version, immutable hash | Unverifiable data |
| Gap/outage handling | Detected gaps retained and excluded per fixed rule; no silent interpolation | Contaminated interval |
| Causal availability | Every field known at decision timestamp; no retrospective cleaning leakage | Look-ahead |

## 8. Bounded diagnostic proposal — R03-A

This is a **proposal only**. It does not authorize a data run.

### Objective

Measure how much apparent cross-venue spot-price dispersion survives progressively stricter reality filters:

1. same timestamp;
2. same/equivalent quote currency;
3. live bid/ask rather than last trade;
4. quote freshness;
5. executable depth;
6. point-in-time fees;
7. venue/account accessibility;
8. inventory and transfer/recycling feasibility.

The primary output is a **fragmentation diagnostic**, not a trading backtest.

### Minimal candidate universe

Start only after venue/account/data qualification. Prefer a small set of high-liquidity **spot** venues and a common quote currency where possible. BTC and ETH are the natural first assets because they overlap the project's existing research universe, but R03-A must remain independent from protected AMS-DEP outcomes.

USD and USDT markets should **not** be pooled as identical. If USDT or another stablecoin is used, the stablecoin-to-fiat conversion/basis becomes an explicit input and sensitivity dimension.

### Required data

At minimum, for every venue/market observation:

```text
venue
market
base_asset
quote_asset
exchange_event_time
provider_collect_or_receive_time
best_bid_price
best_bid_size
best_ask_price
best_ask_size
market_status
source_sequence_or_id_if_available
continuity_or_gap_flag
```

For depth-aware analysis, capture enough order-book levels to price predeclared notionals. Also snapshot immutable metadata for:

```text
fee schedule / account tier
withdrawal fees by asset/network
network/deposit/withdrawal status
minimum order sizes and increments
asset/network mapping
venue status/maintenance records
FX or stablecoin conversion source
```

### Core descriptive measures

For venue `i` as buyer and venue `j` as seller at synchronized time `t`:

```text
gross_cross_venue_gap_ij(t) = bid_j(t) - ask_i(t)

gross_gap_bps_ij(t) = 10,000 * [bid_j(t) / ask_i(t) - 1]
```

This is already stricter than a last-price comparison because it crosses the spread correctly.

For each predeclared notional `Q`, compute the depth-weighted buy and sell prices from contemporaneous books. Then report a **cost-adjusted dispersion measure** using the exact contemporaneous fee schedule. Do not label it profit unless a separate future execution protocol has established inventory, access, fills, recycling and all costs.

### Progressive-filter output

For each asset/pair and venue pair, report:

- raw same-minute or same-second last-price dispersion, for comparison only;
- synchronized top-of-book bid/ask dispersion;
- fraction removed by freshness filtering;
- fraction removed by currency/stablecoin normalization;
- fraction removed by depth constraints at each registered notional;
- fraction removed by fees;
- fraction rendered non-executable by venue/account access;
- fraction requiring unavailable or non-recyclable inventory movement;
- duration distribution of surviving dislocations;
- gap/outage counts and excluded intervals.

This decomposition tells us **why** a visually attractive discrepancy disappears instead of only reporting a final number.

### Timing contract

A future R03-A implementation must register one synchronization rule before viewing outcomes. At minimum:

- retain source/exchange timestamp and collection/receive timestamp separately;
- normalize source time to UTC without discarding original timezone metadata;
- define a maximum permissible quote age in advance;
- never forward-fill across maintenance, reconnect, detected sequence gap or market halt;
- for asynchronous venues, use only information causally observed by the collector at the comparison timestamp;
- do not use a later message to retroactively improve the earlier book state.

### Rejection / stop conditions

R03-A should be classified **NOT FEASIBLE** or the affected venue pair rejected if any of the following holds:

1. timestamps cannot establish contemporaneous market states;
2. quote age cannot be bounded well enough to rule out stale-price artifacts;
3. the data cannot reconstruct executable bid/ask and depth for the registered notional;
4. currency/stablecoin conversion cannot be aligned point-in-time;
5. current fees/access restrictions cannot be documented;
6. the apparent gap exists only on inaccessible venues or non-live markets;
7. the discrepancy disappears after bid/ask, currency and cost normalization;
8. a claimed arbitrage requires instant asset/fiat transfers that are not operationally possible;
9. the strategy would require shorting/leverage contrary to the project's spot-only scope;
10. continuity gaps, outages or vendor transformations make the result non-auditable.

Conditions 7–9 do **not** mean the scientific diagnostic failed. They can be a valid negative result: the apparent opportunity was market-data or execution illusion rather than usable economic arbitrage.

## 9. Data-source feasibility

### Coin Metrics Market Data API

Current Coin Metrics documentation exposes market-level catalogs and time ranges for trades, quotes and order books, with raw/aggregated quote/order-book endpoints. The documented order-book/quote schemas include nanosecond-format timestamps, market identifiers and, for order books, database/collection timing fields. This data class is suitable in principle for a synchronized cross-venue diagnostic.

However, actual feasibility remains **conditional** because product entitlement, historical coverage for the exact same venues/markets/time interval, retained depth, schema history, licensing and cost have not been certified for this project.

### Kaiko

Kaiko is the principal commercial data source used in the Makarov–Schoar study and is therefore a natural historical-replication candidate. R03 does not assume the same 2017–2018 package is currently sold with identical fields or licensing. Current coverage, timestamps, order-book depth, exchange identifiers, entitlement and pricing must be separately qualified before adoption.

### Exchange-native prospective capture

Direct exchange feeds can provide the strongest point-in-time provenance for a future prospective diagnostic if collection is engineered correctly. They also create the largest burden: multiple exchange schemas, reconnect logic, clock alignment, sequence/gap handling, rate limits, maintenance states, symbol/network changes, and durable raw-message storage.

**Feasibility conclusion:** the data class exists, but **no provider is yet certified for R03-A**. The next step is a data-source qualification matrix before any empirical run.

## 10. Evidence cards

### R03-C01 — Cross-country fragmentation was materially larger than within-country fragmentation

```yaml
claim_id: R03-C01
source_id: Makarov_Schoar_2020_JFE
source_version: published metadata + author-final manuscript lineage
review_status: applicability_assessed
source_locator: abstract; sections on price deviations across countries/exchanges
claim_paraphrase: Historical crypto price deviations were recurrent and substantially larger across countries than within countries, while crypto-to-crypto deviations were smaller.
evidence_type: empirical
market_and_sample: BTC/ETH/XRP, multi-exchange, principally 2017-01-01 to 2018-02-28
data_requirements: [multi-venue trades, currencies, FX normalization]
limitations_and_contradictions: [historical sample, market structure has changed]
proposed_project_application: treat venue/currency fragmentation as a required confound and diagnostic dimension
decision: supported_as_historical_evidence
```

### R03-C02 — Executed-side transaction evidence is stronger than last-price comparison

```yaml
claim_id: R03-C02
source_id: Makarov_Schoar_2020_JFE
review_status: applicability_assessed
source_locator: arbitrage-profit construction section
claim_paraphrase: The historical arbitrage calculation matched transaction volume at executable directions and short time intervals rather than relying on arbitrary stale last prices.
evidence_type: empirical_method
data_requirements: [transaction timestamps, trade direction, price, volume]
proposed_project_application: require bid/ask or executable-direction evidence and matched depth before calling a discrepancy executable
decision: supported_methodological_precedent
```

### R03-C03 — Transfer/repatriation and inventory constraints break textbook arbitrage

```yaml
claim_id: R03-C03
source_id: Makarov_Schoar_2020_JFE
review_status: applicability_assessed
source_locator: limits-to-arbitrage discussion
claim_paraphrase: Cross-venue price differences can persist because crypto transfer, fiat repatriation, short-sale limits, market access and inventory recycling constrain arbitrage capital.
evidence_type: institutional/mechanism + empirical context
limitations_and_contradictions: [specific 2017-2018 restrictions are not current facts]
proposed_project_application: separate observed dispersion, simultaneously executable spread, and fully recyclable arbitrage loop
decision: supported_mechanism; current_parameters_require_requalification
```

### R03-C04 — Segmented premium venues need not lead global price discovery

```yaml
claim_id: R03-C04
source_id: Makarov_Schoar_2019_AEA
review_status: applicability_assessed
source_locator: abstract/full short paper
claim_paraphrase: When markets were more segmented, exchanges with larger arbitrage spreads relative to the U.S. became less important for price discovery.
evidence_type: empirical
proposed_project_application: do not treat the most extreme local price as the global reference price by default
decision: supported_as_transfer_guardrail
```

## 11. What R03 does and does not authorize

### Completed by R03

- full-source recovery beyond the playbook's abstract-only status;
- extraction of sample period, exchanges, timestamps, currency normalization and synchronization method;
- extraction of historical transaction-side arbitrage methodology;
- extraction of fees/transfer/inventory/access constraints;
- repository deduplication check for the R03 source/topic;
- market-fragmentation checklist;
- bounded R03-A descriptive diagnostic proposal;
- data-source feasibility conclusion and rejection conditions.

### Not authorized or not completed

- no new cross-exchange dataset was downloaded or queried for outcomes;
- no current venue was certified as accessible for the user's account/jurisdiction;
- no current fee schedule or legal transfer rule was frozen;
- no R03-A market-data run was executed;
- no strategy return/P&L was calculated;
- no paper/live trade or API order was placed;
- no Validation/OOS data were accessed;
- no AMS-DEP gate or frozen method was changed;
- no repository file was created, changed or committed by this review.

## 12. Final R03 status and handoff

**R03 COMPLETE — EXCHANGE FRAGMENTATION IS A SUPPORTED MATERIAL CONFOUND; EXECUTABLE-ARBITRAGE VALIDITY REMAINS UNRESOLVED UNTIL CURRENT DATA/ACCESS/COST QUALIFICATION.**

The paper establishes that historical crypto markets could remain segmented for economically meaningful periods and provides a stronger template than simple last-price comparison. The project's correct response is to make fragmentation and executability explicit research controls, not to infer a trading edge from raw cross-exchange spreads.

**Immediate next research step:** R04 — *Crypto Carry* literature/applicability review, while R03-A remains an unexecuted future diagnostic pending an explicit data-source qualification and separate authorization.

## Source register

1. Makarov, I. & Schoar, A. (2020). **Trading and Arbitrage in Cryptocurrency Markets.** *Journal of Financial Economics*, 135(2), 293–319. DOI: `10.1016/j.jfineco.2019.07.001`.
2. Makarov, I. & Schoar, A. (2019). **Price Discovery in Cryptocurrency Markets.** *AEA Papers and Proceedings*, 109, 97–99. DOI: `10.1257/pandp.20191020`.
3. MIT Open Access Articles. Author-final manuscript record for *Trading and Arbitrage in Cryptocurrency Markets*. Permanent record: `https://hdl.handle.net/1721.1/130495`.
4. Coin Metrics API v4 documentation. Market catalogs, trades, quotes and order-book endpoints. Accessed 2026-09-20.

