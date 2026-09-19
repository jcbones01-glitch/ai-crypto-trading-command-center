# Gate 2 Cycle 8 — Market-State Layer Certification V1

## Certification result

**STATE_LAYER_READY**

Cycle 8 successfully created and verified the preregistered `AMS-V1` causal market-state layer.

This is an infrastructure certification only. It is **not** a trading-strategy promotion, profitability claim, or authorization to access Validation/OOS for strategy selection.

## Verified execution

- Repository branch: `gate2-research-foundation`
- Executing commit: `246d344807b2e9c88972e57e14f632e5d05c7f70`
- Checked-out commit recorded by artifact: `246d344807b2e9c88972e57e14f632e5d05c7f70`
- Workflow: `Gate 2 Cycle 8 Market State`
- Workflow run ID: `35432480012`
- Workflow conclusion: `success`
- Full test suite on PR: **137 passed**
- Dedicated AMS-V1 integrity tests: **passed**
- Artifact: `gate2-cycle8-market-state-results`
- Artifact ID: `10580994439`
- Artifact digest: `sha256:a761bdcd44fd2d9e5aea47776524c2ae730cd000c6afdc09111aaaf4b39cf407`
- State definition: `AMS-V1`
- Preregistration SHA-256: `6b119ca21521f1992ab49db7bc3245f985a8e50f8f0b88214bc6646d545593bf`

## Research firewall verification

The generated artifact explicitly records:

- `validation_or_oos_accessed: false`
- `strategy_pnl_calculated: false`
- `strategy_signals_generated: false`

No strategy from HYP-0001 through HYP-0025 was reopened, retuned, rescued, or relabeled.

## Dataset identities

### BTCUSDT

- Dataset identity: `1590cf8e69ed757eeb6701a218d561448beb2eb6ea09dcd0ae31d15a8f5197cf`
- Certified bars used: **38,179**
- Complete AMS-V1 state observations: **22,116**
- Complete-state fraction: **57.9271%**
- First complete state: `2017-10-07T23:00:00+00:00`
- Last complete state: `2021-12-31T23:00:00+00:00`
- Continuous research segments: **28**

### ETHUSDT

- Dataset identity: `d35bf21e309820abc88090bad29601adc1d1ea6b31dcddf0b80d510af4cf542f`
- Certified bars used: **38,179**
- Complete AMS-V1 state observations: **22,116**
- Complete-state fraction: **57.9271%**
- First complete state: `2017-10-07T23:00:00+00:00`
- Last complete state: `2021-12-31T23:00:00+00:00`
- Continuous research segments: **28**

The incomplete-state fraction is expected because each certified continuous segment must independently rebuild the causal 720-observation reference history. Warm-up is never carried across continuity breaks.

## State occupancy — descriptive observations

These are observations about the Development sample, not evidence of a trading edge.

### BTCUSDT

Volatility:
- VOL_LOW: 26.51%
- VOL_NORMAL: 53.41%
- VOL_HIGH: 20.08%

Activity:
- ACTIVITY_LOW: 23.68%
- ACTIVITY_NORMAL: 53.79%
- ACTIVITY_HIGH: 22.53%

Trend:
- TREND_BEAR: 12.24%
- TREND_NEUTRAL: 69.29%
- TREND_BULL: 18.47%

Observed composite states: **24 of at most 27**.

### ETHUSDT

Volatility:
- VOL_LOW: 22.83%
- VOL_NORMAL: 56.02%
- VOL_HIGH: 21.15%

Activity:
- ACTIVITY_LOW: 21.24%
- ACTIVITY_NORMAL: 51.75%
- ACTIVITY_HIGH: 27.01%

Trend:
- TREND_BEAR: 16.08%
- TREND_NEUTRAL: 60.51%
- TREND_BULL: 23.41%

Observed composite states: **26 of at most 27**.

## Cross-asset state agreement

Exact synchronized timestamps with complete state on both assets: **22,116**

- Volatility-state agreement: **67.13%**
- Activity-state agreement: **68.44%**
- Trend-state agreement: **70.23%**
- Full composite-state agreement: **36.41%**

These figures show that BTC and ETH often share broad conditions but frequently differ when all three state axes are considered together. This does not imply that disagreement or agreement predicts returns.

## Interpretation

Cycle 8 establishes a stable environmental vocabulary for future research:

`volatility state × activity state × trend state`

A future strategy may reference these states only through a new prospective preregistration.

The project must not use the Cycle 8 occupancy or agreement results to retroactively repair a failed strategy. A regime-aware trading rule is a new hypothesis and must define its state dependence before its Development backtest is treated as evidence.

## Certification decision

**Cycle 8 infrastructure certification: PASS — STATE_LAYER_READY**

Allowed next actions:
- use `AMS-V1` as a frozen causal feature layer in newly preregistered research;
- perform non-trading predictability/efficiency diagnostics prospectively;
- formulate new hypotheses with explicit economic mechanisms and state dependence;
- expand validated data sources before strategy research if the mechanism requires them.

Not allowed:
- Validation/OOS access for model selection;
- retroactive regime conditioning of HYP-0001 through HYP-0025;
- strategy P&L claims from Cycle 8;
- paper/live trading;
- autonomous parameter repair.
