# PSR-01B — Bounded Development-Only Cost-Aware BTC Mechanism Replication Specification V1

**Status:** REVISION 3 — SECOND REMEDIATION — PENDING RE-REVIEW — NO IMPLEMENTATION OR P&L AUTHORIZED  
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

## 3.1 Exact raw-row treatment and normalization

The 49 archive hashes alone are not the row-level data contract. Before PAPER_FILL or PROJECT_GAP_PRESERVING is constructed, PSR-01B must reuse the already-audited AMS-DEP V2 treatment-aware normalization stack **without modification**.

The following repository blobs are immutable inputs to PSR-01B:

- `src/research_core/ams_dep_treatment_aware_normalization_v2.py` — blob `8c257290ff04e726b53cafa433596311dcec32c4`;
- `src/research_core/data_quality.py` — blob `a8251c4288013d8264a85bb4cda44007459e1adf`;
- `src/research_core/data_quality_treatment_v2.py` — blob `f4876660fd88b91f0cfb9b9e87a8f9f09f1ddf19`;
- `src/research_core/data_ingestion.py` — blob `bbed81b3ffed215b04dc162368ef9866a4753875`;
- `src/research_core/archive_security.py` — blob `cf31519ead9538a59422c7d3dfdb1b3e9d43bb4b`;
- `src/research_core/data_interfaces.py` — blob `579b27b515d25ce69d565208416a88506286e534`.

Their authority is inherited from `research/governance/ams_dep_development_execution_v3.json`, blob `946dea1c852cd8a23d26d3a90ba99e88db5779a2`.

Before any archive is opened for empirical PSR-01B execution, runtime preflight must verify every listed Git blob SHA-1 and the upstream registration blob. Any mismatch hard-fails before source read.

The exact raw-row pipeline is:

1. verify each archive byte stream against its registered SHA-256;
2. in lexicographic archive order call the pinned `scan_archive(path,"BTCUSDT",checksum_verified=True)`;
3. build one pinned treatment manifest from exactly those 49 reports with research bounds `[2017-12-01T00:00:00Z, 2022-01-01T00:00:00Z)`;
4. call the pinned `normalize_development_archives("BTCUSDT", paths, reports, manifest)`;
5. use only the accepted normalized `MarketBar` rows returned by that function inside the registered source interval.

A raw physical row counts as observed only if that inherited scanner/normalizer accepts it. Explicitly localized treated anomalies are rejected exactly as the inherited contract specifies.

No PSR-01B code may:

- round or snap timestamps;
- interpolate or resample;
- repair OHLCV;
- repair duplicate/order defects;
- skip arbitrary parser/normalizer exceptions;
- create synthetic bars before the two missing-data arms diverge.

A **missing hour** is therefore an hourly label inside the registered interval absent from the accepted normalized timestamp set after this exact treatment. PAPER_FILL and PROJECT_GAP_PRESERVING begin only after that accepted-row set is frozen.

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

### 4.1 Exact endpoint eligibility

Binance kline timestamps are treated as UTC **bar-open labels**. A bar labeled `t` represents `[t,t+1h)`.

For any registered split `[S,E)`, a forecast origin `t` is eligible **if and only if**:

- `S <= t < E`; and
- the target bar label `t+1h` also satisfies `S <= t+1h < E`.

Therefore the last possible origin on a complete hourly grid is `E-2h`. The origin `E-1h` is excluded because its target bar belongs to the next split.

This same half-open endpoint rule governs:

- training targets;
- validation loss;
- held-out test forecasts and evaluation returns;
- feature-selection correlations inside each three-month selection block;
- benchmark evaluation records.

The final fold may not retain any origin whose target bar label is `>= 2022-01-01T00:00:00Z`.

For final XGBoost refitting, the combined train+validation dataset is the union of rows that were independently eligible under the original train split and the original validation split. A boundary-crossing row excluded earlier is not restored merely because the two windows are later combined.

## 5. Forecast target and timing

The target is the paper's one-hour-ahead log return:

`r_(t+1) = log(C_(t+1) / C_t)`.

Information through the completed close at time `t` is used to generate a forecast of `r_(t+1)`.

