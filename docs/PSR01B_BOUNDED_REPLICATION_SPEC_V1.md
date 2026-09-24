# PSR-01B — Bounded Development-Only Cost-Aware BTC Mechanism Replication Specification V1

**Status:** PROPOSED FOR INDEPENDENT SPECIFICATION REVIEW — NO IMPLEMENTATION OR P&L AUTHORIZED  
**Parent source review:** Issue #86 — `PSR01_SOURCE_IDENTITY_UNRESOLVED`  
**Parent design review:** Issue #88 — `APPROVE_PSR01B_BOUNDED_DESIGN_DRAFTING`  
**Machine registration:** `research/governance/psr01b_bounded_spec_v1.json`

## 1. Scientific claim boundary

PSR-01B is **not** an exact reproduction of the Bysik & Ślepaczuk (2026) reported futures backtest.

It is a prospectively frozen, declared-deviation test of one mechanism:

> whether the paper's cost-aware execution rule improves realised net returns relative to naive sign execution when both rules consume the exact same forecast stream.

The instrument is deliberately changed to **Binance Spot BTCUSDT** because the paper's stated Binance USD-M futures history begins before the documented launch of Binance Futures. The unresolved source identity remains recorded in Issue #86.

A positive PSR-01B result would support only this bounded statement:

> under the frozen PSR-01B Spot reconstruction, cost-aware execution improved the same XGBoost forecast stream relative to naive sign execution during the registered Development-only period.

It would not establish reproduction of the paper's reported futures performance, benchmark dominance, live profitability, leverage suitability, or persistence after 2021.

## 2. Authorization boundary

This specification does **not** authorize:

- implementation;
- empirical feature generation;
- model training;
- forecast generation;
- strategy P&L;
- any observation at or after 2022-01-01T00:00:00Z;
- AMS-DEP Validation/OOS access;
- derivatives execution;
- leverage;
- paper trading;
- live trading.

The next action after this document is independent specification review.

## 3. Source universe

The source universe is exactly:

- provider: Binance Public Data;
- market: Spot;
- symbol: BTCUSDT;
- timeframe: 1 hour;
- timezone: UTC;
- monthly klines archives;
- first archive: `BTCUSDT-1h-2017-12.zip`;
- last archive: `BTCUSDT-1h-2021-12.zip`;
- 49 archives total;
- raw/burn-in start: `2017-12-01T00:00:00Z`;
- modelling start: `2018-01-01T00:00:00Z`;
- hard end, exclusive: `2022-01-01T00:00:00Z`.

The exact 49 archive SHA-256 pins are frozen in the machine registration. They are inherited from the already-audited Development BTC parent checksum map.

No PSR-01B source adapter may request, stage, inspect, hash, summarize, or otherwise expose a timestamp >= `2022-01-01T00:00:00Z`.

## 4. Walk-forward folds

The design contains exactly 11 sequential folds.

Each fold is:

- 12 calendar months training;
- 3 calendar months validation;
- 3 calendar months test;
- 3 calendar months forward step.

Fold schedule:

| Fold | Train | Validation | Test |
|---|---|---|---|
| 1 | 2018-01-01 → 2019-01-01 | 2019-01-01 → 2019-04-01 | 2019-04-01 → 2019-07-01 |
| 2 | 2018-04-01 → 2019-04-01 | 2019-04-01 → 2019-07-01 | 2019-07-01 → 2019-10-01 |
| 3 | 2018-07-01 → 2019-07-01 | 2019-07-01 → 2019-10-01 | 2019-10-01 → 2020-01-01 |
| 4 | 2018-10-01 → 2019-10-01 | 2019-10-01 → 2020-01-01 | 2020-01-01 → 2020-04-01 |
| 5 | 2019-01-01 → 2020-01-01 | 2020-01-01 → 2020-04-01 | 2020-04-01 → 2020-07-01 |
| 6 | 2019-04-01 → 2020-04-01 | 2020-04-01 → 2020-07-01 | 2020-07-01 → 2020-10-01 |
| 7 | 2019-07-01 → 2020-07-01 | 2020-07-01 → 2020-10-01 | 2020-10-01 → 2021-01-01 |
| 8 | 2019-10-01 → 2020-10-01 | 2020-10-01 → 2021-01-01 | 2021-01-01 → 2021-04-01 |
| 9 | 2020-01-01 → 2021-01-01 | 2021-01-01 → 2021-04-01 | 2021-04-01 → 2021-07-01 |
| 10 | 2020-04-01 → 2021-04-01 | 2021-04-01 → 2021-07-01 | 2021-07-01 → 2021-10-01 |
| 11 | 2020-07-01 → 2021-07-01 | 2021-07-01 → 2021-10-01 | 2021-10-01 → 2022-01-01 |

