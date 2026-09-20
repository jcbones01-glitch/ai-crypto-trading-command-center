# Oxford Analytica Intake — Geopolitical and Regulatory Scenario Framework

**Project:** AI Crypto Trading Command Center  
**Review date:** 2026-09-20  
**Playbook section:** Oxford Analytica intake  
**Status:** COMPLETE FOR PUBLIC-SOURCE INTAKE DESIGN — NO PROPRIETARY OXFORD ANALYTICA REPORT REVIEWED

## 1. Scope and authority

The project playbook identifies Oxford Analytica as a model for disciplined geopolitical and regulatory scenario intake. This document implements that intake discipline without claiming affiliation with Oxford Analytica and without claiming access to its proprietary Daily Brief or client research.

Public discovery source reviewed:

- Oxford Analytica Foundation: https://foundation.oxan.com/

The Foundation describes an impartial, expert, geopolitical advisory and interdisciplinary research mission. It is not a substitute for proprietary Oxford Analytica reports.

No proprietary Oxford Analytica report was retrieved or quoted in this work package.

This artifact does **not**:

- establish a trading edge;
- convert political or regulatory news into a directional BTC/ETH signal;
- authorize a backtest;
- access Validation or OOS;
- alter AMS-DEP V2;
- authorize derivatives trading;
- authorize paper or live trading.

Its purpose is to define how geopolitical/regulatory events may later be encoded as auditable **scenario context**.

---

## 2. Mandatory intake record

For every future geopolitical or regulatory source, record:

```yaml
scenario_source_id:
source_class: # proprietary_report | official_primary | public_research | secondary_analysis
title:
author_if_stated:
publisher:
publication_timestamp_utc:
retrieved_at_utc:
jurisdiction:
forecast_horizon:
source_url:
source_version_or_hash:

claim:
  exact_claim_paraphrase:
  evidence_supporting_claim:
  uncertainty_stated_by_source:
  contested_or_conditional_points:

mechanism:
  observable_policy_or_market_mechanism:
  affected_entities:
  affected_markets_or_venues:
  possible_access_effect:
  possible_liquidity_effect:
  possible_transfer_effect:
  possible_compliance_effect:

verification:
  primary_official_sources:
  effective_date:
  implementation_status:
  superseded_or_withdrawn:
  later_updates:

research_boundary:
  return_direction_inferred: false
  strategy_signal_authorized: false
  backtest_authorized: false
  validation_oos_authorized: false
  live_trading_authorized: false

next_action:
decision:
decision_reason:
```

A narrative without an observable mechanism is not sufficient for project use.

---

## 3. Scenario classification

Use four separate classes so political/regulatory context is not mixed with statistical evidence.

### Class A — Enacted or formally scheduled policy change

A law, rule, regulation, sanction, licensing regime, or official implementation date exists.

Permitted project use:
- annotate the research calendar;
- define market-access or compliance scenarios;
- identify venues/assets that may become unavailable;
- define prospective stress tests.

Not permitted:
- infer a return direction without a separately specified empirical model.

### Class B — Official proposal or consultation

A government/regulator has proposed or consulted on a change, but implementation is not final.

Required label:
`POLICY_PROPOSAL_NOT_ENACTED`

Never backfill the final outcome into earlier timestamps.

### Class C — Geopolitical risk scenario

Examples:
- sanctions expansion;
- capital controls;
- cross-border payment restrictions;
- banking restrictions;
- exchange-license loss;
- asset blocking;
- internet/payment infrastructure disruption.

The scenario must specify observable triggers and a falsification/closure condition.

### Class D — Expert or advisory forecast

A report forecasts a future development.

Required:
- exact forecast horizon;
- probability/uncertainty if stated;
- supporting evidence;
- later resolution status.

A forecast is not a fact and is not a trading signal.

---

# 4. Public-source pilot scenarios

These are **intake examples**, not Oxford Analytica findings.

## OA-PUBLIC-001 — UK crypto regulatory-perimeter transition

