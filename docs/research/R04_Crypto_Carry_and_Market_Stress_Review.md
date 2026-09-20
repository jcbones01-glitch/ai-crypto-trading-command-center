# R04 — Crypto Carry and Market Stress Review and Preregistration Proposal

**Completed:** 2026-09-20  
**Project:** AI Crypto Trading Command Center  
**Scope:** literature applicability, exact source extraction, source-version reconciliation, dated-futures basis definition, crash/stress target interpretation, data-source feasibility, and a bounded preregistration proposal.  
**Authorization:** research/design only. No new derivatives dataset was queried for outcomes, no strategy P&L was calculated, no Validation/OOS data were accessed, no paper/live trading was performed, no AMS-DEP gate was changed, and no repository mutation was made.

## Decision memo

**R04 is complete as a literature/applicability review and preregistration design.**

Schmeling, Schrimpf & Todorov's 2023 BIS working paper provides direct empirical evidence that **dated crypto futures basis (carry)** for BTC and ETH was large, persistent, and associated with later downside outcomes during the sample they studied. The paper uses daily BTC/ETH spot, futures, options and related data, primarily from March 2019 through January 2022, with constant-maturity 1-month and 3-month dated futures across crypto-native venues and CME. The authors report that higher carry predicts lower subsequent spot returns and more negative realized skew, with stronger evidence in the longer OKEx sample than in CME for some realized-skew specifications.

The paper does **not** define a single binary "crash" event. Its crash-risk evidence is expressed through several continuous measures: option-implied skew/risk reversal, future realized skew, future realized spot returns, future volatility, and futures liquidations. This distinction matters. The project must not silently turn the paper into a threshold-based crash classifier unless a separate prospective definition is frozen first.

The core R04 project application remains **plausible but untested**: ask whether **lagged dated-futures basis provides incremental information about future spot-market stress beyond simple spot-only information**. That is narrower than claiming that crypto carry is itself a trading strategy and narrower than claiming that high basis causes crashes.

**Project decision:**

- Dated-futures basis as a historically supported state/stress variable: **SUPPORTED AS PRIOR EVIDENCE.**
- The 2019–2022 finding as evidence of current 2026 predictability: **UNSUPPORTED WITHOUT NEW TESTING.**
- Perpetual funding as interchangeable with dated-futures basis: **REJECTED.** They are economically related but distinct quantities with different cash-flow and maturity structures.
- A simple lagged-basis predictive diagnostic for future spot outcomes: **SUPPORTED IN PRINCIPLE**, subject to data qualification, causal timing, preregistration and separate empirical authorization.
- A binary "crash" classifier copied from the paper: **UNSUPPORTED**, because the paper does not use one single binary crash definition in its core predictive table.
- A carry-arbitrage trading strategy: **NOT AUTHORIZED** and not the R04 objective.
- Derivatives execution, leverage, shorting, paper trading or live trading: **NOT AUTHORIZED.**

## 1. Playbook requirement and repository reconciliation

The playbook defines R04 as the third-priority literature package using:

Maik Schmeling, Andreas Schrimpf & Karamfil Todorov, **Crypto Carry**, BIS Working Paper No. 1087 (2023).

Required extraction from the playbook:

- futures maturity and annualization conventions;
- contracts and venues;
- sample coverage;
- crash definition;
- controls;
- timing;
- robustness results;
- explicit distinction between dated-futures basis and perpetual funding.

Required deliverable:

- a data dictionary;
- a preregistration proposal;
- a simple baseline;
- explicit conditions for rejecting incremental predictive usefulness.

Repository search before completing R04 found one relevant prior boundary in `docs/GATE2_NEXT_RESEARCH_CANDIDATES_V1.md`: funding-rate/carry hypotheses requiring a new derivatives dataset were explicitly deferred to a **separate data-expansion phase**. No direct Schmeling–Schrimpf–Todorov implementation or existing "Crypto Carry" research module was found in the default-branch search scope. R04 therefore fills a genuine literature/design gap rather than reopening the closed OHLCV-only Gate 2 program.

## 2. Source-version reconciliation

### 2.1 Primary playbook source

Schmeling, M., Schrimpf, A. & Todorov, K. (2023), **Crypto Carry**, BIS Working Paper No. 1087, published 4 April 2023.

