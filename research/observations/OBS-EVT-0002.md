# OBS-EVT-0002 — Delayed CPI Crypto Response

## Classification

`OBSERVATION`

Not a hypothesis, model, backtest result, edge claim, validation result, or live result.

## Source evidence

- CPI timing manifest certification: `docs/GATE2_CPI_MANIFEST_CERTIFICATION_V1.md`
- Preregistered study: `docs/GATE2_CPI_EVENT_STUDY_PREREGISTRATION_V1.md`
- Evidence certification: `research/experiments/CPI_EVENT_STUDY_V1_CERTIFICATION.md`
- Evidence workflow run: `35426274987`
- Exact study commit: `3736517d60a00a4958f85e693e66bce1e18a8e05`
- Development only; Validation/OOS not accessed.

## Observation

Across 52 certified Development-period CPI releases, returns measured from the first full hourly bar beginning 30 minutes after release showed:

1. no material BTC short-horizon absolute-return elevation versus matched controls at 1h (`0.9776x`);
2. only modest ETH elevation at 1h (`1.0668x`);
3. lower event absolute returns than controls for both assets at 6h (BTC `0.7397x`, ETH `0.7672x`);
4. modestly larger event absolute returns at 24h (BTC `1.0727x`, ETH `1.1379x`);
5. no consistent cross-asset directional pattern.

## Relationship to OBS-EVT-0001

OBS-EVT-0001 found stronger short-horizon absolute movement around FOMC releases.

The CPI study does not cleanly reproduce that pattern. However, the event-study anchors differ: FOMC release times were on the hourly grid while CPI V1 begins 30 minutes after the official release.

Therefore this is evidence against a simple universal macro-release volatility rule, not a direct quantitative ranking of FOMC versus CPI impact.

## Interpretation

Macro-event identity appears potentially useful as **risk/intelligence context**, because different event classes show different response profiles.

No strategy is authorized.

## Follow-up rule

Do not retune CPI horizons, anchors, subgroups, or exclusions using these same 52 events.

The next independent test should certify a third event class before returns are examined. Employment Situation releases are the next candidate.

Validation/OOS remain locked.
