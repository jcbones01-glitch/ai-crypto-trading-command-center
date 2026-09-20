# R02 — Order-Flow Replication Specification and Data-Feasibility Review

**Completed:** 2026-09-20  
**Project:** AI Crypto Trading Command Center  
**Scope:** literature applicability, crypto transfer risks, exact replication specification, and data-source feasibility.  
**Authorization:** research/design only. No market-data experiment, Validation/OOS access, P&L calculation, paper trading, live trading, release-gate change, frozen AMS-DEP change, or repository mutation was performed.

## Decision memo

**R02 is complete as a feasibility and replication-design review.**

The main result of Cont, Kukanov & Stoikov (2014) is suitable as a **descriptive microstructure replication target**, but not as a trading signal by itself. Their central regression relates order-flow imbalance (OFI) accumulated inside a time interval to the **mid-price change over that same interval**. That is a contemporaneous price-impact relationship. It does not establish that OFI known at time `t` predicts a return after `t`.

A crypto replication is technically plausible if the project can obtain an ordered, gap-detectable sequence of best-bid/best-ask price and queue-size updates, with causal timestamps and enough metadata to reconstruct the top of book. An exact historical replication from a free periodic-snapshot dataset is **not** adequate, because snapshots can collapse multiple book changes and bias OFI. Prospective live capture or a vendor tick-level L1/L2/L3 archive is the appropriate data class.

The literature also argues against assuming the equity result transfers unchanged. Small-tick markets can exhibit history-dependent order-book impact; Bitcoin studies show order-book state matters and that cross-venue information flow can affect price discovery. A recent, non-peer-reviewed BTC/USDT predictive study using Cont-style OFI reports small out-of-sample explanatory power and multiple result reversals as the sample expanded. That is useful negative/fragility evidence, not validation.

**Project decision:**

- Cont-style contemporaneous OFI replication: **SUPPORTED as a descriptive research target.**
- Crypto transfer without re-estimation and robustness checks: **UNSUPPORTED.**
- Exact historical replication from periodic snapshots: **UNSUPPORTED.**
- Exact/near-exact replication from complete tick-level top-of-book state transitions: **CONDITIONALLY FEASIBLE.**
- Claim that contemporaneous OFI implies future-return predictability: **UNSUPPORTED.**
- Short-horizon predictive OFI research in crypto: **UNRESOLVED; requires a separate preregistered future experiment and separate data authorization.**
- Trading or execution based on OFI: **NOT AUTHORIZED.**

## 1. Repository reconciliation and current authority

Repository reviewed through the connected GitHub account before R02 work:

- Repository: `jcbones01-glitch/ai-crypto-trading-command-center`
- Research branch: `adaptive-markets-research`
- Current PR #42 head: `6431e9995ed3c904b673603b662506692d370539`
- PR #42 remains an open draft against `gate2-research-foundation`.
- Current machine gate: `V2_SYNTHETIC_CALIBRATION_AUTHORIZED`.
- `v2_synthetic_calibration_passed`: `false`.
- V2 holdout: locked.
- Development market-data AMS-DEP execution: locked.
- Validation/OOS: locked.
- Strategy P&L, paper trading, and live trading: locked.

The current release gate explicitly says the next AMS-DEP gate is to execute the frozen V2 **synthetic calibration only** and retain PASS or FAIL. R02 does not modify or supersede that authority.

Repository code search found no current Cont/Kukanov/Stoikov or OFI implementation and no existing order-flow replication module under the searched terms, so this review does not duplicate an identified repository component.

## 2. Primary source: what Cont, Kukanov & Stoikov actually tested

### Source

Rama Cont, Arseniy Kukanov, Sasha Stoikov, **“The Price Impact of Order Book Events,”** *Journal of Financial Econometrics* 12(1), 47–88 (2014). Related DOI: `10.1093/jjfinec/nbt003`. Open manuscript: arXiv `1011.6402`.

### Data and sampling

The manuscript reports:

- one calendar month: April 2010;
- 50 stocks randomly selected from S&P 500 constituents;
- NYSE TAQ consolidated quotes and trades via WRDS;
- Level-I information: best bid price/size and best ask price/size;
- quote records intended to contain all top-of-book queue-size changes;
- a uniform **10-second** aggregation grid for the baseline analysis;
- robustness checks over time scales from about 10 quote updates to 10 minutes;
- separate OLS estimation in **half-hour** subsamples.