The held-out test union is the only empirical evaluation series.

## 5. Forecast target and timing

The target is the paper's one-hour-ahead log return:

`r_(t+1) = log(C_(t+1) / C_t)`.

Information through the completed close at time `t` is used to generate a forecast of `r_(t+1)`.

The position selected from that forecast is applied to the next close-to-close market return.

This is an **idealized paper-accounting timing convention**. It is not a claim that a real order can be computed, transmitted, filled, and confirmed at exactly the same close with zero latency.

## 6. Two mandatory missing-data arms

Both arms must be implemented and reported. Neither may be dropped after outcomes are known.

### 6.1 PAPER_FILL

Reconstruct a complete hourly grid.

For each internal missing timestamp:

- open = previous accepted close;
- high = previous accepted close;
- low = previous accepted close;
- close = previous accepted close;
- volume = 0;
- `synthetic = true`.

A leading gap without a previous accepted close hard-fails.

### 6.2 PROJECT_GAP_PRESERVING

No synthetic bar is created.

No target or feature may cross a continuity gap.

Rolling state resets at every gap.

A row is feature-eligible only after at least 336 contiguous valid hours are available after the most recent gap.

EGARCH state is also reset at a gap as defined below.

## 7. Feature tier

The first PSR-01B experiment uses exactly one feature tier:

`OHLCV + TA + EGARCH`

This corresponds to 28 deployed predictors:

- 15 OHLCV-derived predictors;
- 10 selected TA-related predictors;
- 3 EGARCH predictors.

Because the manuscript does not publish enough detail to reconstruct all 28 inputs exactly, the missing definitions below are **project-defined declared deviations**. They must never be represented as author-supplied definitions.

### 7.1 Warm-up

For every fold, feature construction begins exactly 744 hours before the fold's training start.

Only training-window rows enter fitting or feature selection.

### 7.2 Fifteen OHLCV-derived predictors

The 15 predictors are frozen as:

1. `RET_1 = log(C_t/C_(t-1))`
2. `OPEN_GAP = log(O_t/C_(t-1))`
3. `HIGH_PREVCLOSE = log(H_t/C_(t-1))`
4. `LOW_PREVCLOSE = log(L_t/C_(t-1))`
5. `CLOSE_OPEN = log(C_t/O_t)`
6. `HIGH_LOW = log(H_t/L_t)`
7. close location in the bar;
8. body fraction of bar range;
9. upper-wick fraction;
10. lower-wick fraction;
11. `log1p(volume)`;
12. one-hour log volume change using `V+1`;
13. volume / 24-hour mean volume − 1;
14. `log1p(close × volume)`;
15. one-hour log change in typical price `(H+L+C)/3`.

For zero-range bars, range-normalized bar-shape variables equal zero.

No predictor scaling is applied for XGBoost.

### 7.3 TA candidate pool

Windows are exactly:

`{3, 6, 12, 24, 48, 72, 168, 336}` hours.

Indicator families:

- RSI;
- ROC;
- distance to SMA;
- normalized MACD;
- MACD histogram;
- ATR ratio;
- rolling return standard deviation;
- Bollinger position;
- VWAP deviation;
- OBV slope;
- MFI.

Six return lags are:

`{1, 2, 3, 6, 12, 24}` hours.

The resulting candidate pool is exactly 94 features.

### 7.4 Ten reconstruction selection groups

The manuscript states that 94 candidates are mapped into 10 configured groups but does not disclose that mapping. PSR-01B freezes the following reconstruction before outcomes:

1. RSI;
2. ROC;
3. distance-to-SMA;
4. MACD + MACD histogram;
5. ATR ratio + rolling standard deviation;
6. Bollinger position;
7. VWAP deviation;
8. OBV slope;
9. MFI;
10. lagged returns.

Exactly one candidate is selected from each group.

### 7.5 Training-only feature selection

The 12-month training window is divided into four consecutive three-calendar-month blocks.

Within each block:

- use only rows whose predictor and aligned next-hour target are in that block;
- require at least 100 finite aligned rows for candidate eligibility;
- rank eligible candidates by descending absolute Spearman correlation with the next-hour return;
- resolve equal correlations by lexical feature name.

Average each candidate's ordinal rank across the four blocks.

The candidate with the lowest average rank wins its group; final ties are lexical.