Primary source: `https://www.bis.org/publications/working-paper-1087-crypto-carry`

The detailed extraction below is anchored to the 54-page BIS working paper because that is the source named by the playbook.

### 2.2 Later peer-reviewed version

A later version was published online in **Management Science on 6 May 2026** under DOI `10.1287/mnsc.2024.05069`.

The published-version abstract retains the core mechanism—large, time-varying carry linked to trend-chasing demand and constrained arbitrage capital—but its wording differs from the BIS working paper. The 2023 BIS abstract says carry can reach "up to 60% p.a." whereas the 2026 published abstract says it can exceed 40% p.a. The later online appendix also contains additional data and a bear-market robustness exercise.

The publisher lists both an online appendix and replication files. The appendix was accessible and reviewed. The replication-file download endpoint was located but timed out during this review, so the code/data package itself was **not independently audited**. Therefore this report does not claim exact replication readiness.

**Version rule for the project:** never mix coefficients, samples or variable definitions across the 2023 working paper and 2026 journal version without explicitly tagging the source version.

## 3. What the 2023 BIS paper actually studies

### 3.1 Data and sample

Section 2.1 reports **daily data from March 2019 to January 2022** on BTC and ETH spot prices plus futures and options characteristics from **Skew**.

The futures data include:

- futures basis;
- trading volume;
- open interest;
- buy liquidations;
- sell liquidations.

The options data include:

- options open interest;
- put/call open-interest ratio;
- realized 1-month volatility;
- 1-month ATM implied volatility;
- 25-delta risk reversal, defined as the difference between 25-delta put and call implied volatility normalized by ATM implied volatility.

Additional data include Reddit attention measures, Aave/Binance borrowing and lending rates, and CFTC Commitments of Traders positioning.

### 3.2 Maturities and venues

The Skew futures-basis data are described as **annualized constant-maturity 1-month and 3-month basis** for:

- Binance;
- OKEx;
- FTX;
- Huobi;
- BitMEX;
- Deribit;
- CME.

Not every venue has the same history. The paper notes, for example, that CME basis begins in August 2020 in the main sample. Table 1 reports BTC OKEx data beginning March 2019 and ETH OKEx beginning April 2019; ETH CME begins February 2021; all those series end January 2022 in the working-paper table.

### 3.3 Constant-maturity construction and annualization

The working paper states that the Skew basis series are **annualized** and refer to constant maturities of 1 and 3 months, from which the authors calculate constant-maturity futures prices `F_(t,T)`.

However, the working paper text reviewed here does **not** spell out the exact vendor interpolation algorithm or an exact annualization formula such as day-count basis, linear/log interpolation rule, or treatment of contract rolls. This is an unresolved replication detail.

The paper's theoretical equations use log futures and spot prices in the futures-pricing identity, while the Fama-style decomposition is written in price-level differences `F_(t,T) - S_t`. A future project implementation must therefore freeze its own exact basis formula and interpolation method rather than infer one from the word "annualized."

**R04 replication gap:** exact Skew constant-maturity construction and annualization are not sufficiently specified in the 2023 text alone.

## 4. Economic structure and why basis can be informative

The paper organizes carry around a futures-pricing equation in which the futures-minus-spot difference can reflect:

1. fiat-versus-crypto interest-rate differentials;
2. exchange-specific pricing errors;
3. a time-varying crypto convenience yield.

The authors report that exchange fixed effects explain very little variation in carry while time fixed effects explain much more, and that measured interest-rate differentials explain little of the observed variation. They interpret the residual common component as a crypto futures convenience yield linked to speculative demand for leveraged upside exposure and limited arbitrage capital.

This is a **mechanism interpretation**, not proof that carry causes future crashes. For the project, carry should initially be treated as an observable market-state variable whose incremental predictive content can be tested, not as a causal variable.

## 5. Predictive specification in the paper

### 5.1 Fama-style spot/futures decomposition

Section 2.4.1 uses the identity:

```text
F_(t,T) - S_t = [F_(t,T) - F_(T,T)] + [S_T - S_t]
```

and predictive regressions of subsequent spot change and futures-premium change on the current basis.

This design is important because it enforces a forward direction: **basis at time t** is related to changes that occur between `t` and maturity `T`.