The study's reason for Level-I rather than deeper-book data is important for this project: the OFI measure is constructed from changes at the best bid and ask, so full order-by-order L3 data are not mathematically required for the baseline measure if every relevant top-of-book state transition is observed.

### Exact event contribution

For consecutive top-of-book observations `n-1` and `n`, with best bid price/size `(P^B, q^B)` and best ask price/size `(P^A, q^A)`, the paper defines the event contribution:

```text
e_n = 1{P^B_n >= P^B_{n-1}} q^B_n
    - 1{P^B_n <= P^B_{n-1}} q^B_{n-1}
    - 1{P^A_n <= P^A_{n-1}} q^A_n
    + 1{P^A_n >= P^A_{n-1}} q^A_{n-1}
```

OFI over interval `[t_{k-1}, t_k]` is the sum of `e_n` for all book events in that interval.

The mid-price change is measured on the **same** time grid:

```text
mid_k = (best_bid_k + best_ask_k) / 2
DeltaP_k = (mid_k - mid_{k-1}) / tick_size
```

The baseline empirical equation is:

```text
DeltaP_k = alpha_i + beta_i * OFI_k + epsilon_k
```

estimated inside half-hour block `i`.

### What the paper found

The paper reports a strong, approximately linear contemporaneous relationship between OFI and short-interval mid-price changes, with average R-squared around 65% across its equity sample. It reports that the price-impact coefficient is inversely related to average market depth. The paper also finds trade-volume-only specifications less robust than OFI-based specifications.

The paper uses heteroskedasticity-consistent (White) standard errors for the short-interval regression and Newey–West standard errors for the depth/impact relationship.

### Critical interpretation

This is an **instantaneous/contemporaneous price-impact model**. The OFI and `DeltaP` in the baseline equation are measured over the same 10-second interval. A strategy cannot legitimately compute the full interval's OFI and then pretend it was known at the beginning of that same interval.

Therefore:

> High contemporaneous R-squared would demonstrate that order-book changes and price formation are tightly connected. It would not, by itself, demonstrate a forecast, an exploitable edge, or profitability after spread, fees, latency, adverse selection, and fill uncertainty.

That distinction is the central guardrail for R02.

## 3. Transfer-risk evidence

### 3.1 Event impact can be history-dependent

Eisler, Bouchaud & Kockelkoren, **“The price impact of order book events: market orders, limit orders and cancellations,”** *Quantitative Finance* 12(9), 1395–1419 (2012), studies auto/cross-correlations among order-book event types and their effect on future price changes. Their abstract reports that for small-tick stocks, a simple permanent, non-fluctuating bare-impact model is insufficient and a history-dependent component related to past order flow is needed.

**Project implication:** the Cont linear specification should be replicated rather than assumed. Crypto markets often have very small relative tick sizes, so small-tick findings are particularly relevant as a transfer warning.

### 3.2 Bitcoin order-book state matters and information is cross-venue

Alexander, Heck & Kaeck, **“Price Discovery in Bitcoin: The Role of Limit Orders”** (2022 working paper), studies BTC/USD on Coinbase. Its abstract reports that order-book state materially affects price discovery, that limit orders contribute strongly because they are abundant, and that Coinbase price discovery is influenced by information flows from other exchanges.

**Project implication:** a single-venue OFI replication can be scientifically useful, but a future prediction study must treat venue fragmentation as a possible omitted-information source. It cannot automatically interpret a Coinbase/Binance signal as self-contained market information.

### 3.3 Recent crypto evidence is not stable enough to count as validation

A 2026 SSRN preprint by Michael Schmalz, **“Order Flow Imbalance and Short-Horizon BTC/USDT Returns: A Signal That Kept Needing More Scrutiny,”** tests Cont-style OFI against 1–10 second future returns using Binance.US L2 data. The abstract reports that the out-of-sample result reversed twice as the captured sample expanded from roughly 7 to 9 to 17 days. The reported positive out-of-sample R-squared values, when positive, are small (roughly tenths of a percent to around 1%).

This source is very recent and not peer reviewed. It is retained because its instability is directly relevant to project design, not because it validates a strategy.

**Project implication:** any later predictive experiment must be long enough to expose regime dependence and must preserve every interim failure. A single attractive walk-forward result is insufficient.