If a group has no candidate eligible in all four blocks, the fold hard-fails.

### 7.6 Indicator formulas

The machine registration freezes the exact formulas.

Key project choices include:

- Wilder RSI and ATR;
- MACD fast span `max(2,floor(w/2))`, slow span `w`, signal span `max(2,floor(w/3))`;
- population standard deviations, `ddof=0`, for rolling feature calculations;
- OLS slope for OBV;
- deterministic zero-denominator behavior;
- causal resets at gaps.

## 8. EGARCH

Candidate orders are exactly:

- (1,1,1);
- (2,1,1);
- (1,1,2);
- (2,1,2).

Use:

- constant conditional mean;
- Student-t innovations;
- training returns in percentage units, `100 × log return`;
- lowest training AIC;
- lexicographic order tie-break.

Output predictors:

1. conditional volatility;
2. log conditional volatility;
3. standardized residual.

Parameters are fit only on training and held fixed through validation/test.

No validation/test EGARCH refit is permitted.

For PROJECT_GAP_PRESERVING, EGARCH recursion resets at a gap to the fitted unconditional log-variance proxy with standardized residual zero; no residual or variance state may propagate across the missing interval.

## 9. XGBoost and model selection

Only XGBoost is allowed.

Only MSE is allowed.

Only validation loss-best selection is allowed.

Optuna uses TPE with exactly 50 trials per fold and no pruner.

Search ranges are frozen to the paper's reported ranges:

- max depth: integer 2–4;
- learning rate: log-uniform 0.005–0.03;
- estimators: integer 1000–2500;
- min child weight: 10–40;
- subsample: 0.60–0.90;
- column sample by tree: 0.60–0.90;
- L1: log-uniform 1e-4–0.05;
- L2: log-uniform 1–40.

Fixed XGBoost settings include:

- `reg:squarederror`;
- histogram tree method;
- one thread;
- early-stopping patience 50.

### 9.1 Target standardization

During tuning:

- compute training target mean/std from training only;
- standardize training target;
- evaluate validation MSE in that same training scale.

For final refit:

- recompute target mean/std from combined train+validation;
- retrain on combined train+validation;
- inverse-transform test forecasts back to raw log-return units before any trading rule is applied.

A zero target standard deviation hard-fails.

### 9.2 Final retraining

After the winning trial is chosen:

- preserve its hyperparameters;
- set final estimator count to `best_iteration + 1`;
- if early stopping never triggered, use the sampled estimator count;
- retrain once on combined train+validation;
- do not early-stop final refit;
- apply once to held-out test.

## 10. Forecast identity firewall

For each missing-data arm and fold, exactly one final forecast vector is generated.

Its SHA-256 must be recorded.

Both:

- BASELINE_SIGN; and
- COST_AWARE

must consume the exact same forecast-vector bytes/logical values.

The execution rules may not trigger separate tuning, feature selection, refitting, or hyperparameter selection.

## 11. Trading rules

Mode: long-only.

Transaction cost:

`c = 0.001` per unit turnover.

Cost-aware threshold:

`lambda = 2.0`.

Desired position:

- 1 if raw-unit forecast > 0;
- 0 otherwise.

Baseline execution always moves to the desired position.

Cost-aware execution moves only when:

`abs(forecast) > lambda × c × abs(desired_position − previous_position)`.

Otherwise it keeps the previous position.

Net return:

`position_t × (exp(realized_log_return_(t+1)) − 1) − c × abs(position_t − previous_position)`.

## 12. Fold position accounting

Every test fold begins in cash:

`position_previous = 0`.

No position is inherited from the previous fold.

At the end of every test fold, any open position is forcibly liquidated to cash and the exit cost is charged to the final test return record after the final held market return.

This prevents a free reset across model changes.

Turnover includes the forced liquidation.

A **completed trade** is one long episode:

`0 → 1 ... 1 → 0`.

A forced terminal liquidation may complete the final trade.

## 13. Benchmarks

Benchmarks are contextual only. They are not the primary success gate.

### Buy-and-hold

Within each fold:

- enter long from cash at the first eligible test forecast origin;
- charge `c=0.001`;
- remain long;
- liquidate at fold end and charge `c=0.001`.

### 24-hour momentum

Desired long position = 1 only when cumulative log return over the previous 24 contiguous completed hours is positive; otherwise 0.

Use the same proportional transaction cost and fold reset/liquidation rules.

No cost-aware filter is applied to the momentum benchmark.