The paper reports economically large negative spot-price coefficients in its sample, especially at longer maturities, while emphasizing that the basis mechanically has to converge through some combination of futures and spot price movements by maturity.

### 5.2 Crash/stress regressions

Section 3.4 and Table 8 use a simple predictive form:

```text
y_(t+1 month) = alpha + beta * Carry_t + epsilon_(t+1)
```

The authors report the 1-month BTC basis as the predictor, with future horizons of 1 month and 3 months for realized outcomes.

Table 8 includes:

- 25-delta risk reversal / risk-neutral skew;
- future realized skew;
- future realized spot return.

For BTC, the paper reports negative coefficients linking higher basis to more negative realized skew and lower subsequent spot returns. Evidence differs by exchange and target: some CME realized-skew/return coefficients are not significant at the 1-month horizon but are significant at 3 months, while OKEx has a longer sample and stronger significance in several specifications.

### 5.3 There is no single binary crash definition

The playbook asked for the paper's "crash definition." The correct extraction is:

**The paper does not rely on one threshold-defined binary crash variable in its core predictive analysis.**

Instead, "crash risk" is operationalized using continuous downside/asymmetry and stress measures, including:

- option-implied risk reversal / skew;
- future realized skew;
- future realized spot returns;
- sell liquidations;
- future implied and realized volatility.

This is a major guardrail for R04. A future binary target such as "30-day return below -20%" would be a **new project choice**, not a replication of the paper, and would need independent preregistration.

## 6. Controls and timing

### 6.1 Controls used in explanatory carry regressions

The paper's broader carry regressions examine variables including:

- past 1-week spot return;
- past 1-month spot return;
- Reddit attention;
- signed futures volume;
- futures volume;
- futures open interest;
- lagged basis;
- ATM implied volatility;
- 25-delta skew;
- realized volatility;
- put/call open-interest ratio;
- interest-rate spreads;
- VIX changes in selected specifications.

The authors use Newey-West standard errors with automatic bandwidth selection in the regression tables described in the working paper.

These are not all necessary controls for the project's first test. A simple baseline is preferable before richer specifications.

### 6.2 Timing distinction

Not every relationship in the paper is a forward predictive relationship.

Examples:

- `Carry_t -> future realized return/skew/volatility/liquidations` is predictive in timing.
- `Carry_t` versus an option-implied risk measure observed at `t` is **contemporaneous state association**, even if the option itself prices future risk.
- Explanatory regressions of current carry on current attention, signed volume or open interest are not proof of future spot predictability.

**Project rule:** R04's primary test must use only information available at the decision timestamp and must predict a future spot outcome whose measurement window starts strictly after that timestamp.

## 7. Robustness evidence and limitations

### 7.1 Within the 2023 working paper

The working paper reports several relevant robustness checks:

- same-period versus longest-available exchange samples;
- multiple venues;
- 1-month versus 3-month maturities;
- BTC and ETH;
- CME raw futures prices from Bloomberg as a robustness check against constant-maturity/interpolated futures;
- option, liquidation and volatility measures;
- Newey-West standard errors for overlapping/persistent daily regressions.

The raw-CME-futures appendix result is especially important: some significance patterns differ between raw and interpolated/constant-maturity series. This reinforces the need to treat constant-maturity construction as a model choice rather than a harmless preprocessing step.

### 7.2 2026 published-version appendix

The accessible Management Science online appendix adds, among other things:

- updated cross-exchange summary statistics;
- comparisons with traditional-asset carry;
- a **bear-market subsample from November 2021 to January 2023** for attention/trend-chasing regressions;
- ETH regressions;
- data references including Skew and Coin Metrics.

The bear-market appendix is useful evidence that the authors examined a different market regime. It does **not** by itself establish that the paper's crash-prediction coefficients are stable in 2026 or that the project's proposed spot-stress target will generalize.

### 7.3 Main external-validity limitation

The principal working-paper sample covers a historically unusual phase of crypto market development, including extreme leverage and venues whose market structure, access or existence has changed. FTX is an obvious example of a venue in the historical data that cannot be treated as a current tradable venue.

Therefore the historical findings are prior evidence, not a current edge estimate.

## 8. Dated futures basis is not perpetual funding

This distinction is mandatory.

### Dated-futures basis

