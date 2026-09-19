# FOMC Descriptive Event Study V1 — Evidence Certification

## Status

**COMPLETED DESCRIPTIVE DEVELOPMENT EVIDENCE — NO STRATEGY PROMOTION**

The preregistered descriptive event study completed successfully. It does not authorize a trading hypothesis, Validation access, paper trading, or live execution.

## Reproducibility evidence

- Study workflow: `Gate 2 FOMC Descriptive Event Study`
- Workflow run: `35424531997`
- Exact code commit: `081971a12965929cc5405570b853cbdce38ecacc`
- Workflow conclusion: `success`
- Full-suite foundation workflow at same commit: `35424532040` — `success`
- Artifact ID: `10578668099`
- Artifact name: `gate2-fomc-event-study-v1`
- Artifact digest: `sha256:02c3a08be37850d88d99c48e071214d07a2610156ce5126c8b70cdc656daa223`
- Event-study JSON SHA-256: `ed9b0f37129432e22f6d97be6843cfdb5ae865703c0023a26d01c6e95c96978f`
- Preregistration SHA-256: `3fd430e3851d4dd54e0ab0dc971dd3a4d84d2e651a5bf7870b1d573f5a853ae8`
- Frozen FOMC manifest SHA-256: `8d50b8deff5a91c11880c896c7c02bf23fc917322a157ffae17a1404e11f70c1`
- FOMC event dataset ID: `fd5021aa2ff2f01ceaa2f5e060d08db8e0825cc27e1bde147e8eb5948ee14e11`
- BTCUSDT dataset identity: `1590cf8e69ed757eeb6701a218d561448beb2eb6ea09dcd0ae31d15a8f5197cf`
- ETHUSDT dataset identity: `d35bf21e309820abc88090bad29601adc1d1ea6b31dcddf0b80d510af4cf542f`
- Validation/OOS accessed: `False`

## Frozen V1 results

All returns are open-to-open market responses. Controls are the preregistered prior 7/14/21/28-day same-weekday/same-UTC-hour observations, subject to continuity and FOMC-proximity exclusions.

### BTCUSDT

| Horizon | Event N | Event mean | Control N | Control mean | Event positive | Control positive | Absolute-return ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1h | 37 | +1.0293% | 146 | -0.0716% | 70.27% | 46.58% | 2.3145x |
| 6h | 37 | +1.1120% | 146 | +0.3121% | 64.86% | 54.79% | 1.3443x |
| 24h | 36 | +1.1093% | 143 | +0.0242% | 52.78% | 46.85% | 1.1656x |

Median signed returns were +0.1866%, +0.6796%, and +0.3604% at 1h, 6h, and 24h respectively.

### ETHUSDT

| Horizon | Event N | Event mean | Control N | Control mean | Event positive | Control positive | Absolute-return ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1h | 37 | +0.9400% | 146 | -0.0098% | 56.76% | 50.68% | 1.6733x |
| 6h | 37 | +0.8836% | 146 | +0.3769% | 64.86% | 59.59% | 1.0678x |
| 24h | 36 | +1.0718% | 143 | -0.1384% | 55.56% | 46.15% | 0.9978x |

Median signed returns were +0.1821%, +0.9878%, and +0.6299% at 1h, 6h, and 24h respectively.

## Exclusions

For both assets:
- 1h and 6h: all 37 event observations were eligible; 146 of 148 controls were eligible.
- 24h: 36 of 37 event observations were eligible; 143 of 148 controls were eligible.

The 24h event exclusion crossed a certified continuity break. Control exclusions were caused only by the preregistered rules: unavailable certified start/end data, certified continuity breaks, or proximity within 24 hours of another FOMC event. No observation was removed because of its return.

## Certified interpretation

### OBSERVATION A — short-horizon absolute movement

At the 1h horizon, mean absolute returns around FOMC statements were larger than frozen controls for both assets:
- BTCUSDT: `2.3145x`
- ETHUSDT: `1.6733x`

The absolute-return difference attenuated at longer horizons. By 24h, the ratio was approximately `1.1656x` for BTC and `0.9978x` for ETH.

This is evidence that FOMC releases may be useful as a **short-horizon risk/intelligence context**, not evidence of a profitable volatility strategy.

### OBSERVATION B — signed returns

Mean signed event returns exceeded matched-control means at 1h, 6h, and 24h for both assets, and event median signed returns were positive at every frozen asset/horizon combination.

This is exploratory Development evidence only. It is not independently confirmatory.

## Critical anti-hindsight boundary

All 37 Development FOMC outcomes have now been observed.

Therefore a strategy such as `buy BTC/ETH after an FOMC statement and hold 1h/6h/24h` **cannot be retroactively treated as preregistered Development evidence on these same events**.

A future directional FOMC hypothesis would require genuinely independent evidence, such as a prospectively frozen future research window or another valid independent design. Validation and locked OOS remain inaccessible for rescuing a discovery-derived rule.

## Limitations

- No inferential significance test was preregistered or performed.
- No scheduled/emergency subgroup was selected.
- No policy-stance, surprise, hawkish/dovish, sentiment, or text classification was used.
- Macro regime and other contemporaneous news may confound event returns.
- Controls are deterministic historical matches, not randomized experiments.
- The study does not include transaction costs because it is not a trading simulation.
- Historical statement text vintage remains uncertified for NLP/LLM use.

## Next research direction

The next permitted research step is to test whether the **macro-release risk-context observation generalizes to a separate official event class**, rather than mining the same FOMC events further.

Consumer Price Index releases from the U.S. Bureau of Labor Statistics are the next source candidate because BLS maintains archived releases with explicit embargo/release timestamps. Source provenance and point-in-time semantics must be certified before any CPI/crypto return analysis.