The position selected from that forecast is applied to the next close-to-close market return.

This is an **idealized paper-accounting timing convention**. It is not a claim that a real order can be computed, transmitted, filled, and confirmed at exactly the same close with zero latency.

## 6. Two mandatory missing-data arms

Both arms must be implemented and reported. Neither may be dropped after outcomes are known.

A **contiguous segment** is a maximal sequence of accepted bar-open labels spaced by exactly one hour.

Within a segment, the first bar has zero-based index `j=0` and counts as contiguous hour 1. At bar index `j`, exactly `j` one-hour transitions have been observed since the segment began.

The global feature-origin eligibility rule is:

`j >= 336`.

Thus the first deployable origin after a gap is the **337th bar** of the new contiguous segment. This guarantees 336 complete one-hour transitions for the longest return/change-based features.

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

At every gap:

- all rolling windows are discarded;
- RSI and ATR Wilder state are discarded;
- price EMAs and MACD signal EMA are discarded;
- OBV state is discarded;
- MFI loses its predecessor;
- lagged-return state is discarded;
- EGARCH latent histories are discarded and restarted under Section 8.

Window-specific first-valid indices inside a segment are:

- ROC(`w`) and lag return(`k`): `j>=w` or `j>=k`;
- distance-to-SMA(`w`), Bollinger(`w`), VWAP(`w`), OBV slope(`w`): `j>=w-1`;
- RSI(`w`), ATR(`w`), rolling return std(`w`), MFI(`w`): `j>=w`;
- recursive MACD exists earlier but cannot enter a deployed row before the global `j>=336` rule.

The global `j>=336` rule is controlling even when a shorter-window feature becomes mathematically available earlier.

### 6.3 Position and return accounting across a preserved gap

PROJECT_GAP_PRESERVING never carries a trading position across an interval for which market returns are deliberately absent.

Whenever an accepted-bar contiguous test segment ends and a later segment exists in the same fold:

1. after the final valid pre-gap market return is realized, force every strategy and benchmark position to cash at that final accepted close;
2. charge `c × abs(0-previous_position)` to that final valid pre-gap evaluation return record;
3. keep position exactly zero throughout the missing interval and the subsequent feature-recovery interval;
4. impute no market return during those omitted hours;
5. at the first post-gap model-eligible evaluation origin, set `previous_position=0`.

Therefore:

- BASELINE_SIGN resumes from cash using its ordinary desired-position rule;
- COST_AWARE resumes from cash and uses `previous_position=0` in its threshold turnover term;
- BUY_AND_HOLD re-enters long from cash at the first post-gap model-eligible origin and pays the ordinary entry cost;
- MOMENTUM_24H stays flat until both its 24-contiguous-hour signal history and the common model-origin eligibility are available, then applies its rule from cash.

Forced gap exits and later re-entries count in turnover and completed-trade accounting. A forced gap exit may complete a trade.

If the position is already flat, the forced-liquidation cost is zero.

If a segment end is also the fold end, apply only the ordinary fold terminal liquidation once; never double-charge both a gap exit and a fold exit.

## 7. Feature tier

The first PSR-01B experiment uses exactly one feature tier:

`OHLCV + TA + EGARCH`.

The deployed vector contains exactly 28 columns:

- 15 OHLCV-derived predictors;
- 10 selected TA-related predictors;
- 3 EGARCH predictors.

The manuscript does not publish enough detail to reconstruct all 28 inputs exactly. Every project-specified definition below is therefore a **declared reconstruction**, not an author-supplied formula.

### 7.1 Warm-up

For every fold, source feature construction may begin exactly 744 hours before the fold's training start. Only rows inside the registered training window enter model fitting or feature selection.

### 7.2 Fifteen OHLCV-derived predictors

Input domain: `O,H,L,C` must be finite and strictly positive and `V` must be finite and non-negative. Violation hard-fails.

The 15 columns are exactly:

1. `RET_1 = log(C_t/C_{t-1})`
2. `OPEN_GAP = log(O_t/C_{t-1})`
3. `HIGH_PREVCLOSE = log(H_t/C_{t-1})`
4. `LOW_PREVCLOSE = log(L_t/C_{t-1})`
5. `CLOSE_OPEN = log(C_t/O_t)`
6. `HIGH_LOW = log(H_t/L_t)`
7. `CLOSE_LOCATION = (2C_t-H_t-L_t)/(H_t-L_t)`
8. `BODY_FRAC = (C_t-O_t)/(H_t-L_t)`
9. `UPPER_WICK_FRAC = (H_t-max(O_t,C_t))/(H_t-L_t)`
10. `LOWER_WICK_FRAC = (min(O_t,C_t)-L_t)/(H_t-L_t)`
11. `LOG_VOLUME = log(1+V_t)`
12. `LOG_VOLUME_CHANGE = log((V_t+1)/(V_{t-1}+1))`
13. `VOLUME_SMA24_RATIO = V_t/mean(V_{t-23},...,V_t)-1`
14. `LOG_DOLLAR_VOLUME = log(1+C_tV_t)`
15. `TYPICAL_RETURN_1 = log(TP_t/TP_{t-1})`, with `TP_t=(H_t+L_t+C_t)/3`.

For columns 7–10, if `H_t=L_t`, the feature equals zero. For column 13, if the 24-hour volume mean is zero, the feature equals zero.

No predictor scaling is applied for XGBoost.

### 7.3 TA candidate pool

Windows are exactly:

`{3,6,12,24,48,72,168,336}` hours.

Indicator families are:

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

Six lagged returns are:

`{1,2,3,6,12,24}` hours.

Therefore the candidate pool is exactly `11×8+6=94`.

### 7.4 Exact recursive and rolling formulas

**RSI(`w`).** Let `delta_j=C_j-C_{j-1}`. At `j=w`, seed average gain and loss as the arithmetic means of the first `w` positive/negative changes. For `j>w`, use Wilder recursion `avg_j=(avg_{j-1}(w-1)+current_j)/w`. RSI is 100 when loss is zero but gain positive, 50 when both are zero, otherwise `100-100/(1+gain/loss)`. A gap requires a fresh `w`-change seed.

**ROC(`w`).** `C_t/C_{t-w}-1`.

**Distance to SMA(`w`).** `C_t/mean(C_{t-w+1},...,C_t)-1`.

**MACD(`w`).** Within each segment, for span `s`, initialize `EMA_s(0)=C_0`, then recurse `EMA_s(j)=alpha_s C_j+(1-alpha_s)EMA_s(j-1)` with `alpha_s=2/(s+1)`. Slow span is `w`; fast span is `max(2,floor(w/2))`. `rawMACD=EMA_fast-EMA_slow`. Feature = `rawMACD/C_t`.

**MACD histogram(`w`).** Signal span is `max(2,floor(w/3))`. Initialize `signal_0=rawMACD_0`, then apply the same unadjusted recursive EMA formula to raw MACD. Feature = `(rawMACD-signal)/C_t`. A gap resets all three EMAs.

**ATR ratio(`w`).** For `j>=1`, `TR_j=max(H_j-L_j,|H_j-C_{j-1}|,|L_j-C_{j-1}|)`. At `j=w`, seed ATR as `mean(TR_1,...,TR_w)`; then use Wilder recursion. Feature = `ATR/C_t`. A gap requires a fresh seed.

**Rolling std(`w`).** Population standard deviation (`ddof=0`) of the latest `w` one-hour log returns.

**Bollinger position(`w`).** Let `SMA` and population close standard deviation `SD` use the latest `w` closes. Feature = `(C_t-SMA)/(2SD)`, or zero when `SD=0`.

**VWAP deviation(`w`).** `VWAP=sum(TP_kV_k)/sum(V_k)` over the latest `w` bars. Feature = `C_t/VWAP-1`; zero when total volume is zero.

**OBV slope(`w`).** At segment start `OBV_0=0`. For `j>=1`, `OBV_j=OBV_{j-1}+sign(C_j-C_{j-1})V_j`, with `sign(0)=0`. Regress the latest `w` OBV observations on integer `x=0,...,w-1` by OLS with intercept. Divide slope by `max(mean(volume over the same w bars),1e-12)`.