## 4. R02 replication specification — descriptive phase

This section defines a future protocol target only. It does not authorize a run.

### R02-A objective

Test whether a crypto spot venue exhibits the same **contemporaneous** Level-I OFI/price-impact structure documented by Cont et al., while keeping the analysis separate from return forecasting.

### Required raw fields

At minimum for every top-of-book state transition:

```text
venue
market/symbol
exchange_event_time (if supplied)
collector_receive_time
sequence/update id (if supplied)
best_bid_price
best_bid_size
best_ask_price
best_ask_size
source connection/session id
reconnect/gap flag
raw message identifier/hash
```

Additional strongly preferred fields:

```text
exchange trade id and trade timestamp
aggressor/maker side where natively reported
price tick size and quantity step size
market-status/maintenance events
source schema/version
snapshot-vs-delta flag
```

### Reconstruction contract

1. Start from an authoritative snapshot when the source requires it.
2. Apply updates strictly according to the source's documented sequencing rules.
3. Record both exchange/source time and local receive time where available.
4. Treat a detected update gap, invalid sequence, reconnect without valid recovery, crossed book, missing side, or non-positive best quote/size as a continuity break.
5. Do not interpolate missing book states.
6. Do not join across a continuity break when calculating `e_n`.
7. Preserve raw source messages or immutable hashes so a reconstructed book can be audited.
8. Preserve venue-native price/quantity precision; do not round before OFI construction.

### Baseline replication grid

To match the primary paper as closely as a 24/7 crypto market allows:

- aggregate `e_n` on non-overlapping **10-second UTC intervals**;
- calculate mid-price change over that exact same interval;
- estimate the baseline equation separately in fixed **30-minute UTC blocks**;
- use the venue's effective tick size at the observation time;
- use an intercept in the regression;
- retain White/HC heteroskedasticity-consistent inference for the same-interval regression;
- estimate the price-impact/depth relation separately, with dependence-robust inference consistent with the original paper's use of Newey–West errors.

Crypto has no daily market open and close. Equity open/close seasonality should therefore **not** be transplanted as a hypothesis. Any 24-hour seasonality analysis must be separately defined in UTC and interpreted as crypto-specific.

### Registered descriptive outputs

A future descriptive replication should report at least:

- distribution of `beta_i` across 30-minute blocks;
- distribution of R-squared across blocks;
- intercept magnitude/significance;
- linear vs predeclared nonlinear extension fit;
- relation between `beta_i` and average top-of-book depth;
- spread and tick-size context;
- missing/gap rate and excluded-window counts;
- event intensity and top-of-book update intensity;
- sensitivity to a small preregistered set of aggregation windows, preserving all outcomes;
- results by calendar time only if that analysis was preregistered.

No trading metric belongs in R02-A.

## 5. Future predictive extension — concept only, not authorized

If the descriptive replication later passes its data-integrity checks, a **different** experiment could ask a predictive question.

The timing must change from:

```text
OFI[t-10s, t]  <->  return[t-10s, t]     # contemporaneous
```

to something causal such as:

```text
OFI[t-10s, t]  ->  return[t, t+h]         # predictive
```

A future preregistration would need to define `h`, decision latency, feature publication time, order submission latency, spread/fees, maker/taker assumptions, fill logic, queue uncertainty, baselines, purging/embargo, multiple testing, walk-forward partitions, and a minimum economic edge after costs.

At minimum it should benchmark OFI against simple alternatives such as recent return/autocorrelation and trade-flow imbalance. It must not use the contemporaneous Cont R-squared as its expected predictive R-squared.

This future experiment would require separate project authorization and must respect the existing market-data/Validation/OOS governance.

## 6. Data-source feasibility

### 6.1 Binance Spot public WebSocket — prospective capture

Current Binance Spot documentation exposes:

- a real-time `bookTicker` stream that pushes updates to the best bid/ask price or quantity and includes an order-book update ID;
- a differential depth stream at 1000 ms or 100 ms with event time, first update ID, final update ID, and changed bid/ask price levels;
- trade/aggregate-trade streams with trade timestamps and maker-side information.

**Strengths:** public prospective feed; enough information to build a top-of-book state series; update IDs permit gap/order checks on differential depth.