### Source record

**Primary official sources:**
- FCA, *A new regime for cryptoasset regulation*
- FCA, *PS26/18: Cryptoasset perimeter guidance*
- FCA, 2026 cryptoasset policy statements

URLs:
- https://www.fca.org.uk/firms/new-regime-cryptoasset-regulation
- https://www.fca.org.uk/publications/policy-statements/ps26-18-cryptoasset-perimeter-guidance
- https://www.fca.org.uk/publications/policy-statements/cryptoasset-regime

**Jurisdiction:** United Kingdom  
**Observed status as of 2026-09-20:** Formal future regulatory implementation path.

The FCA states that the new UK cryptoasset regime is expected to commence on **25 October 2027** and that final rules/guidance were published on **30 June 2026**. Perimeter guidance was published on **16 September 2026**.

### Observable mechanism

Potential mechanisms include:

- authorization requirements for firms carrying on regulated cryptoasset activities in or to the UK;
- compliance and prudential requirements;
- possible changes to which firms/venues can legally serve UK customers;
- admissions/disclosures and crypto market-abuse controls;
- operational preparation and licensing costs.

### Project relevance

Possible future use:
- venue-availability calendar;
- exchange-access risk flags;
- regulatory-transition stress scenario;
- execution-adapter eligibility rules.

### Prohibited inference

Do **not** encode:
`UK crypto regulation -> BTC goes up/down`

The official sources do not establish a directional BTC/ETH return effect.

### Closure condition

Update this scenario if:
- commencement date changes;
- implementing legislation/rules are amended;
- a venue's UK authorization status materially changes.

**Decision:** RETAIN_AS_MARKET_ACCESS_CONTEXT

---

## OA-PUBLIC-002 — U.S. sanctions and virtual-currency access

### Source record

**Primary official source:** U.S. Treasury, Office of Foreign Assets Control (OFAC)

Relevant sources:
- Sanctions Compliance Guidance for the Virtual Currency Industry
- OFAC Virtual Currency FAQs
- FAQ 646 on blocking digital currency
- FAQ 1250, published May 1, 2026, concerning Iranian digital asset exchanges

URLs:
- https://ofac.treasury.gov/recent-actions/20211015
- https://ofac.treasury.gov/faqs/topic/1626
- https://ofac.treasury.gov/faqs/646
- https://ofac.treasury.gov/faqs/1250

### Observable mechanism

OFAC states that U.S. sanctions obligations apply to virtual currency as they do to fiat currency.

Possible observable market-access effects include:

- blocked wallets/assets;
- prohibited transactions;
- venue/customer screening;
- rejected deposits or withdrawals;
- exchange or counterparty inaccessibility;
- additional compliance friction;
- forced changes to usable transfer routes.

OFAC FAQ 1250 states that Iranian digital asset exchanges meet the relevant definition of Iranian financial institutions and are blocked under the cited sanctions framework.

### Project relevance

This belongs primarily in:

- venue-access controls;
- legal eligibility filters;
- cross-venue fragmentation analysis;
- transfer-feasibility checks;
- operational-risk scenarios.

### Critical rule

A price on a sanctioned/inaccessible venue is **not executable opportunity evidence** for a U.S.-subject trading system merely because the quote exists.

This connects directly to R03's fragmentation safeguards.

### Prohibited inference

Do not infer that a sanctions action causes a particular BTC/ETH direction without a separate prospective empirical specification.

**Decision:** RETAIN_AS_ACCESS_AND_COUNTERPARTY_RISK_CONTEXT

---

## OA-PUBLIC-003 — Capital-flow restrictions and local crypto premia

### Sources

**Institutional framework:**
- IMF Integrated Policy Framework
- IMF Institutional View on capital flows

Research sources:
- IMF Working Paper 2024/133, *Crypto as a Marketplace for Capital Flight*
- IMF FinTech Note 2022/005, *Capital Flow Management Measures in the Digital Age: Challenges of Crypto Assets*
- IMF Working Paper 2024/085, *A Primer on Bitcoin Cross-Border Flows: Measurement and Drivers*