**MFI(`w`).** Raw flow is `TP_jV_j`. For `j>=1`, classify it positive when `TP_j>TP_{j-1}`, negative when lower, neither when equal. At `j>=w`, sum the latest `w` classified flows. MFI is 100 when negative flow is zero but positive flow is nonzero, 50 when both are zero, otherwise `100-100/(1+positive/negative)`. Feature = MFI/100. A gap removes the predecessor and requires `w` new changes.

**Lag return(`k`).** `log(C_t/C_{t-k})` for `k∈{1,2,3,6,12,24}`.

### 7.5 Ten reconstruction groups

Exactly one feature is selected from each group, in this registered order:

1. `MOM_RSI`: RSI
2. `MOM_ROC`: ROC
3. `TREND_SMA`: distance-to-SMA
4. `TREND_MACD`: MACD + MACD histogram
5. `VOL_ATR_STD`: ATR ratio + rolling std
6. `VOL_BB`: Bollinger position
7. `PRICE_VOLUME_VWAP`: VWAP deviation
8. `VOLUME_OBV`: OBV slope
9. `VOLUME_MFI`: MFI
10. `RETURN_LAGS`: lagged returns

Canonical candidate names are `FAMILY__W{hours}` and `LAG_RETURN__K{hours}`.

### 7.6 Training-only selection

Divide the 12-month training window into four consecutive three-calendar-month blocks.

Within each block, a correlation row is permitted only when both origin `t` and target bar label `t+1h` lie in that same block.

For each candidate/block:

- retain pairwise finite candidate/target pairs;
- fewer than 100 pairs => candidate ineligible for that block;
- compute `scipy.stats.spearmanr`;
- any nonfinite correlation, including a constant candidate, => ineligible for that block.

For each selection group `g`, first construct the **common four-block eligible set** `E_g`: candidates in that group that are eligible in all four training blocks.

If `E_g` is empty, the fold hard-fails.

Then, within each block, rank **only candidates in `E_g`** by descending absolute Spearman correlation, using ASCII lexical canonical feature name as tie-break. Do not rank against block-local candidates that fail eligibility in another block.

Average the four ordinal ranks for each candidate in `E_g`. Lowest average rank wins; exact average-rank ties are broken by ASCII lexical canonical name.

### 7.7 Exact deployed column order

The XGBoost matrix columns are exactly:

1–15. the OHLCV columns in Section 7.2 order;  
16. `SELECTED__MOM_RSI`;  
17. `SELECTED__MOM_ROC`;  
18. `SELECTED__TREND_SMA`;  
19. `SELECTED__TREND_MACD`;  
20. `SELECTED__VOL_ATR_STD`;  
21. `SELECTED__VOL_BB`;  
22. `SELECTED__PRICE_VOLUME_VWAP`;  
23. `SELECTED__VOLUME_OBV`;  
24. `SELECTED__VOLUME_MFI`;  
25. `SELECTED__RETURN_LAGS`;  
26. `EGARCH_SIGMA_NEXT`;  
27. `EGARCH_LOG_SIGMA_NEXT`;  
28. `EGARCH_Z_CURRENT`.

No dictionary/object iteration order may substitute for this contract.

## 8. EGARCH

PSR-01B uses a project-defined exact segmented EGARCH contract to prevent hidden state propagation across gaps.

Candidate orders, evaluated in this exact order, are:

1. (1,1,1)
2. (2,1,1)
3. (1,1,2)
4. (2,1,2)

Returns are `y_t=100×log(C_t/C_{t-1})`.

For EGARCH(`p,o,q`):

`h_t = omega + sum_i alpha_i a_{t-i} + sum_j gamma_j z_{t-j} + sum_k beta_k h_{t-k}`

`sigma_t = exp(h_t/2)`

`z_t = (y_t-mu)/sigma_t`

`a_t = |z_t|-m_nu`.

The standardized Student-t absolute-moment constant is:

`m_nu = 2 sqrt(nu-2) Gamma((nu+1)/2) / ((nu-1)sqrt(pi)Gamma(nu/2))`.

