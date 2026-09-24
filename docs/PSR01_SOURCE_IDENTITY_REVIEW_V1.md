# PSR-01 — Source Identity and Exact-Replication Feasibility Review V1

**Status:** SOURCE IDENTITY UNRESOLVED — NO EMPIRICAL REPLICATION AUTHORIZED  
**Issue:** #86  
**Decision:** `PSR01_SOURCE_IDENTITY_UNRESOLVED`  
**Decision comment:** 5819520257  
**Reviewed paper:** Andrei Bysik & Robert Ślepaczuk (2026), *Machine Learning-Based Bitcoin Trading Under Transaction Costs: Evidence From Walk-Forward Forecasting*, arXiv:2606.00060v1.

## Purpose

This review determines whether PSR-01 can be treated as an exact independent reproduction of the paper before any project P&L is generated.

It is separate from AMS-DEP. It does not authorize access to AMS-DEP Validation/OOS, derivatives execution, paper trading, live trading, or strategy deployment.

## Primary finding

The paper describes its source as hourly OHLCV for a **BTC/USDT USD-margined futures contract collected from Binance public REST API**, with a raw sample beginning **2017-12-01** and ending **2026-01-01**.

Official Binance historical materials place the launch of Binance Futures in **September 2019** and identify BTCUSDT USDT-margined perpetual futures as its first product.

Therefore the claimed pre-September-2019 Binance futures history cannot presently be reconciled with Binance's documented product history.

This blocks an exact replication until the actual data source/instrument is identified.

## Source classification

The source must not be silently reinterpreted as Binance Spot merely because Spot BTCUSDT has earlier history.

Possible unresolved explanations include:

- the paper used Binance Spot BTCUSDT but described it as futures;
- the paper spliced Spot and Futures;
- the paper used a vendor/continuous series;
- the paper used another product/source;
- the manuscript contains a source-description error.

No reviewed evidence establishes which explanation is correct.

## Additional reproducibility gaps

The paper is detailed enough to preserve the core economic mechanism, but this review did not establish all details needed for exact algorithm-level reproduction, including:

- the exact 15 OHLCV feature variables;
- the exact six lagged-return lags;
- the mapping of 94 TA candidates into the stated 10 selection groups;
- random seeds and Optuna sampler state;
- full package/runtime versions;
- exact post-selection XGBoost retraining/early-stopping behavior after combining train and validation;
- an execution timing/latency convention beyond bar-close accounting.

The absence of these details does not invalidate the paper. It limits exact reproducibility.

## Paper mechanism preserved for future bounded replication

The following should be retained prospectively if a bounded replication is later approved:

- next-hour BTC/USDT return forecasting;
- 12-month training window;
- 3-month validation window;
- 3-month test window;
- 3-month rolling step;
- 27 held-out test folds;
- XGBoost as the first bounded target;
- MSE loss;
- validation loss-best selector;
- long-only position mapping;
- transaction cost `c = 0.001` per unit turnover;
- cost-aware threshold `lambda = 2.0`;
- update position only when
  `abs(forecast) > lambda * c * abs(desired_position - previous_position)`;
- the paper's net-return accounting;
- buy-and-hold and stated benchmarks;
- explicit retention of the paper's stronger descriptive OHLCV+TA result as known prior evidence rather than a post-project-outcome replacement target.

## Missing-data boundary

The paper reconstructs a complete hourly grid and fills missing bars using previous close and zero volume.

That is a paper-specific treatment. The existing project research pipeline generally preserves missingness and prohibits silent synthetic repair.

A future bounded replication should distinguish:

1. a **paper-treatment arm**, reproducing the published fill rule if the source can be reconstructed; and
2. a **project-native sensitivity arm**, preserving gaps and prohibiting synthetic bars.

These two arms must not be mixed or selected based on whichever performs better.

## Current gate

Classification:

`PSR01_SOURCE_IDENTITY_UNRESOLVED`

No empirical P&L run is authorized.

No exact replication specification should be frozen under the current evidence.

## Resolution paths

PSR-01 may advance only after one of the following is prospectively documented:

1. author/code/data clarification resolves the exact source and instrument; or
2. the project explicitly approves a **bounded declared-deviation replication** on a different fully auditable source, such as Binance Spot, while forbidding any claim that its returns reproduce the paper's futures results.

## Firewall

Until a later reviewed gate:

- do not access AMS-DEP Validation/OOS for PSR-01;
- do not run PSR-01 P&L;
- do not tune model, features, `lambda`, costs, folds, missing-data rules, or selector using project outcomes;
- do not paper trade or live trade;
- do not authorize leverage or derivatives execution;
- do not call a Spot implementation an exact futures replication.

## Sources

Primary paper:
- https://arxiv.org/abs/2606.00060
- https://arxiv.org/html/2606.00060v1

Binance historical product references:
- https://www.binance.com/en/blog/all/421499824684900356
- https://www.binance.com/en/blog/all/421499824684900979
- https://www.binance.com/en/support/announcement/detail/360033273472
