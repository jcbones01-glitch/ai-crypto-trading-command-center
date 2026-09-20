# V02 — LSE “Demystifying Cryptocurrency” / Igor Makarov Review

**Project:** AI Crypto Trading Command Center  
**Playbook item:** V02  
**Review date:** 2026-09-20  
**Primary public source:** London School of Economics, *Demystifying Cryptocurrency*  
**Speaker:** Igor Makarov, LSE Department of Finance  
**LSE page publication date:** 2023-03-08  
**Playbook video URL:** https://www.youtube.com/watch?v=CkS9l65ILQI  
**Status:** COMPLETE FOR ACCESSIBLE SOURCE EXTRACTION; VIDEO TIMESTAMPS UNAVAILABLE

## Decision memo

**V02 materially reinforces R03’s market-structure conclusions and adds two useful adjacent lessons: Bitcoin ownership/mining concentration and the value/limits of blockchain-level data. It does not establish a trading strategy.**

The strongest project-relevant conclusions are:

1. crypto markets do not eliminate the familiar frictions of traditional finance;
2. decentralization of infrastructure does not imply dispersed ownership, dispersed mining power, frictionless competition, or integrated markets;
3. cross-venue price differences must be interpreted through access, capital movement, currencies, fees, settlement, and market segmentation — exactly the guardrails already built into R03;
4. public blockchain records create unusually rich research opportunities, but addresses are not automatically real-world entities and entity-resolution assumptions must be explicit;
5. concentration of ownership/mining is a market-structure fact worth monitoring, but it is not by itself a directional BTC/ETH signal.

No repository files, release gates, protected outcomes, Validation/OOS data, or trading permissions were changed by V02.

---

# 1. Source-access status

## Official LSE research-showcase page

Accessible:

https://www.lse.ac.uk/finance/news/research-showcase-demystifyingcryptocurrency

The official page contains:
- the title;
- speaker identity;
- publication date;
- a linked video;
- substantial first-person explanatory text from Makarov;
- references to his work with Antoinette Schoar.

## Video-access limitation

The playbook points to:

https://www.youtube.com/watch?v=CkS9l65ILQI

The direct YouTube page/caption transcript was not retrievable in the available web interface.

A separate LSE YouTube search listing surfaced under a different video ID, but that is not treated as a substitute for the playbook’s linked source.

Therefore:

- no video timestamp was invented;
- no unverified caption quotation was used;
- evidence cards use the official LSE webpage section/paragraph as source locator;
- claims are cross-checked against the underlying research papers where possible.

This follows the playbook rule: inaccessible transcript timing remains **UNAVAILABLE**, rather than estimated.

---

# 2. Underlying research cross-references

## R03 primary paper

Igor Makarov and Antoinette Schoar,  
**“Trading and Arbitrage in Cryptocurrency Markets,”**  
*Journal of Financial Economics* 135(2), 293–319 (2020).  
DOI: 10.1016/j.jfineco.2019.07.001

Journal page:
https://www.sciencedirect.com/science/article/pii/S0304405X19301746

The paper reports recurring cross-exchange cryptocurrency price deviations, larger deviations across countries than within countries, and evidence that constraints on arbitrage capital matter for market segmentation.

## Bitcoin network/concentration paper

Igor Makarov and Antoinette Schoar,  
**“Blockchain Analysis of the Bitcoin Market,”**  
NBER Working Paper 29396 (2021).  
DOI: 10.3386/w29396

https://www.nber.org/papers/w29396

The paper constructs an entity-linked Bitcoin database from public and proprietary sources and studies:
- transaction/network structure;
- miners and mining concentration;
- ownership concentration.

## DeFi paper

Igor Makarov and Antoinette Schoar,  
**“Cryptocurrencies and Decentralized Finance (DeFi),”**  
*Brookings Papers on Economic Activity*, Spring 2022, 141–215.

NBER working-paper record:
https://www.nber.org/papers/w30006

Brookings:
https://www.brookings.edu/articles/cryptocurrencies-and-decentralized-finance-defi/

This paper emphasizes that blockchain/DeFi can reduce some intermediation costs while still facing network effects, economies of scale, rents, governance problems, and regulatory challenges.

---

# 3. Evidence cards

## V02-C01 — Crypto market structure still contains familiar financial frictions