In the gap-preserving arm, remain flat until 24 contiguous prior hours are available after a gap.

## 14. Performance metrics

Use the paper's definitions.

For finite evaluation returns `r_t`:

`ARC = prod(1+r_t)^(8760/N)-1`.

`ASD = sqrt(8760) × sample_std(r_t, ddof=1)`.

Annual risk-free rate:

`r_f = 0.042`.

Sharpe:

`(ARC - 0.042) / ASD`.

Also report maximum drawdown, turnover, completed-trade count, fold-level returns, and fold-level Sharpe.

For PROJECT_GAP_PRESERVING, `N` is the number of finite accepted evaluation-return records. Missing/gap rows are not silently inserted as zero returns.

## 15. Primary inferential test

Primary differential:

`d_t = r_t(COST_AWARE) - r_t(BASELINE_SIGN)`.

Primary statistic:

mean hourly net-return differential.

Primary block length:

168 hours.

Bootstrap replications:

10,000.

The 24-hour and 72-hour block lengths are secondary robustness diagnostics only.

### 15.1 Segment-respecting bootstrap

Bootstrap blocks may not cross:

- fold boundaries; or
- continuity gaps.

Each registered contiguous fold/segment is circularly block-resampled independently back to its original length.

Resampled segments are then concatenated in the registered fold/segment order.

For the one-sided primary test, center the observed differential by subtracting its observed pooled mean before resampling.

Alternative:

`mean(COST_AWARE − BASELINE_SIGN) > 0`.

Raw p-value:

`(1 + # bootstrap centered means >= observed mean) / 10001`.

A 95% percentile interval from uncentered paired bootstrap draws is also reported.

Sharpe-difference bootstrap evidence is complementary, not a mandatory pass gate.

## 16. Multiple testing

There are exactly two primary hypotheses:

1. PAPER_FILL mean differential;
2. PROJECT_GAP_PRESERVING mean differential.

Apply Holm step-down correction across these two raw one-sided p-values at alpha 0.05.

Registered tie-break order:

1. PAPER_FILL;
2. PROJECT_GAP_PRESERVING.

The 24h/72h robustness diagnostics are not added to the primary family and cannot rescue failure at 168h.

## 17. Replication decision

Return:

`BOUNDED_H2_REPLICATION`

only if **all** of the following hold in both missing-data arms:

1. observed mean cost-aware minus baseline net return > 0;
2. Holm-adjusted primary 168h one-sided p-value <= 0.05;
3. cost-aware turnover < baseline turnover;
4. cost-aware completed trades >= 20;
5. cost-aware Sharpe − baseline Sharpe > 0.

Otherwise:

`BOUNDED_H2_NOT_REPLICATED`.

The manuscript itself uses a 20-trade minimum for formal interpretation. PSR-01B additionally freezes the operational meaning of a trade as one completed long episode.

A failure closes this registered experiment. It may not be rescued inside PSR-01B by changing:

- lambda;
- transaction cost;
- features;
- feature reconstruction;
- model;
- selector;
- folds;
- missing-data arms;
- bootstrap family.

Any such change requires a new registered experiment.

## 18. Stochastic reproducibility

Model root:

`2026092401`.

Bootstrap root:

`2026092402`.

Seeds are generated by NumPy `SeedSequence` and the first uint32 child value.

Separate deterministic namespaces are frozen for:

- Optuna arm/fold;
- XGBoost arm/fold/trial;
- final XGBoost arm/fold/selected trial;
- bootstrap arm/block length.

All numerical-library and model threads are fixed to one.

## 19. Runtime

Proposed frozen runtime:

- Ubuntu 24.04 GitHub runner;
- Python 3.12.14;
- NumPy 2.2.6;
- SciPy 1.15.3;
- pandas 3.0.6;
- XGBoost 3.4.1;
- Optuna 5.0.0;
- arch 8.0.0;
- statsmodels 0.15.0.

BLAS/OpenMP/NumExpr thread counts are all one.

These versions are specification inputs. Any required version change before implementation must return to independent review before empirical execution.

## 20. Future governance

If this specification is independently approved, the next lifecycle is:

1. bounded implementation only;
2. synthetic/offline tests only;
3. exact implementation freeze;
4. independent implementation review;
5. immutable reviewed-candidate anchor;
6. separate execution-authorization review;
7. explicit manual confirmation;
8. one-shot execution claim;
9. only then PSR-01B Development source read/model execution;
10. fail-closed relock;
11. independent result review.

No source read, model fitting, forecast generation, or P&L is authorized by this specification draft.