The standardized Student-t log-density is:

`log f(z)=lgamma((nu+1)/2)-lgamma(nu/2)-0.5log(pi(nu-2))-((nu+1)/2)log(1+z^2/(nu-2))`.

Observation log likelihood is:

`log f(z_t)-0.5h_t`.

### 8.1 Exact reset

Require `0<=beta_k<=0.999` and `sum beta_k<=0.999`.

Define:

`h_bar = omega/(1-sum beta_k)`.

At every independent segment start, all pre-segment `q` log-variance lags equal `h_bar`, all pre-segment centered absolute-shock lags equal 0, and all pre-segment signed standardized-residual lags equal 0.

A nonfinite reset, nonpositive denominator, or overflow hard-fails that order.

### 8.2 Segmented training likelihood

PAPER_FILL has one continuous filled training segment.

PROJECT_GAP_PRESERVING maximizes one **joint likelihood with one shared parameter vector**, equal to the sum of log likelihoods over all maximal contiguous training-return segments. Each segment resets independently under Section 8.1. Latent state never propagates across a missing interval.

Only training-split returns enter the likelihood.

Optimization is deterministic:

- `scipy.optimize.minimize`;
- method `SLSQP`;
- one start only;
- `maxiter=5000`;
- `ftol=1e-10`;
- `disp=False`.

Initial values:

- `mu` = arithmetic mean of eligible training `y`;
- total beta = 0.90, split equally across `q`;
- each alpha = `0.05/p`;
- each gamma = 0;
- `omega = log(population_variance(y,ddof=0))×(1-0.90)`;
- `nu=8`.

Bounds:

- `mu ∈ [-1000,1000]`;
- `omega ∈ [-20,20]`;
- each alpha/gamma `∈[-2,2]`;
- each beta `∈[0,0.999]`;
- `nu∈[2.05,200]`;
- inequality: `0.999-sum(beta)>=0`.

Optimizer failure, nonfinite objective/parameters, or invalid recursion makes that order unavailable. If all four orders are unavailable, the fold hard-fails.

For a successful order:

`AIC=2k-2LL`, with `k=3+p+o+q`.

Lowest finite AIC wins; exact ties use the registered order above.

### 8.3 Exact causal update

For each observed return `y_t`:

1. compute `h_t` using only pre-`y_t` histories;
2. observe `y_t`;
3. compute `z_t` and `a_t`;
4. update histories so `h_{t+1}` can be computed.

At forecast origin `t`, after `C_t` is complete, the three deployed features are:

- `EGARCH_SIGMA_NEXT = exp(h_{t+1}/2)`;
- `EGARCH_LOG_SIGMA_NEXT = h_{t+1}/2`;
- `EGARCH_Z_CURRENT = z_t`.

Therefore no `y_{t+1}` information enters the feature vector.

Parameters are fit on training only. After fitting, replay training from a training-start reset, then carry state causally through validation and test with parameters fixed. Do not reset at train/validation or validation/test boundaries; reset only at an actual continuity gap.

## 9. XGBoost and model selection

Only XGBoost, MSE, and validation loss-best selection are allowed.

Target standardization uses arithmetic mean and **population standard deviation (`ddof=0`)**.

During tuning:

- calculate mean/std on training target only;
- standardize training target;
- validation uses the same training mean/std.

For final refit:

- recompute mean/std with `ddof=0` on the union of rows independently eligible in original train and validation splits;
- inverse-transform test forecasts to raw log-return units.

Zero or nonfinite std hard-fails.

### 9.1 Optuna

Use exactly:

`TPESampler(seed=derived_optuna_seed, multivariate=False, group=False, constant_liar=False)`

and `NopPruner()`.

Create one minimization study and execute exactly 50 trials sequentially with `n_jobs=1`.

Suggestion calls occur in this exact order and use these exact names:

1. `max_depth`: int 2–4 inclusive
2. `learning_rate`: log float 0.005–0.03
3. `n_estimators`: int 1000–2500 inclusive
4. `min_child_weight`: float 10–40
5. `subsample`: float 0.60–0.90
6. `colsample_bytree`: float 0.60–0.90
7. `reg_alpha`: log float 1e-4–0.05
8. `reg_lambda`: log float 1–40

