# Gate 2 Cycle 7 Closeout

## Status

Cycle 7 is complete. No Development candidate is promoted to Validation.

- GitHub Actions run: `35423704263`
- Evidence commit: `9e6661c88b263ab6e79e9380ee37529730a12494`
- Workflow conclusion: `success`
- Evidence artifact: `gate2-cycle7-results`
- Artifact ZIP digest: `sha256:7154d0c12cf38e1ca17436de375f68e72fca2396b30b9c0a582cf83c167ca1bd`
- Evidence JSON SHA-256: `a0122d00ec6f6e3b057a52503cc3bfb71346d7990e17c6b649be48e683bda764`
- Preregistration SHA-256: `c9ddc30c6ddeb25339d0e2f966ff0231ad482e651a7f01dabfe370fd5577b995`
- Validation/OOS accessed by experiment: `False`

## Certified Development datasets

- BTCUSDT dataset identity: `1590cf8e69ed757eeb6701a218d561448beb2eb6ea09dcd0ae31d15a8f5197cf`
- ETHUSDT dataset identity: `d35bf21e309820abc88090bad29601adc1d1ea6b31dcddf0b80d510af4cf542f`
- Source integrity: `SOURCE VERIFIED`
- Research certification: `VALID WITH DOCUMENTED EXCLUSIONS`

## Decisions

### HYP-0023 — Rolling 24h Abnormal-Return Continuation

Decision: `REJECT`.

Baseline compound return:
- BTCUSDT: -40.06%
- ETHUSDT: -60.06%

It failed parameter-neighborhood, fee/slippage, timing, regime, sample-stability, asset-transferability, and protocol-eligibility requirements.

### HYP-0024 — Volatility-Contraction Breakout Continuation

Decision: `REJECT`.

Baseline compound return:
- BTCUSDT: +68.63%
- ETHUSDT: +105.98%

This is an interesting Development observation, but it is not eligible for Validation.

Mandatory failures:
- strongest fee/slippage stress: BTCUSDT compound return -20.01%; fee/slippage dimension failed;
- regime requirement: failed on both assets because the frozen qualifying-regime requirement was not met;
- protocol sample support: 284 combined completed trades versus the frozen minimum of 300.

Passing dimensions included parameter-neighborhood stability, execution-timing stress, leave-one-segment-out stability, concentration, drawdown/recovery, and cross-asset baseline profitability. These passing dimensions do not override any mandatory failure.

No threshold may be weakened and no parameter may be changed post hoc to rescue HYP-0024. Any future related hypothesis must be a new preregistered version and must remain Development-only until independently eligible.

### HYP-0025 — Bullish-Harami Multi-Hour Reversal

Decision: `REJECT`.

Baseline compound return:
- BTCUSDT: -85.47%
- ETHUSDT: -95.37%

It failed parameter-neighborhood, fee/slippage, timing, regime, sample-stability, asset-transferability, and protocol-eligibility requirements.

## Overall decision

`NO_DEVELOPMENT_PROMOTION`

The OHLCV-only Gate 2 research family has not produced a candidate satisfying all frozen promotion requirements. Validation and locked OOS remain untouched. No paper trading, live trading, leverage, exchange credentials, or autonomous capital deployment is authorized.

## Next research direction

The next research family should broaden the information set rather than weaken the evidence standard. The approved next foundation is point-in-time external event/intelligence data with deterministic provenance and leakage controls. AI interpretation and trading hypotheses come only after the raw event-data foundation is validated.