```yaml
claim_id: V02-C01
source_id: LSE-DEMY-2023
source_version: LSE research showcase page published 2023-03-08
review_status: reviewed
reviewed_at: 2026-09-20
source_locator:
  page_section: "this field essentially faces the same frictions that are found in traditional finance"
  timestamp_range: UNAVAILABLE_VIDEO_TRANSCRIPT
claim_paraphrase: >
  Makarov argues that the crypto/DeFi ecosystem still faces important frictions
  familiar from traditional finance; decentralization does not automatically
  remove the reasons financial infrastructure, market design, and regulation exist.
evidence_type: expert explanation linked to published research
market_and_sample: conceptual overview of cryptocurrency/DeFi markets
data_requirements: []
method_and_assumptions: []
reported_effect_and_uncertainty: not a quantified trading effect
limitations_and_contradictions:
  - explanatory interview material is not independent strategy evidence
  - the particular friction must be identified empirically before project use
replication_assets: []
proposed_project_application: >
  Treat market access, settlement, market segmentation, liquidity, ownership
  concentration, and regulatory constraints as explicit possible confounds.
existing_repo_overlap:
  - R03 exchange-fragmentation checklist
  - Oxford market-access scenario framework
  - D03 market-data qualification
causal_timing_requirements:
  - any friction/state variable must be observable at the research decision time
cost_and_execution_requirements:
  - fees
  - bid/ask
  - depth
  - capital-transfer feasibility
falsification_or_rejection_condition: >
  Do not retain a proposed friction as explanatory merely because it matches a
  narrative; require direct measurable evidence in the proposed study.
next_action: none; already incorporated into R03 architecture
decision: retain
decision_reason: strong conceptual support for existing R03 safeguards
```

---

## V02-C02 — Fragmentation is a limits-of-arbitrage problem, not “free money”

```yaml
claim_id: V02-C02
source_id: MAKAROV-SCHOAR-2020
source_version: JFE 2020 published article
review_status: reviewed
reviewed_at: 2026-09-20
source_locator:
  paper_sections:
    - introduction
    - arbitrage index / cross-region price deviations
    - implementation of arbitrage strategies
  video_timestamp_range: UNAVAILABLE_VIDEO_TRANSCRIPT
claim_paraphrase: >
  Cross-exchange crypto price differences can persist because capital cannot
  necessarily move frictionlessly between venues, countries, currencies, and
  settlement systems. A visible spread is not automatically an executable arbitrage.
evidence_type: empirical research
market_and_sample: transaction-level cryptocurrency exchange data; 34 exchanges across 19 countries in the published study
data_requirements:
  - synchronized venue prices
  - currencies and FX conversion
  - venue location/access
  - fees
  - transfer restrictions
  - executable depth
method_and_assumptions:
  - cross-market price comparison
  - market segmentation / limits-of-arbitrage interpretation
reported_effect_and_uncertainty: >
  Published paper reports large recurrent deviations, larger across countries than
  within countries; historical magnitudes are sample-specific and must not be
  treated as current expected profits.
limitations_and_contradictions:
  - historical exchange landscape differs materially from today
  - some venues may be inaccessible or defunct
  - gross price spread is not net executable profit
replication_assets:
  - BTC spot
  - potentially ETH spot in a separately specified replication
proposed_project_application: >
  Preserve R03's staged filter:
  raw spread -> synchronized prices -> executable bid/ask -> freshness -> FX ->
  depth -> fees -> venue access -> inventory -> transfer/recycling feasibility.
existing_repo_overlap:
  - R03 Exchange Fragmentation Review
causal_timing_requirements:
  - synchronized contemporaneous quotes
  - stale-quote rejection
cost_and_execution_requirements:
  - maker/taker costs
  - spread
  - depth
  - settlement/transfer delay
  - fiat/stablecoin conversion
falsification_or_rejection_condition: >
  Reject an arbitrage interpretation when the spread disappears after synchronization,
  costs, access, depth, or transfer constraints.
next_action: no new experiment authorized
decision: retain
decision_reason: directly corroborates R03
```

---

## V02-C03 — Bitcoin ownership is concentrated

```yaml
claim_id: V02-C03
source_id: LSE-DEMY-2023 / NBER-W29396
source_version: LSE page 2023; NBER working paper 2021
review_status: reviewed
reviewed_at: 2026-09-20
source_locator:
  lse_section: discussion of large and concentrated Bitcoin participants
  nber_source: "Blockchain Analysis of the Bitcoin Market"
  timestamp_range: UNAVAILABLE_VIDEO_TRANSCRIPT
claim_paraphrase: >
  Makarov and Schoar's entity-linked analysis finds Bitcoin ownership to be highly
  concentrated. The LSE showcase summarizes the finding as the top 10,000 investors
  controlling more than 30% of Bitcoin in circulation.
evidence_type: empirical blockchain/entity-resolution study
market_and_sample: Bitcoin blockchain and entity-linked data through the study period, including end-2020 ownership analysis
data_requirements:
  - raw blockchain transactions
  - address clustering/entity resolution
  - intermediary classification
method_and_assumptions:
  - address-to-entity linkage using public/proprietary sources
  - algorithms separating entities and activity types
reported_effect_and_uncertainty: >
  Concentration estimates depend on entity-resolution methodology and the study's
  historical sample; they are not a current 2026 ownership estimate.
limitations_and_contradictions:
  - addresses are not people
  - exchange/custodian addresses can represent many beneficial owners
  - proprietary-source components affect reproducibility
  - concentration alone does not imply a return forecast
replication_assets:
  - BTC
proposed_project_application: >
  Treat ownership concentration as possible market-ecology context only after a
  point-in-time, reproducible measurement source is qualified.
existing_repo_overlap:
  - Adaptive Markets market-ecology concept
  - D02 Coin Metrics/on-chain qualification
causal_timing_requirements:
  - concentration measure must be computable using information available at the historical decision time
cost_and_execution_requirements: []
falsification_or_rejection_condition: >
  Do not use concentration as a predictive feature unless a separate preregistered
  test establishes incremental information.
next_action: future data-source feasibility only
decision: retain_as_context
decision_reason: meaningful market-structure evidence, not a strategy signal
```