A dated futures contract has a specific maturity `T`; its price must converge to the relevant settlement/spot reference at expiration. The basis reflects the difference between futures and spot with an explicit time-to-maturity.

### Perpetual funding

A perpetual swap has no fixed expiry and uses periodic funding transfers to keep the contract close to its reference/index price. Funding rates are a cash-flow mechanism, not the same object as the annualized basis of a dated contract.

They can be correlated because both reflect derivatives demand and financing conditions, but **one cannot be substituted for the other in a replication of Schmeling–Schrimpf–Todorov without a separate theoretical and empirical specification.**

R04 therefore does not authorize a shortcut of using Binance perpetual funding as a stand-in for 1-month or 3-month dated futures basis.

## 9. Current data-feasibility assessment

### 9.1 Coin Metrics

Current Coin Metrics documentation states that its Market Data Feed includes historical and real-time data for thousands of futures markets and exposes, among other fields/endpoints:

- market trades;
- market candles;
- market contract prices;
- market open interest;
- market liquidations;
- market funding rates;
- exchange-asset basis metrics;
- market metadata/catalog information.

This is promising for a future R04 data phase, but documentation alone does not certify that the exact required **dated BTC/ETH contracts, spot references, timestamps, settlement/expiry metadata, and full historical periods** are accessible under the project's entitlement.

The project must query the catalog and record `min_time`, `max_time`, contract identity, market type, exchange, symbol, expiry and any provider-specific transformations before any experiment is approved.

### 9.2 CME

CME currently provides official settlement and historical futures data products, including continuous settlement-based series and DataMine products. CME documentation states that daily settlements are derived from defined settlement procedures and that historical volume/open-interest files can be acquired through DataMine/related licensed products.

For a project replication, raw individual contract settlements plus explicit expiry metadata are preferable to relying only on a vendor's continuous series, because constant-maturity construction should be transparent and reproducible.

### 9.3 Skew / original dataset

The 2023 paper's main data provider is Skew. The later 2026 publication lists replication files through INFORMS, but the replication package itself was not successfully retrieved in this review. Therefore the exact original vendor series and transformation code remain **not independently reproduced**.

### Feasibility conclusion

The required **data class exists**, but a project-ready R04 experiment remains **conditionally feasible**, not certified. Exact provider coverage, entitlement, history, cost, licensing and reproducible basis construction must be qualified first.

## 10. R04 data dictionary for a future project experiment

The following is the minimum proposed schema. Fields labeled **derived** must be computed only from point-in-time inputs and frozen formulas.

| Field | Type | Definition / rule | Timing requirement |
| --- | --- | --- | --- |
| `timestamp_utc` | datetime | common observation timestamp | known at or before decision time |
| `provider` | string | data vendor/source | metadata |
| `venue` | string | exact exchange | metadata |
| `instrument_id` | string | immutable futures/spot identifier | metadata |
| `base_asset` | string | BTC/ETH initially | metadata |
| `quote_asset` | string | USD/USDT/etc. | metadata |
| `instrument_type` | enum | `spot`, `dated_future`, `perpetual` | must not conflate types |
| `expiry_utc` | datetime | expiry/settlement time for dated future | known ex ante |
| `days_to_expiry` | float | actual time remaining | **derived** causally |
| `spot_price` | float | registered spot/reference price | same timestamp convention as future |
| `future_price` | float | dated futures price/settlement | same timestamp convention as spot |
| `basis_raw` | float | frozen price-difference or log-ratio definition | **derived** |
| `basis_ann` | float | annualized basis using frozen day-count/formula | **derived** |
| `basis_1m_const` | float | optional 1m constant maturity | **derived** from registered interpolation only |
| `basis_3m_const` | float | optional 3m constant maturity | **derived** from registered interpolation only |
| `open_interest` | float | dated-future OI | no later revision leakage |
| `volume` | float | dated-future volume | causal window only |
| `liquidations` | float | if provider supports, direction preserved | causal window only |
| `spot_ret_1w_lag` | float | prior 7-day spot return | uses history ending at t |
| `spot_ret_1m_lag` | float | prior 30-day spot return | uses history ending at t |
| `spot_rvol_30d_lag` | float | prior 30-day realized volatility | uses history ending at t |
| `future_spot_ret_30d` | float | spot return from t to t+30d | target only |
| `future_spot_ret_90d` | float | spot return from t to t+90d | secondary target only |
| `future_realized_skew_30d` | float | realized skew of future daily returns | target only |
| `future_rvol_30d` | float | future realized volatility | secondary target |
| `availability_time` | datetime | when each source field was actually available | required for point-in-time audit |
| `revision_flag` | bool | whether observation can be revised | provenance |
| `continuity_flag` | enum | normal/gap/outage | no silent fill |
| `source_hash` | string | immutable snapshot/hash | reproducibility |