**Limits:** differential-depth messages can summarize multiple book changes within a 100 ms update message, so they are not identical to the primary paper's complete sequence of individual top-of-book quote events. `bookTicker` is closer to the Level-I target but the documented payload does not include an exchange event timestamp, so a collector must retain receive time and update ID. Official live endpoints also do not, by themselves, solve historical backfill.

**R02 status:** **feasible for a prospectively designed collection pilot; not yet certified as an exact historical replication source.**

### 6.2 Coin Metrics market order books — historical candidate

Current Coin Metrics API documentation exposes market-orderbook time series, including:

- raw or downsampled granularity;
- nanosecond-precision `time`;
- bids and asks;
- `coin_metrics_id`;
- database time and, when available, collection time;
- catalog endpoints for checking market/depth/time coverage.

**Strengths:** explicit historical coverage discovery and useful timing/provenance fields; suitable as a serious historical candidate.

**Limits:** documentation alone does not prove that `raw` records preserve every top-of-book state transition needed for an exact Cont-style event sequence for every venue/period. Entitlements can also vary.

**R02 status:** **conditionally feasible; require a sample-data qualification before scientific use.**

### 6.3 CoinAPI L2/L3 — strong reconstruction candidate

Current CoinAPI documentation describes L2 order-book messages containing:

- full snapshots plus incremental updates;
- connection-local sequence numbers;
- exchange time and CoinAPI receive time;
- `is_snapshot`;
- changed bid/ask levels.

Its L3 interface, where a venue supports it, additionally exposes order-level IDs and update types such as ADD, UPDATE, SUBTRACT, DELETE, and MATCH.

**Strengths:** the snapshot/delta/sequence model is directly compatible with auditable book reconstruction; dual timing fields are valuable for causal/data-latency studies; L3 can distinguish individual passive-order changes when the source venue exposes them.

**Limits:** coverage and historical entitlement must be verified for the exact venue/symbol/date; connection-local sequence rules must be respected; L3 availability is venue dependent.

**R02 status:** **technically strong candidate, pending coverage/cost/sample validation.**

### 6.4 Kaiko tick-level Level 1/2 — strong but commercial

Current Kaiko documentation describes:

- tick-level best-bid/ask streaming;
- tick-level all-bids/all-asks data;
- 72-hour streaming replay;
- cloud-delivered tick-level full order-book history since August 2023 for supported CeFi spot markets;
- top-of-book cloud history since December 2022;
- separate slower raw snapshot products at at-least-one-snapshot-per-minute frequency.

The current public product page lists Level-2 tick-level packages starting in the thousands of dollars per month.

**Strengths:** technically appropriate tick-level data class and historical depth for supported markets.

**Limits:** cost is high for a research-stage project; exact venue coverage and message semantics still need sample qualification. The once-per-minute snapshot product is **not** adequate for Cont OFI.

**R02 status:** **technically suitable but economically non-preferred for an initial project pilot unless access terms change.**

## 7. Data-source acceptance test

Before any provider is approved, a small **data qualification** sample should satisfy all of the following without looking at strategy profitability:

1. **Coverage:** the selected spot venue and symbol are present for the required dates.
2. **Event/state fidelity:** every best-bid/best-ask change needed to reconstruct consecutive Level-I states is represented, or the exact batching limitation is documented and accepted as an approximation.
3. **Sequence integrity:** gaps, duplicates, reconnects, and snapshot resets can be detected deterministically.
4. **Timing:** exchange/source time and collector/receive time semantics are documented; no future timestamp is used to build a feature.
5. **Precision:** price and size are lossless at venue-native precision.
6. **Book validity:** no unexplained crossed books, negative sizes, or impossible transitions after reconstruction.
7. **Outage handling:** maintenance and feed interruptions are retained rather than silently bridged.
8. **Reproducibility:** raw inputs can be snapshotted and hashed under licensing terms.
9. **Licensing:** research storage, derived-data use, and repository/publication rules are known.
10. **Cost:** data acquisition and storage fit the research phase before a larger purchase is made.

Failure of items 2–4 is a blocker for exact/causal OFI research.

## 8. Proposed project artifacts if later authorized

The following are design proposals only:

```text
docs/R02_ORDER_FLOW_DATA_CONTRACT.md
research/governance/r02_order_flow_data_gate.json
research/experiments/r02_cont_replication_v1.json
src/research_core/order_flow_imbalance.py
tests/test_order_flow_imbalance.py
tests/test_orderbook_reconstruction.py
research/scripts/qualify_orderbook_source.py
```

