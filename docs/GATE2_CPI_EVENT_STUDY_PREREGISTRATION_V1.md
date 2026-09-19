# CPI descriptive event study preregistration V1

Written after timing-only source certification and before any CPI-linked crypto
return calculation. Classification: DESCRIPTIVE STUDY, not a strategy or edge.
Question: are delayed post-CPI absolute returns descriptively elevated relative
to historical weekday/time controls? FOMC motivated this question; CPI-specific
return values have not been inspected. The broader research program has already
used Development OHLCV data, so this is not an untouched market holdout.

## Frozen inputs

CPI dataset `7773afbb02bbfff60031e3a8455ce119308b1d1b86c0b45adc43d54a6c1dc119`,
52 releases; manifest `research/experiments/cpi_development_manifest_v1.json`.
FOMC timing dataset `fd5021aa2ff2f01ceaa2f5e060d08db8e0825cc27e1bde147e8eb5948ee14e11`
is used only to exclude contaminated controls. BTCUSDT and ETHUSDT certified
Development identities remain those in the existing FOMC loader. The market
loader may read only `[2017-08-17, 2022-01-01)` monthly archives. No Validation,
OOS, forecast values, CPI numeric values, text features, or classifications.

## Hourly-grid decision made before returns

All CPI timestamps are at xx:30 UTC. Define anchor a = the next full UTC hour.
Return at horizon h is `open(a+h)/open(a)-1`, h in {1,6,24} hours. Preserve the
true event timestamp separately. No rounding down, interpolation, candle-close
substitution, or assumed 08:30 price. This measures delayed post-release returns
from 30 minutes after release and deliberately misses the first 30 minutes.
The same event cannot be retested with a different anchor to improve results.
Immediate reaction requires a separate finer-frequency certified dataset and
new preregistration; it is not answered here.

## Controls and missingness

For each event and horizon, candidate control anchors are a minus 7,14,21,28
days (same weekday and UTC hour). Exclude out-of-Development intervals, missing
endpoints, non-positive prices, or continuity-break crossings using the existing
certified hourly helper. Also exclude a control when any certified CPI or FOMC
release lies within 24 hours of any part of its return interval, inclusive.
This interval-aware contamination check is frozen before results.

Include an event in the primary comparison only if its own return and at least
one control are eligible. Each matched event has equal weight: compare its
signed/absolute return with the mean signed/absolute return of its eligible
controls. Record every control, event and exclusion, and control count. Report
unmatched event summaries separately; no imputations or post-hoc exclusions.
Controls reused across events and overlapping horizons are dependent, not
independent replications.

## Frozen reporting

For each asset/horizon report matched pair count, means of event and matched
control signed returns, means of event and matched control absolute returns,
absolute-return ratio (null for zero denominator), and signed/absolute differences.
Also report all eligible-event descriptive summaries (mean/median signed and
absolute return and positive fraction) and pooled eligible controls, explicitly
secondary. No p-values, confidence-based promotion, optimized horizons,
subgroups, directional rules, emergency splits, or parameter searches.

These comparisons are associations. Simultaneous releases, time-of-day effects,
market regimes and dependent controls limit attribution. Existing FOMC evidence
has different anchoring and pooling: compare only qualitatively, never claim an
apples-to-apples ratio ranking or causal validation. All six CPI asset/horizon
results must be reported regardless of sign. This run consumes the 52 CPI
Development events for discovery; no subsequent directional test on these same
events may be presented as independent preregistered validation.

## Authority

No strategy promotion, Validation/OOS access, paper trading or live trading.
After the run, record an OBSERVATION and decide whether further independent
macro-event timing research is warranted. No thresholds may be changed to rescue
a result. Code corrections require disclosure and retained run lineage.