### Formula gap to resolve before execution

The preregistration must write the exact formula. A defensible project candidate is an annualized log basis such as:

```text
basis_ann_t = (year_fraction / time_to_expiry) * ln(F_t / S_t)
```

but **this formula is a project proposal, not an extracted claim that Skew used this exact convention**. The day-count basis, settlement timestamp and interpolation to constant maturity must be fixed before any outcomes are viewed.

## 11. Proposed R04-A preregistration — incremental stress information

**Status: PROPOSED ONLY. No execution authorization.**

### 11.1 Research question

Does **lagged dated-futures basis** add incremental information about future spot-market stress beyond simple spot-only predictors?

### 11.2 Assets and initial instrument scope

Start with **BTC only** for the primary specification to minimize multiplicity. ETH can be a separately registered replication asset after the BTC specification is frozen.

Use **dated futures only** for the primary predictor. Perpetual funding is excluded from the primary test.

### 11.3 Primary predictor

One registered measure:

```text
B_t = 1-month constant-maturity annualized dated-futures basis
```

If exact constant-maturity replication is not feasible, the project must either:

1. preregister a nearest-expiry/raw-contract alternative with fixed time-to-maturity rules; or
2. classify the replication as not feasible.

Do not switch methods after seeing which one performs better.

### 11.4 Primary target

A simple source-aligned primary target:

```text
Y_t = BTC spot return over the next 30 calendar days
```

This mirrors the paper's use of future realized spot returns without inventing a binary crash threshold.

### 11.5 Secondary stress targets

Secondary, multiplicity-controlled targets may include:

- future 30-day realized skew;
- future 30-day realized volatility;
- future 90-day spot return.

A binary crash variable is **not** part of the initial R04-A protocol.

### 11.6 Baseline model

Use a deliberately simple spot-only baseline:

```text
Y_t = alpha
      + b1 * spot_return_7d_t
      + b2 * spot_return_30d_t
      + b3 * realized_vol_30d_t
      + error_t
```

Then the augmented model is:

```text
Y_t = alpha
      + b1 * spot_return_7d_t
      + b2 * spot_return_30d_t
      + b3 * realized_vol_30d_t
      + gamma * basis_t
      + error_t
```

The central question is **incremental information from `basis_t`**, not whether basis alone has a statistically significant coefficient.

### 11.7 Causal timing contract

At each observation timestamp `t`:

- futures and spot inputs must use only prices available by `t`;
- contract expiry and metadata must be known by `t`;
- lagged spot controls must end at `t`;
- the future target window starts strictly after `t`;
- no revised or backfilled value may be treated as contemporaneously known unless its publication history proves it;
- no target-derived regime label may enter predictors;
- venue outages and missing contracts are retained as missing rather than silently interpolated.

### 11.8 Overlap and inference

Because 30-day and 90-day forward returns/skew create overlapping observations at daily sampling frequency, naive IID standard errors are inappropriate. The exact inferential method must be frozen before execution. The paper uses Newey-West standard errors with automatic bandwidth selection in its regressions, but the project should not automatically import that setting without checking compatibility with its own sampling, model and evaluation design.

A simpler alternative is to preregister **non-overlapping observation dates** for the primary test. That sacrifices sample size but reduces serial dependence and makes timing easier to audit. Method choice must be made prospectively.

### 11.9 Evaluation hierarchy

R04-A should evaluate, in order:

1. data/timing validity;
2. descriptive stability of basis;
3. in-sample coefficient sign and uncertainty only as descriptive evidence;
4. chronological out-of-sample incremental forecast performance **only if separately authorized**;
5. economic usefulness only after statistical usefulness survives and only under a later, distinct strategy protocol.

Do not jump directly from a regression coefficient to a trading rule.