URLs:
- https://www.imf.org/en/topics/ipf-integrated-policy-framework
- https://www.imf.org/en/topics/capital-flows
- https://www.imf.org/en/publications/wp/issues/2024/06/28/crypto-as-a-marketplace-for-capital-flight-550966
- https://www.imf.org/en/publications/fintech-notes/issues/2022/05/09/capital-flow-management-measures-in-the-digital-age-516671
- https://www.imf.org/en/publications/wp/issues/2024/04/05/a-primer-on-bitcoin-cross-border-flows-measurement-and-drivers-547429

### Evidence classification

The IMF policy framework establishes that countries may use capital-flow management measures under specified circumstances.

The 2024 capital-flight paper is an IMF **working paper**; its authors' findings must not be represented as a formal IMF policy determination.

That paper reports evidence that, in markets with international transaction restrictions, local crypto premia can reflect demand for foreign currency and capital-control intensity.

### Observable mechanism

Potential mechanism:

`capital/FX restriction -> impaired cross-border fiat arbitrage -> local crypto demand imbalance -> local/global crypto price premium`

This is closely related to R03's fragmentation mechanism.

### Project relevance

Potential future descriptive use:
- compare local fiat-denominated crypto premia with documented capital-control episodes;
- test whether apparent cross-exchange arbitrage is actually non-transferable;
- identify regimes in which fiat convertibility assumptions fail.

### Required causal controls

Before any empirical use:

- policy effective timestamp;
- jurisdiction;
- legal scope;
- fiat convertibility;
- official/parallel FX rates;
- exchange accessibility;
- capital transfer limits;
- stablecoin conversion path;
- withdrawal/deposit restrictions;
- transaction costs.

### Prohibited inference

A local crypto premium is not automatically a tradable arbitrage and is not automatically evidence of future global BTC returns.

**Decision:** RETAIN_AS_FRAGMENTATION_AND_TRANSFER_CONTEXT

---

## OA-PUBLIC-004 — Market-access interruption template

**Status:** HYPOTHETICAL SCENARIO TEMPLATE, NOT A CURRENT EVENT CLAIM.

### Trigger examples

The scenario activates only after a verifiable event such as:

- exchange authorization suspended/revoked;
- sanctions designation;
- bank/payment-rail termination;
- fiat deposit/withdrawal suspension;
- crypto withdrawal suspension;
- jurisdictional prohibition;
- exchange geofencing;
- major communications/internet restriction affecting venue access.

### Required source hierarchy

1. regulator/government notice;
2. exchange/financial institution operational notice;
3. payment/banking provider notice;
4. reliable secondary reporting only as corroboration.

### State machine

```text
WATCH
  -> CONFIRMED_ANNOUNCEMENT
  -> EFFECTIVE
  -> PARTIAL_ACCESS
  -> RESTORED
  -> CLOSED
```

Every transition requires a timestamped source.

### Project effect

When `EFFECTIVE`, future execution research should be able to mark:

- venue unavailable;
- transfer path unavailable;
- fiat route unavailable;
- asset pair unavailable;
- stale/inaccessible quote excluded.

It should **not** automatically change a strategy's directional position.

**Decision:** RETAIN_AS_OPERATIONAL_SCENARIO_TEMPLATE

---

# 5. Anti-hindsight rules

The geopolitical scenario layer must obey these controls.

1. **No retrospective crisis labels.**  
   Do not label a period "crisis", "sanctions shock", or "capital-flight regime" because price subsequently moved.

2. **Timestamp the information set.**  
   Store when the source was published and when the policy/event became effective.

3. **Separate announcement from implementation.**  
   A proposed regulation, final rule, effective rule, and actual venue response are distinct events.

4. **Preserve uncertainty.**  
   If the source presents alternatives or conditional forecasts, preserve them.

