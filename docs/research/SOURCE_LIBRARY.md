# Research source library — 2026-09-20

Status: **literature and data-source context only**. This index records reviewed material and open qualifications. It does not authorize an experiment, alter a frozen specification, access protected samples, or authorize trading.

Base inspected: `adaptive-markets-research` at `6431e9995ed3c904b673603b662506692d370539`. The machine gate at that head authorizes **V2 synthetic calibration only**; holdout, empirical BTC/ETH AMS-DEP work, Validation/OOS, P&L and trading remain blocked. Recheck the gate before any future action.

The companion reports in this folder contain evidence cards, source locators, assumptions, negative findings and proposed application boundaries. A completed review is not a validated signal.

| ID | Primary source or provider | Review | Decision and boundary |
| --- | --- | --- | --- |
| R01 | [Shao, dependent wild bootstrap (2010)](https://doi.org/10.1198/jasa.2009.tm08744) | [Bootstrap applicability](R01_Bootstrap_Applicability_Review.md) | Adjacent theory, not a theorem certifying the frozen AMS-DEP design; synthetic calibration remains essential. |
| R02 | [Cont, Kukanov & Stoikov, order-book events (2014)](https://doi.org/10.1093/jjfinec/nbt003) | [Order-flow replication/data feasibility](R02_Order_Flow_Replication_and_Data_Feasibility_Review.md) | Contemporaneous price explanation does not show subsequent-return predictability; event fidelity remains to be qualified. |
| R03 | [Makarov & Schoar, crypto arbitrage (2020)](https://doi.org/10.1016/j.jfineco.2019.07.001) | [Exchange fragmentation](R03_Exchange_Fragmentation_Review.md) | Historical cross-venue spreads do not establish currently accessible executable arbitrage. |
| R04 | [Schmeling, Schrimpf & Todorov, Crypto Carry](https://www.bis.org/publ/work1087.htm) | [Carry and market stress](R04_Crypto_Carry_and_Market_Stress_Review.md) | Dated-futures basis and perpetual funding differ; incremental spot predictive value remains untested. |
| R05 | [Bailey et al., backtest overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) | Review reported complete in playbook; companion report unavailable in supplied materials | Search/exposure ledger and selection-inference compatibility remain unresolved; no report reproduced here. |
| D01–D03 | [ALFRED](https://fred.stlouisfed.org/docs/api/fred/alfred.html), [Coin Metrics community](https://github.com/coinmetrics/data), [Coin Metrics market data](https://docs.coinmetrics.io/market-data/market-data-overview) | [Data feasibility](D01_D03_Data_Source_Feasibility_Review.md) | Availability time, coverage, revision policy, licensing and entitlement require dataset-level verification. |
| OA | [Oxford Analytica Foundation](https://foundation.oxan.com/) and public policy sources | [Geopolitical scenario intake](Oxford_Analytica_Intake_Geopolitical_Scenario_Framework.md) | No proprietary Oxford Analytica report reviewed; scenario framing supplies no alpha claim. |
| V01 | [MIT Adaptive Markets course](https://ocw.mit.edu/courses/15-481x-adaptive-markets-financial-market-dynamics-and-human-behavior-fall-2022/) | [Course review](V01_MIT_Adaptive_Markets_Course_Review.md) | Educational framework, no crypto strategy validation; some exact timestamps unavailable. |
| V02 | [LSE cryptocurrency lecture](https://www.lse.ac.uk/finance/news/research-showcase-demystifyingcryptocurrency) | [Lecture review](V02_LSE_Demystifying_Cryptocurrency_Review.md) | Accessible institutional descriptions and primary papers reviewed; video timestamps/captions unverified. |
| V03 | [MIT Finance, AI, and Human Behavior](https://ocw.mit.edu/courses/15-481x-adaptive-markets-financial-market-dynamics-and-human-behavior-fall-2022/resources/mit-economist-andrew-w-lo-on-finance-ai-and-human-behavior/) | [Lecture review](V03_MIT_Finance_AI_and_Human_Behavior_Review.md) | Decision support and human oversight; no autonomous trading authority. |

[Full research playbook](AI_Trading_Research_Playbook.md) records evidence states, the review queue and the project firewalls.

## Foundational context, separate from trading evidence

[Satoshi Nakamoto, *Bitcoin: A Peer-to-Peer Electronic Cash System*](https://bitcoin.org/bitcoin.pdf) is useful to understand the network's transaction and consensus design. Its white paper does not specify exchange order books, forecast returns, or demonstrate a trading edge. Review it as protocol background before treating any on-chain metric as a point-in-time market feature.

## Next integration decisions

1. Retrieve and inspect the missing R05 companion before adding it; do not infer its contents from the playbook.
2. For any proposed dataset, record original provider, publication/availability timestamp, revision policy, license, coverage, immutable snapshot hash, and authorized use.
3. For any new experiment, write a distinct prospective protocol and pass the current machine/research authorization process. Preserve negative results and the existing search history.
