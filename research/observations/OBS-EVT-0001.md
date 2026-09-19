# OBS-EVT-0001 — FOMC Release-Time Crypto Response

## Classification

`OBSERVATION`

Not a hypothesis, model, backtest result, edge claim, or live result.

## Source evidence

- Preregistered study: `docs/GATE2_FOMC_EVENT_STUDY_PREREGISTRATION_V1.md`
- Evidence certification: `research/experiments/FOMC_EVENT_STUDY_V1_CERTIFICATION.md`
- Evidence workflow run: `35424531997`
- Development only; Validation/OOS not accessed.

## Observation

Across the frozen 2017-09-20 through 2021-12-15 FOMC statement set:

1. BTCUSDT and ETHUSDT both showed larger mean absolute 1h returns around FOMC releases than deterministic prior same-time controls.
2. The absolute-return difference attenuated with horizon and was effectively absent for ETH at 24h.
3. Mean signed returns around FOMC events exceeded control means at all preregistered horizons for both assets.
4. Event medians were positive at every asset/horizon combination.

## Interpretation

The most defensible use of this observation today is as motivation for a broader **macro-event risk-intelligence** research family.

The directional pattern is discovery-derived and may not be promoted by backtesting the same FOMC Development events after the fact.

## Follow-up rule

Do not tune or subgroup FOMC events to improve this observation.

Next, certify a separate official macro event source and preregister its descriptive study before linking its event timestamps to crypto returns. Cross-event-class consistency can motivate later hypotheses, while inconsistency is also useful evidence.