5. **No directional return labels by analyst judgment.**  
   "Risk-off", "bullish", and "bearish" are not machine labels unless separately and prospectively defined.

6. **No source substitution.**  
   A media article cannot silently replace a missing official implementation notice.

7. **No inaccessible-venue economics.**  
   If regulation/sanctions prevents lawful access to a venue, its prices cannot be treated as executable for that system.

8. **No automatic strategy use.**  
   Scenario context enters a strategy only through a separate preregistered research object.

---

# 6. Event record for future quantitative use

A future machine-readable event should look like:

```yaml
event_id: OA-EVT-YYYY-NNN
scenario_class: A
jurisdiction: GB
topic: crypto_regulatory_perimeter

announcement_time_utc:
effective_time_utc:
known_to_system_time_utc:

source:
  type: official_primary
  publisher: FCA
  title:
  url:
  retrieved_at_utc:
  snapshot_sha256:

state:
  status: CONFIRMED_ANNOUNCEMENT
  probability: null

mechanism_flags:
  venue_access: true
  fiat_access: false
  transfer_restriction: false
  sanctions: false
  compliance_cost: true
  market_structure: true

affected_entities: []
affected_markets: []

research:
  directional_label: null
  signal_authorized: false
  development_test_authorized: false
  validation_oos_authorized: false
```

---

# 7. Relationship to existing research packages

## R03 — Exchange fragmentation

Highest overlap.

The Oxford-intake layer can explain why some exchange prices become inaccessible or non-transferable, but R03's synchronization, depth, fee, transfer, and venue-access requirements still determine whether a price difference is economically meaningful.

## R04 — Crypto carry

Regulatory/geopolitical context might later be used as a **predefined stress state**, but it must not be selected retrospectively because carry performed differently.

## R05 — Selection/backtest overfitting

Every tested geopolitical event definition, jurisdiction filter, lag, and scenario family must count in the global research-search ledger.

The scenario layer cannot become an unlimited source of hand-crafted regime labels.

## D01–D03

Data provenance applies equally here:

- publication timestamp;
- effective timestamp;
- source version;
- retrieval time;
- immutable snapshot;
- revisions/corrections;
- license.

---

# 8. Oxford Analytica source intake status

Current classification:

`PUBLIC_DISCOVERY_SOURCE_REVIEWED`

Not:

`PROPRIETARY_OXFORD_ANALYTICA_REPORT_REVIEWED`

If a genuine accessible Oxford Analytica report is later supplied or lawfully accessible, create a separate evidence card containing:

- report title;
- author if stated;
- publication timestamp;
- jurisdiction;
- forecast horizon;
- exact claim;
- supporting evidence;
- uncertainty;
- observable mechanism;
- relevant primary official sources;
- later resolution status.

Do not attribute any scenario in this artifact to Oxford Analytica.

---

# 9. Completion decision

**OXFORD ANALYTICA INTAKE: COMPLETE AS A GOVERNANCE/SCENARIO FRAMEWORK.**

What is established:

- a source hierarchy;
- a mandatory intake schema;
- separation of fact, proposal, scenario, and forecast;
- public-source pilot examples;
- anti-hindsight rules;
- a future machine-readable event schema;
- explicit links to R03/R04/R05 and data provenance.

What is **not** established:

- access to proprietary Oxford Analytica research;
- forecast accuracy;
- a geopolitical alpha factor;
- a directional BTC/ETH relationship;
- permission to backtest scenario variables;
- any trading authorization.

## Next playbook package

The next incomplete section is the **video queue**:

1. **V01 — MIT Adaptive Markets course / Andrew Lo**
2. **V02 — LSE Demystifying Cryptocurrency / Igor Makarov**
3. **V03 — MIT Finance, AI, and Human Behavior / Andrew Lo**

Video extraction must use actual accessible lecture/video content or transcript, preserve timestamps, connect claims to original research where possible, and mark inaccessible transcript segments as blocked rather than inventing them.