---

## V02-C04 — Bitcoin mining capacity is concentrated

```yaml
claim_id: V02-C04
source_id: NBER-W29396
source_version: 2021 working paper
review_status: reviewed
reviewed_at: 2026-09-20
source_locator:
  paper_topic: mining concentration
  lse_summary: top 50 miners often control more than half of aggregate capacity
  timestamp_range: UNAVAILABLE_VIDEO_TRANSCRIPT
claim_paraphrase: >
  The study finds substantial concentration in Bitcoin mining capacity; its historical
  analysis reports periods in which fewer than roughly 50 miners were sufficient to
  account for about half of mining capacity, with concentration changing over time.
evidence_type: empirical blockchain/mining-entity study
market_and_sample: Bitcoin mining network during the paper's historical sample
data_requirements:
  - miner/pool identification
  - block-production data
  - entity-resolution assumptions
method_and_assumptions:
  - miner identification and inferred capacity shares
reported_effect_and_uncertainty: >
  Historical concentration is time-varying and should not be represented as a current
  2026 mining-share estimate.
limitations_and_contradictions:
  - pool identity and underlying miner identity differ
  - geographic/miner composition changes
  - concentration does not establish price predictability
replication_assets:
  - BTC
proposed_project_application: >
  Possible future network-security/market-ecology context, not a direct trading feature.
existing_repo_overlap:
  - Adaptive Markets market-ecology framework
causal_timing_requirements:
  - historically observable miner classification required
cost_and_execution_requirements: []
falsification_or_rejection_condition: >
  Do not encode miner concentration as a return signal without a separate mechanism
  and preregistered empirical test.
next_action: none in current playbook phase
decision: retain_as_context
decision_reason: useful structure evidence but not immediately actionable
```

---

## V02-C05 — Public blockchains provide unusually rich data, but identity is imperfect

```yaml
claim_id: V02-C05
source_id: LSE-DEMY-2023 / NBER-W29396
source_version: LSE page 2023
review_status: reviewed
reviewed_at: 2026-09-20
source_locator:
  lse_section: "I saw unique opportunities for Finance research"
  timestamp_range: UNAVAILABLE_VIDEO_TRANSCRIPT
claim_paraphrase: >
  Blockchain transaction records make a large amount of activity publicly observable,
  creating unusual opportunities to study investor/participant behavior; however,
  blockchain addresses do not directly reveal the real people or entities behind them.
evidence_type: methodological/research-design observation
market_and_sample: Bitcoin/blockchain research
data_requirements:
  - blockchain transaction history
  - address clustering
  - entity labels where justified
method_and_assumptions:
  - mapping addresses to entities is inferential and source-dependent
reported_effect_and_uncertainty: not a quantitative return effect
limitations_and_contradictions:
  - pseudonymity
  - custodial aggregation
  - clustering errors
  - retrospective entity labels can create point-in-time leakage
replication_assets:
  - BTC
  - possibly other chains with chain-specific methods
proposed_project_application: >
  Any future on-chain feature must include a point-in-time entity-resolution rule and
  must not use labels that became known only later.
existing_repo_overlap:
  - D02 point-in-time data qualification
  - R05 leakage/search accounting
causal_timing_requirements:
  - label availability time
  - observation time
  - methodology version
cost_and_execution_requirements: []
falsification_or_rejection_condition: >
  Reject a historical feature if entity labels or classifications rely on future
  information unavailable at the time being simulated.
next_action: carry into any future on-chain data qualification
decision: retain
decision_reason: directly useful data-provenance guardrail
```

---

## V02-C06 — DeFi does not automatically eliminate rents or competition constraints

