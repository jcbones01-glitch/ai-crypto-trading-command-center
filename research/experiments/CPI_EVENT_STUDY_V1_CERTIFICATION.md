# CPI Delayed Descriptive Event Study V1 — Evidence Certification

## Status

**COMPLETED DESCRIPTIVE DEVELOPMENT EVIDENCE — NO STRATEGY PROMOTION**

The preregistered CPI study completed successfully. It measures delayed post-release crypto returns beginning at the first full hourly bar after each xx:30 CPI release, so it deliberately excludes the first 30 minutes after release.

It does not authorize a trading hypothesis, Validation/OOS access, paper trading, or live execution.

## Reproducibility evidence

- Study workflow: `Gate 2 CPI Descriptive Event Study`
- Workflow run: `35426274987`
- Exact study/code commit: `3736517d60a00a4958f85e693e66bce1e18a8e05`
- Workflow conclusion: `success`
- Artifact ID: `10579665474`
- Artifact name: `gate2-cpi-event-study-v1`
- Artifact digest: `sha256:4abcd718235f50b43a31a5896cdea3f78c1f11259374f326731075afade415c8`
- Event-study JSON SHA-256: `f466226e2036d28340e43ab0e34738e04c3a46da82ea79defceac2ba31e2f039`
- Preregistration SHA-256: `d9ff4fdd2d2561c3b73d0e67b88d11b72b8a6756235c1925fa07b915d115f881`
- Frozen CPI manifest SHA-256: `927b61306dba19e08871f18ced0e9147a54a5b53c2ab4a9a03f7280672adedb7`
- Frozen FOMC manifest SHA-256: `8d50b8deff5a91c11880c896c7c02bf23fc917322a157ffae17a1404e11f70c1`
- CPI event dataset ID: `7773afbb02bbfff60031e3a8455ce119308b1d1b86c0b45adc43d54a6c1dc119`
- BTCUSDT dataset identity: `1590cf8e69ed757eeb6701a218d561448beb2eb6ea09dcd0ae31d15a8f5197cf`
- ETHUSDT dataset identity: `d35bf21e309820abc88090bad29601adc1d1ea6b31dcddf0b80d510af4cf542f`
- Validation/OOS accessed: `False`
- Anchor delay after certified release time: `30 minutes`
- Frozen horizons: `1h / 6h / 24h`
- Frozen control lags: `7 / 14 / 21 / 28 days`

## Frozen primary matched results

The primary analysis gives each CPI event equal weight and compares its event return with the mean of its eligible same-weekday/same-UTC-hour controls.

### BTCUSDT

| Horizon | Matched events | Event mean signed | Matched-control signed | Event mean abs | Matched-control abs | Abs-return ratio |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 52 | +0.0522% | -0.0167% | 0.6106% | 0.6246% | 0.9776x |
| 6h | 52 | -0.0566% | -0.2128% | 1.3520% | 1.8276% | 0.7397x |
| 24h | 51 | -0.5481% | -0.0170% | 3.4023% | 3.1718% | 1.0727x |

### ETHUSDT

| Horizon | Matched events | Event mean signed | Matched-control signed | Event mean abs | Matched-control abs | Abs-return ratio |
|---|---:|---:|---:|---:|---:|---:|
| 1h | 52 | +0.1695% | +0.0276% | 0.8944% | 0.8384% | 1.0668x |
| 6h | 52 | -0.1866% | -0.0084% | 1.6664% | 2.1720% | 0.7672x |
| 24h | 51 | -0.7932% | +0.2580% | 4.5628% | 4.0099% | 1.1379x |

All six preregistered asset/horizon results are retained regardless of sign.

## Eligibility and exclusions

The exclusion pattern is symmetric across BTCUSDT and ETHUSDT.

### Event observations

- 1h: 52 / 52 eligible and matched.
- 6h: 52 / 52 eligible and matched.
- 24h: 51 / 52 eligible and matched.
- The single 24h event exclusion crossed a certified continuity break.

### Controls

There were 208 candidate controls per asset/horizon before preregistered exclusions.

- 1h: 174 eligible.
  - 33 excluded because the full control interval was within 24 hours of a certified CPI/FOMC event.
  - 1 excluded because the certified market start timestamp was unavailable.
- 6h: 168 eligible.
  - 39 CPI/FOMC-proximity exclusions.
  - 1 unavailable certified market start.
- 24h: 167 eligible.
  - 39 CPI/FOMC-proximity exclusions.
  - 1 unavailable forward endpoint.
  - 1 unavailable certified market start.

No event or control was removed because of its return.

## Certified interpretation

### OBSERVATION A — FOMC short-horizon volatility pattern did not reproduce cleanly in delayed CPI data

The prior FOMC study observed materially elevated 1h absolute returns relative to controls:

- BTCUSDT: approximately `2.31x`
- ETHUSDT: approximately `1.67x`

The CPI delayed study does **not** show the same pattern:

- BTCUSDT 1h: `0.9776x`
- ETHUSDT 1h: `1.0668x`
- BTCUSDT 6h: `0.7397x`
- ETHUSDT 6h: `0.7672x`

Therefore the broad proposition that all major U.S. macro releases create elevated short-horizon crypto volatility is not supported by these two event classes as currently measured.

This is not a strict apples-to-apples replication because CPI begins 30 minutes after release while the hourly-grid FOMC study begins at an exact release-hour open.

### OBSERVATION B — modest 24h absolute-return elevation after CPI

At 24h, delayed CPI absolute-return ratios were modestly above controls:

- BTCUSDT: `1.0727x`
- ETHUSDT: `1.1379x`

This is descriptive only and does not establish a 24h volatility edge.

### OBSERVATION C — directional patterns are inconsistent and remain discovery-only

Signed CPI results vary by asset and horizon. They do not provide a consistent cross-asset directional rule.

No directional CPI strategy is authorized.

## Critical anti-hindsight boundary

All 52 Development CPI outcomes have now been consumed for discovery.

No subsequent rule derived from these results may be presented as independent preregistered evidence when tested on the same 52 events.

Immediate CPI reaction is also **not measured** by V1 because the first 30 minutes are excluded. Studying that interval requires a separately certified finer-frequency market dataset and a new preregistration written before inspecting those finer-frequency returns.

## Cross-event conclusion

The combined FOMC and CPI evidence supports continuing **macro-event timing as a risk/intelligence research family**, but it does not justify a general macro-event trading strategy.

The strongest current statement is:

> Different U.S. macro event classes appear to have different crypto response profiles. Event identity may therefore be useful context for risk and regime analysis, but event-class-specific behavior must be independently characterized before any trading hypothesis is created.

## Next permitted step

Use a third independent, first-party event class to test whether event-class-specific behavior persists.

The recommended next class is the U.S. Bureau of Labor Statistics **Employment Situation** release because it is a major scheduled U.S. macro release with explicit publication timing and is logically distinct from both FOMC policy statements and CPI inflation releases.

Source provenance and point-in-time timing must be certified before any crypto return analysis.

Validation/OOS, paper trading, live trading, leverage, and exchange credentials remain locked.