The data gate should be separable from a research-result gate: a source can pass integrity/causal-timing qualification even if the Cont relationship fails empirically, and an attractive empirical relationship cannot rescue a failed data-integrity gate.

## 9. Falsification and rejection conditions

The descriptive replication should be rejected or explicitly downgraded to an approximation if:

- top-of-book changes are periodically sampled rather than event-complete;
- sequence gaps cannot be identified;
- reconnects silently alter book state;
- tick/lot rules are unknown or changed without being tracked;
- timestamps cannot establish causal ordering;
- the OFI implementation fails hand-built transition fixtures;
- a purported predictive model uses same-interval OFI to explain the same-interval return and labels that as forecasting;
- a later trading claim omits spread, fees, latency, fills, or queue/adverse-selection effects.

A failure of the Cont-style relationship in crypto would be a valid scientific result. It must not be repaired by post-hoc parameter retuning.

## 10. Evidence status register

| Evidence | Status | R02 use |
|---|---|---|
| Cont, Kukanov & Stoikov (2014) | Full primary manuscript reviewed | Exact replication target and timing distinction |
| Eisler, Bouchaud & Kockelkoren (2012) | Peer-reviewed abstract/method implications reviewed | History-dependence/small-tick transfer warning |
| Alexander, Heck & Kaeck (2022) | Working-paper abstract reviewed | Crypto order-book relevance and cross-venue warning |
| Schmalz (2026) | Recent SSRN abstract reviewed; not peer reviewed | Predictive instability/fragility warning only |
| Binance Spot WebSocket docs | Current official docs reviewed | Prospective public-feed feasibility |
| Coin Metrics API docs | Current official docs reviewed | Historical/orderbook candidate |
| CoinAPI order-book docs | Current official docs reviewed | L2/L3 reconstruction candidate |
| Kaiko data dictionary/product docs | Current official docs reviewed | Tick-level commercial feasibility |

A scite MCP full-text/citation-context cross-check was attempted but the currently connected scite account had exhausted its monthly MCP call quota. This did not block the primary-source review because the Cont manuscript and current provider documentation were directly available.

## 11. R02 completion decision

**R02 COMPLETE — DATA FEASIBILITY CONDITIONALLY POSITIVE, PREDICTIVE VALIDITY UNRESOLVED.**

The project now has a bounded specification for what a valid Cont-style crypto replication would require and a clear reason not to confuse that replication with a trading signal.

No market-data experiment is authorized by this report. No repository code, release gate, workflow, branch, frozen AMS-DEP specification, or protected result was changed or accessed.

Per the existing research playbook, the next scheduled future-phase feasibility package after R02 is **R04 — crypto carry and market stress**, unless the project explicitly chooses to perform the R02 data-source qualification first under a separate authorization.

## Sources

1. Cont, R., Kukanov, A., & Stoikov, S. *The Price Impact of Order Book Events*. Journal of Financial Econometrics 12(1), 47–88. DOI: 10.1093/jjfinec/nbt003. Open manuscript: https://arxiv.org/abs/1011.6402
2. Eisler, Z., Bouchaud, J.-P., & Kockelkoren, J. *The price impact of order book events: market orders, limit orders and cancellations*. Quantitative Finance 12(9), 1395–1419. https://doi.org/10.1080/14697688.2010.528444
3. Alexander, C., Heck, D. F., & Kaeck, A. *Price Discovery in Bitcoin: The Role of Limit Orders*. SSRN 4150979. https://ssrn.com/abstract=4150979
4. Schmalz, M. *Order Flow Imbalance and Short-Horizon BTC/USDT Returns: A Signal That Kept Needing More Scrutiny*. SSRN 7227998 (2026). https://ssrn.com/abstract=7227998
5. Binance Spot WebSocket Market Streams. https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams
6. Coin Metrics API v4, market orderbooks. https://docs.coinmetrics.io/api/v4/
7. CoinAPI Market Data API order-book WebSocket messages. https://www.coinapi.io/products/market-data-api/docs/websocket-ds/messages
8. Kaiko data dictionary / Level 1 & Level 2 data. https://docs.kaiko.com/explore-our-data/data-dictionary
