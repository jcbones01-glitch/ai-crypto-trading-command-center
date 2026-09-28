# What the Evidence Says About Trading

This file covers the plain facts. Each item gives the finding, what it means for us, and its source.

## 1. Most day traders lose money, and the few who don't earn little
- **Brazil (whole population, 2013–2015):** of everyone who began day trading Brazilian equity futures and kept going for more than 300 days:
  - 97% lost money;
  - only 1.1% earned more than the minimum wage;
  - the authors found no evidence that traders improved with experience.

  *Source:* Chague, De-Losso & Giovannetti, "Day Trading for a Living?" (2019/2020). [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3423101) · [RePEc](https://ideas.repec.org/p/spa/wpaper/2019wpecon47.html)
- **Taiwan (all stock day traders, 1992–2006):**
  - about 20% were profitable in a given year after fees;
  - fewer than 1% could predictably earn money year after year;
  - traders lost money before costs, and costs more than tripled their losses.

  *Sources:* Barber, Lee, Liu & Odean. [The Cross-Section of Speculator Skill](https://faculty.haas.berkeley.edu/odean/papers/day%20traders/The%20Cross-Section%20of%20Speculator%20Skill.pdf) · [Do Day Traders Rationally Learn About Their Ability?](https://faculty.haas.berkeley.edu/odean/papers/Day%20Traders/Day%20Trading%20and%20Learning%20110217.pdf)

**What this means:** day trading is not a reliable income. The rare winners are the exception, and even the best Brazilian trader earned modest amounts with huge swings.

## 2. Leveraged retail trading: most accounts lose
- EU regulators examined retail CFD accounts (leveraged trading) and found that **74–89% lost money**, with average losses of €1,600–€29,000 per client. Brokers there must now publish their own loss percentage.

  *Source:* ESMA product intervention, 2018. [ESMA press release](https://www.esma.europa.eu/press-news/esma-news/esma-agrees-prohibit-binary-options-and-restrict-cfds-protect-retail-investors)

**What this means:** leverage makes losses bigger and faster. Our rule: **no leverage.**

## 3. Even professionals rarely beat a simple index fund
- Over 15 years, about **89.5% of US large-cap active funds underperformed the S&P 500**. After 15 years, in no fund category did a majority of active managers beat their benchmark.

  *Source:* S&P Dow Jones Indices, [SPIVA Scorecards](https://www.spglobal.com/spdji/en/research-insights/spiva/) (as summarized by [Ritholtz](https://ritholtz.com/2025/05/the-data-on-active-large-cap-underperformance/)). *Note:* some researchers dispute parts of SPIVA's method ([WealthManagement](https://www.wealthmanagement.com/mutual-funds/new-report-challenges-methodology-in-long-running-active-scorecard)), but the overall direction is widely accepted.

**What this means:** a low-cost index fund is the baseline any strategy must beat. Most professionals don't beat it.

## 4. Backtests lie easily
- If you test many strategy variants and pick the best one, the chance that it's only lucky approaches certainty as the number of variants grows. This is the "probability of backtest overfitting."

  *Source:* Bailey, Borwein, López de Prado & Zhu, "The Probability of Backtest Overfitting," *Journal of Computational Finance* (2017). [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253)

**What this means:** count every idea you try, and test on data the strategy has never seen, ideally future data through paper trading.

## 5. Our own evidence (PSR-01B project, this repository)
- A careful BTC strategy (XGBoost forecasts plus a cost filter) passed its registered test against a weak baseline in 2018–2021.
- But it **lost badly to simply holding Bitcoin**: +166% vs +1008%, Sharpe 0.69 vs 1.73, with drawdowns of 43–55%.
- *Source:* this repository, Issue #110 audit; evidence commit `7ba09ce`.

**What this means:** we confirmed first-hand that a rigorous process mostly kills or shrinks strategies. That is normal, and it's valuable to know before risking money.