Exactly equal finite objective values are resolved by smallest `trial.number`.

### 9.2 XGBoost

Fixed settings include:

- `objective='reg:squarederror'`;
- `tree_method='hist'`;
- CPU execution;
- `n_jobs=1`;
- `random_state=derived_seed`;
- `eval_metric='rmse'`;
- early stopping patience 50.

No additional uncontrolled RNG is allowed.

During tuning, the evaluation set is exactly the registered validation matrix and standardized validation target.

The monitored metric is validation RMSE.

If multiple boosting iterations attain the same minimum recorded RMSE, the **smallest iteration** is the selected best iteration.

The Optuna objective is validation MSE computed from predictions using trees `0..best_iteration` inclusive.

### 9.3 Final retraining

After winning-trial selection:

- preserve winning hyperparameters;
- final estimator count = `best_iteration+1`;
- if early stopping never triggered, use the sampled estimator count;
- recompute target scaling on combined eligible train+validation;
- retrain once on combined train+validation;
- no early stopping in final refit;
- use the registered final-refit random seed;
- apply once to held-out test.

## 10. Forecast identity firewall

For each missing-data arm/fold, exactly one final forecast vector is generated.

BASELINE_SIGN and COST_AWARE must consume the same vector. No execution-rule-specific tuning, fitting, feature selection, or RNG path is permitted.

The vector is strictly sorted by forecast-origin bar-open timestamp and contains no duplicate timestamps or nonfinite forecasts.

The serialization prefix is the ASCII/UTF-8 bytes for `PSR01B_FORECAST_VECTOR_V1` followed by **exactly one NUL byte `0x00`**. It is not the two printable characters backslash and zero. Offline implementation tests must include a fixed synthetic hash fixture.

Canonical forecast bytes are:

- the exact prefix bytes defined above;
- unsigned 64-bit little-endian row count;
- for each row, `struct.pack('<qd', timestamp_unix_seconds, forecast_float64)`.

The timestamp is signed int64 Unix seconds for the UTC bar-open label. Forecast is IEEE-754 float64 little-endian in raw log-return units.

Forecast identity is `SHA256(payload)`.

Both execution rules must record the same hash for an arm/fold.

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

For any registered return sequence, all returns must be finite and `1+r_t>0`.

`ARC = prod(1+r_t)^(8760/N)-1`.

`ASD = sqrt(8760)×sample_std(r_t,ddof=1)`.

Annual risk-free rate is `0.042`.

`Sharpe=(ARC-0.042)/ASD`.

For each fold:

- `fold_total_return=prod(1+r_t)-1`;
- `fold_ARC=prod(1+r_t)^(8760/N_fold)-1`;
- `fold_ASD=sqrt(8760)×sample_std(r_t,ddof=1)`;
- `fold_Sharpe=(fold_ARC-0.042)/fold_ASD`.

If fold or consolidated ASD is zero/nonfinite, Sharpe is unavailable; an experiment cannot pass a condition that requires its sign.

### 14.1 Maximum drawdown

Set `E_0=1`.

For each registered net return:

`E_j=E_{j-1}(1+r_j)`.

Costs are already embedded in `r_j`.

Running peak:

`P_j=max(E_0,...,E_j)`.

Drawdown:

`D_j=E_j/P_j-1`.

Maximum drawdown:

`MDD=min_j D_j`, a non-positive number.

For consolidated statistics, concatenate fold return records in registered fold order and **carry equity across fold boundaries**. Do not reset wealth between folds even though positions reset to cash. Terminal liquidation costs are already inside the last return record of each fold.

Consolidated total return is `prod(1+r_t)-1`.

For PROJECT_GAP_PRESERVING, `N` is the number of accepted finite evaluation-return records; gap rows are not inserted as zero.

## 15. Primary inferential test

For each missing-data arm define paired hourly differential:

`d_t = r_t(COST_AWARE)-r_t(BASELINE_SIGN)`.

The descriptive **all-record mean** uses every registered evaluation record, including records in short contiguous segments.