```yaml
claim_id: V02-C06
source_id: MAKAROV-SCHOAR-DEFI-2022
source_version: BPEA 2022 / NBER w30006
review_status: reviewed
reviewed_at: 2026-09-20
source_locator:
  paper: "Cryptocurrencies and Decentralized Finance (DeFi)"
  lse_context: discussion of traditional-finance frictions and infrastructure
  timestamp_range: UNAVAILABLE_VIDEO_TRANSCRIPT
claim_paraphrase: >
  DeFi may reduce some intermediary transaction costs, but network effects,
  economies of scale, and other endogenous constraints can still create rents,
  concentration, governance challenges, and a role for regulation.
evidence_type: institutional/market-structure analysis
market_and_sample: cryptocurrency and DeFi architecture
data_requirements: []
method_and_assumptions:
  - economic analysis of competition, intermediation, and blockchain architecture
reported_effect_and_uncertainty: not a strategy-return estimate
limitations_and_contradictions:
  - broad institutional analysis does not specify a tradable feature
  - DeFi protocols differ materially across chains and eras
replication_assets: []
proposed_project_application: >
  Avoid assuming that "decentralized" means frictionless, competitive, or free of
  concentration; qualify protocol-level market structure separately.
existing_repo_overlap:
  - Oxford/regulatory scenario framework
  - market-ecology research direction
causal_timing_requirements: []
cost_and_execution_requirements: []
falsification_or_rejection_condition: >
  Any protocol-specific claim must be tested against the actual protocol and period.
next_action: none for current spot research
decision: retain_as_institutional_context
decision_reason: useful for architecture/risk interpretation, not alpha
```

---

# 4. Cross-reference to R03

V02 **supports rather than changes** R03.

R03's key discipline remains:

```text
observed venue price gap
        |
        v
synchronize timestamps
        |
        v
use executable bid/ask
        |
        v
remove stale quotes
        |
        v
normalize currency / stablecoin
        |
        v
check available depth
        |
        v
apply fees
        |
        v
verify legal/operational venue access
        |
        v
verify inventory
        |
        v
verify transfer / settlement / capital recycling
        |
        v
only then discuss executable spread
```

Makarov's LSE explanation that crypto faces the same kinds of financial frictions is consistent with this architecture.

Nothing in V02 justifies bypassing any R03 filter.

---

# 5. What V02 adds beyond R03

R03 is primarily about **cross-exchange fragmentation and executability**.

V02 adds two adjacent market-structure dimensions:

### A. Participant concentration

Ownership and mining can be highly concentrated even in a decentralized protocol.

Potential future relevance:
- market ecology;
- counterparty/systemic concentration;
- network-security states.

But no predictive test is authorized.

### B. Entity-resolution discipline

Blockchain transparency is valuable, but a public address is not automatically a known investor.

Potential future research must record:
- clustering algorithm/version;
- label source;
- time the label became available;
- whether the historical feature can be reconstructed without hindsight.

---

# 6. Negative evidence / things not learned from V02

V02 does **not** establish:

- that Bitcoin is currently concentrated at the exact historical percentages reported in the 2021 study;
- that miner concentration predicts Bitcoin returns;
- that ownership concentration predicts returns;
- that regulation increases or decreases BTC/ETH prices;
- that cross-exchange arbitrage is currently profitable;
- that historical exchange premia remain at 2017–2018 magnitudes;
- that public blockchain data are automatically causal or point-in-time safe;
- that DeFi eliminates traditional market frictions;
- that any of these observations authorize strategy development.

---

# 7. Source-quality note

The LSE showcase is useful because it presents Makarov's own explanation of his research.

For project evidence hierarchy:

1. **Published paper / technical working paper** for empirical claims;
2. **LSE showcase** for interpretation and research framing;
3. **Video interview** for explanation only.

Where the showcase summarizes a numerical empirical result, the underlying research paper remains the primary evidence source.

---

# 8. Final classification

**V02: COMPLETE FOR ACCESSIBLE SOURCE EXTRACTION**

### Supported for project use

- crypto market structure contains persistent financial frictions;
- fragmentation/access constraints matter to apparent arbitrage;
- ownership/mining concentration can coexist with decentralized infrastructure;
- blockchain data create unusual research opportunities;
- entity resolution and point-in-time labeling are material methodological risks;
- R03's execution/transfer/access safeguards remain appropriate.

### Unresolved

- exact playbook-video timestamps;
- current 2026 ownership/mining concentration;
- current magnitude of cross-venue/cross-country fragmentation;
- any predictive relationship between concentration and returns.

### Not supported

- a new trading strategy;
- reopening closed hypotheses;
- changing AMS-DEP;
- Validation/OOS access;
- paper/live trading.

## Next playbook item

**V03 — MIT: “Finance, AI, and Human Behavior,” Andrew Lo**

Playbook objective:

> Extract implications for AI-assisted decision-making and human oversight.

Required boundary:

Educational/interview material can inform governance and hypothesis design, but cannot by itself validate an AI trading strategy or authorize autonomous capital deployment.