## 12. Rejection conditions for incremental predictive usefulness

R04-A should be classified **REJECTED / NOT USEFUL FOR THIS PROJECT** if any preregistered primary condition fails. Proposed rejection conditions are:

1. **Data infeasibility:** dated futures and synchronized spot cannot be reconstructed with known expiry, timestamps and point-in-time availability.
2. **Construction ambiguity:** constant-maturity/annualization choices cannot be specified without materially outcome-dependent discretion.
3. **Timing leakage:** basis uses settlement, index or revised information that was unavailable at the registered decision time.
4. **No incremental signal:** adding basis does not improve the registered primary forecast metric relative to the frozen spot-only baseline in the authorized chronological test.
5. **Unstable sign/effect:** the registered basis coefficient reverses materially across predeclared venue/construction checks without a pre-specified explanation.
6. **Robustness failure:** the result disappears under the approved alternative raw-contract versus constant-maturity construction, where both are feasible.
7. **Venue dependence:** the apparent effect exists only on a venue that is inaccessible, defunct, or structurally incomparable to the current research universe.
8. **Retrospective event dependence:** the result requires choosing crash dates, basis thresholds or regimes after examining future outcomes.
9. **Multiplicity failure:** significance appears only after searching many horizons, venues, maturities or target definitions without correction/ledger accounting.
10. **No temporal persistence:** the effect appears only in the original 2019–2022-style period and fails the separately authorized later chronological evaluation.

A rejection is a valid research result. Do not rescue the idea by switching to perpetual funding, changing the maturity, changing the crash threshold, or selecting a different venue after seeing outcomes.

## 13. Stress-test / robustness matrix to preregister before any run

Keep the first run small. Suggested robustness dimensions, to be frozen in advance:

| Dimension | Primary | Registered robustness |
| --- | --- | --- |
| Predictor | 1m dated basis | 3m dated basis only as secondary |
| Basis construction | constant-maturity | raw contract / fixed DTE window if feasible |
| Asset | BTC | ETH replication after freeze |
| Target | next-30d spot return | future skew, future vol, 90d return |
| Baseline | 7d return + 30d return + 30d vol | reduced baseline with lagged return only |
| Venue/reference | one prequalified primary source | one independent qualified source |
| Frequency | daily or predeclared non-overlap | alternative only if preregistered |
| Inference | one frozen method | one predeclared sensitivity |
| Market regime | no hindsight labels | calendar-defined subperiods only |

This matrix is intentionally small to avoid reproducing the project's earlier multiple-testing problem.

## 14. Evidence cards

### R04-C01 — Crypto carry was historically large and time-varying

```yaml
claim_id: R04-C01
source_id: Schmeling_Schrimpf_Todorov_2023_BIS1087
review_status: full_text_reviewed
source_locator: abstract; Section 2; Table 1
claim_paraphrase: BTC/ETH dated-futures basis was large and persistent in the paper's 2019-2022 sample, with strong time variation across 1m and 3m constant maturities.
evidence_type: empirical
market_and_sample: BTC/ETH, daily, March 2019-January 2022 main sample; exchange-specific shorter histories
limitations_and_contradictions: historical market structure; constant-maturity construction partly vendor-defined
proposed_project_application: use dated basis as a candidate market-state variable
falsification_or_rejection_condition: no incremental future-spot information under frozen current-data protocol
decision: supported_as_historical_prior
```

### R04-C02 — High basis predicted future downside outcomes in the study

```yaml
claim_id: R04-C02
source_id: Schmeling_Schrimpf_Todorov_2023_BIS1087
review_status: full_text_reviewed
source_locator: Section 3.4; Equation 7; Table 8
claim_paraphrase: Higher 1m BTC basis was associated with lower subsequent spot returns and more negative realized skew at 1m/3m horizons, with significance varying by venue/target.
evidence_type: predictive regression
market_and_sample: BTC, OKEx and CME, historical working-paper sample
limitations_and_contradictions: overlapping observations; persistent predictor; shorter CME sample; not a modern OOS test; no binary crash target
timing: Carry_t -> future realized target
proposed_project_application: preregister an incremental lagged-basis test versus spot-only baseline
decision: supported_as_prior_not_current_edge
```

### R04-C03 — Carry-arbitrage is not risk-free in practice