Primary inferential block length is exactly 168 hours. Secondary diagnostic block lengths are exactly 24 and 72 hours. Bootstrap draws are exactly 10,000.

### 15.1 Fixed-block inference universe

For a requested block length `L`, a contiguous evaluation segment is eligible for bootstrap inference **only if `n >= 2L`**.

Segments with `n < 2L`:

- remain in descriptive strategy returns, Sharpe, turnover, trade count, and the all-record differential mean;
- are excluded from that block-length bootstrap p-value and CI;
- are never shortened to a smaller block length;
- are never dropped selectively based on their returns.

At least **two** inference-eligible segments are required for an arm/block-length result. Otherwise inference for that arm/block is `UNAVAILABLE`. An unavailable primary 168-hour inference means PSR-01B cannot pass.

For the 168-hour primary test, the inference universe therefore contains only segments with `n>=336`.

Report both:

1. the all-record observed mean differential; and
2. the 168-hour inference-universe observed mean differential.

Both must be positive for a replication pass.

### 15.2 Exact circular fixed-block algorithm

For every inference-eligible segment of length `n`:

- keep block length exactly `L`;
- draw `ceil(n/L)` independent start indices uniformly from `{0,...,n-1}`, with replacement;
- a block starting at `s` contains indices `(s+j) mod n` for `j=0,...,L-1`;
- concatenate blocks and retain exactly the first `n` sampled observations.

Process segments in registered fold order, then ascending segment-start timestamp.

Resample each eligible segment independently back to its original length and concatenate sampled segments in that same order. The pooled bootstrap statistic is the observation-weighted arithmetic mean over this fixed inference universe.

No block may cross a fold or continuity-gap boundary.

RNG is exactly:

`numpy.random.Generator(numpy.random.PCG64(registered_seed))`.

### 15.3 Null test and interval

Let `mu_inf` be the observed arithmetic mean over the inference universe.

For the one-sided primary null bootstrap, subtract `mu_inf` from every differential observation in that inference universe before applying the sampled indices.

Alternative:

`mean(COST_AWARE-BASELINE_SIGN)>0`.

Raw p-value:

`(1 + count(centered_bootstrap_mean >= mu_inf))/10001`.

Use the identical sampled indices on uncentered paired strategy returns in the same inference universe for complementary Sharpe-difference evidence.

The 95% percentile interval is exactly:

`np.quantile(uncentered_inference_mean_draws,[0.025,0.975],method='linear')`.

Sharpe-difference bootstrap evidence is reported but is not an additional mandatory inferential gate.

The all-record cost-aware versus baseline Sharpe difference remains the pass-direction metric.

## 16. Multiple testing

There are exactly two primary raw p-values, in registered order:

1. PAPER_FILL;
2. PROJECT_GAP_PRESERVING.

Apply Holm step-down at alpha 0.05.

Let `m=2`. Sort raw p-values ascending, resolving exact ties by registered arm order.

At sorted rank `j=0,...,m-1` compute:

`s_j=(m-j)p_j`.

Then:

`adjusted_j=min(1,max(s_0,...,s_j))`.

Map adjusted values back to registered arm order.

Reject iff `adjusted_p<=0.05`.

A nonfinite raw p-value hard-fails; no pass classification is available.

The 24h and 72h robustness diagnostics are outside the primary Holm family and cannot rescue a 168h failure.

## 17. Replication decision

Return:

`BOUNDED_H2_REPLICATION`

only if **all** of the following hold in both missing-data arms:

1. all-record observed mean cost-aware minus baseline net return > 0;
2. primary 168h inference-universe observed mean differential > 0;
3. at least two 168h-inference-eligible contiguous segments (each `n>=336`) exist;
4. Holm-adjusted primary 168h one-sided p-value <= 0.05;
5. cost-aware turnover < baseline turnover under all registered fold/gap liquidations;
6. cost-aware completed trades >= 20;
7. all-record cost-aware Sharpe − baseline Sharpe > 0.

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

Any such change requires a new registered experiment. More generally, **any registered analytic field changed after empirical outcome observation constitutes a new experiment and cannot amend PSR-01B.**

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