```yaml
claim_id: R04-C03
source_id: Schmeling_Schrimpf_Todorov_2023_BIS1087
review_status: full_text_reviewed
source_locator: Section 3.3; Figure 5; Table 5
claim_paraphrase: Cash-and-carry positions can suffer large mark-to-market losses and liquidation risk before convergence, especially under leverage and margin constraints.
evidence_type: strategy-risk analysis
limitations_and_contradictions: historical margin regimes and before-cost Sharpe calculations are not current execution assumptions
proposed_project_application: do not infer an executable arbitrage strategy from a positive basis
decision: supported_guardrail
```

### R04-C04 — Final published version adds robustness and replication assets

```yaml
claim_id: R04-C04
source_id: Schmeling_Schrimpf_Todorov_2026_ManagementScience
review_status: applicability_assessed
source_locator: publisher abstract + online appendix; Table A.3 bear-market sample
claim_paraphrase: The final publication preserves the core carry/limits-to-arbitrage mechanism, provides supplemental robustness including a 2021-2023 bear-market exercise, and lists replication files.
evidence_type: peer_reviewed_publication + supplement
limitations_and_contradictions: replication package itself not audited due download timeout; final-version sample/coefficients must not be mixed with 2023 version without tagging
proposed_project_application: treat final version as source update and replication lead, not as silent replacement of the playbook source
decision: retained_with_version_separation
```

## 15. What R04 does and does not authorize

### Completed by R04

- full-text extraction of the 2023 BIS working paper;
- sample, venue, maturity, timing and control extraction;
- correct interpretation of "crash" as continuous downside/stress measures rather than one binary definition;
- identification of constant-maturity/annualization replication gaps;
- dated-futures versus perpetual-funding separation;
- review of core robustness evidence;
- 2026 publication and supplemental-version reconciliation;
- repository deduplication check;
- current data-feasibility assessment;
- project data dictionary;
- bounded R04-A preregistration proposal;
- explicit rejection conditions.

### Not authorized / not completed

- no current derivatives market-data outcomes were queried or inspected;
- no original INFORMS replication package was successfully downloaded/audited;
- no provider entitlement or paid dataset was purchased;
- no constant-maturity series was constructed;
- no regression was run on project data;
- no basis threshold was optimized;
- no strategy P&L was calculated;
- no futures or perpetual trade was simulated or executed;
- no leverage/shorting permission was added;
- no protected Validation/OOS partition was accessed;
- no AMS-DEP experiment, gate or frozen specification was changed;
- no repository commit was made.

## 16. Final R04 status and handoff

**R04 COMPLETE — DATED CRYPTO FUTURES BASIS IS A CREDIBLE HISTORICAL STRESS/PREDICTIVE CANDIDATE, BUT CURRENT INCREMENTAL PREDICTIVE USEFULNESS IS UNRESOLVED AND REQUIRES A SEPARATELY AUTHORIZED, PREREGISTERED DATA-EXPANSION TEST.**

The paper gives a substantially stronger research basis than simply trying a funding-rate signal. It supplies a concrete forward-timing hypothesis, plausible mechanism, historically documented downside association, and important negative guardrails about margin/liquidation risk. At the same time, its historical sample and partially vendor-defined constant-maturity construction mean the project should not assume the effect survives today.

**Immediate next playbook research task: R05 — Selection and Backtest Overfitting.**

R04-A remains a proposed future derivatives-data experiment and must not be executed until the data source, exact basis formula, timing contract, evaluation partition and statistical method are prospectively frozen and separately authorized.

## Source register

1. Schmeling, M., Schrimpf, A. & Todorov, K. (2023). **Crypto Carry.** BIS Working Paper No. 1087. `https://www.bis.org/publications/working-paper-1087-crypto-carry`
2. Schmeling, M., Schrimpf, A. & Todorov, K. (2026). **Crypto Carry.** *Management Science*, published online 6 May 2026. DOI: `10.1287/mnsc.2024.05069`.
3. Management Science online appendix for `10.1287/mnsc.2024.05069`.
4. Coin Metrics, **Market Data Overview** and API v4 documentation. Current documentation reviewed 2026-09-20.
5. CME Group, cryptocurrency futures settlement and historical/continuous price-series documentation. Current documentation reviewed 2026-09-20.
