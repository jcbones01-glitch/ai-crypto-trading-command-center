# AMS-DEP synthetic numerical calibration v1

Status: fixed synthetic-only experiment specification. Commit this plan and JSON before code execution/results. It does not freeze or authorize the BTC/ETH study. Prior spot data, AMS-V1 occupancy and strategy results are not inputs.

Configuration: `research/experiments/ams_dep_synthetic_core_v1.json`. Exactly 1,000 replicates of each of seven cases, no early stopping, rerolling seeds, case dropping or threshold changes. RNG is NumPy PCG64 with SeedSequence([20260919, case_index, replicate_index]); indices start at zero. Each path has 10,000 retained hours, 2,000 in each of five synthetic year blocks. Calendar hours for each year begin January 1 at 00:00 UTC. Gaps between year blocks create separate segments; never carry residual state across them. These are artificial regressors and histories, not historical observations.

For each year reset two previous returns to zero and GARCH variances to 0.0001, generate a 1,000-hour burn-in and 2,000 retained predictor/target pairs. Need 3,001 innovations per year to obtain 2,000 pairs. For each time, generate two standard normal variates z1,z2; correlated asset innovations are (z1,0.6*z1+0.8*z2). Both assets share deterministic exogenous state label LOW/NORMAL/HIGH cycling every 240 hours, indexed by retained predictor t; burn-in states extend the same cycle backward. Years are the fixed categorical design blocks, not discovered breakpoints.

Generate r_(t+1)=phi(year,state_t)*r_t + sigma_(t+1)*z_(t+1). Return r_t is x; next return is y. In the IID and three AR cases sigma=0.01. Case order and parameters:

1. iid_null: phi=0.
2. heteroskedastic_null: phi=0; sigma is 0.005, 0.01, 0.03 for predictor LOW, NORMAL, HIGH, respectively.
3. garch_null: phi=0; h_(t+1)=0.000005+0.10*r_t²+0.85*h_t, sigma=sqrt(h). Initialize h=0.0001 each year before burn-in.
4. stable_ar: phi=0.10 in all years/states.
5. time_ar: phi=+0.15 in 2017/2019/2021 and -0.15 in 2018/2020.
6. state_ar: phi=+0.15 in LOW, 0 in NORMAL, -0.15 in HIGH.
7. bid_ask_bounce: efficient returns u are correlated IID with sigma=0.01 and phi=0. Observed returns r_t=u_t+e_t-e_(t-1), where e_t is independent per-asset equiprobable ±0.005. Draw e arrays after innovation arrays within each year. No economic edge is claimed even if measured dependence is detected.

Implementation fixes the RNG call sequence as one `(3001,2)` normal array per year, followed only in bounce by one `(3002,2)` integer Bernoulli array. Compute all steps sequentially, then retain x=r[1000:3000], y=r[1001:3001]. In the recurrence for r[j], state is that of predictor j-1-1000; for j=0 the preceding r is initialized at zero. Both assets use exactly the same row and state schedule. There are no data-driven parameters.

Fit the full specified 14-column model for both assets and apply Holm over all six tests. Null size checks count any erroneous rejection among:

- all six tests for iid_null, heteroskedastic_null, garch_null;
- both TIME and both STATE tests for stable_ar (DEP is an alternative);
- both STATE tests for time_ar;
- both TIME tests for state_ar.

Use the full six-slot Holm family even when only a subset is truly null. For bounce, record all outcomes but impose no null-size requirement: measured serial dependence is intentionally present, while the latent efficient-price returns are independent.

Engineering screening criteria, fixed before results: null-family erroneous-rejection rate <=0.075 and invalid-fit fraction <=0.01 in each of the six applicable cases. Strong-alternative power must be >=0.80 separately per asset for stable_ar DEP, time_ar TIME and state_ar STATE. Report 95% Wilson intervals with z=1.959963984540054 for every rate. These limits are screening choices, not statistical proof that nominal 5% control holds universally. Missing fits count as non-detections for power and are also counted as invalid; never discard replicates from denominators.

Report each replicate's six raw/adjusted p-values and validity, all aggregate rates, exact configuration and code hashes, executing SHA, runtime/package versions, and source scope. Output must be labeled SYNTHETIC_ONLY and must not contain market data. Deterministically gzip the replicate ledger (mtime=0). A failed screen blocks empirical release and is retained without tuning this version. A coding correction gets a new recorded implementation and full rerun, with the prior evidence retained.

## Limits and next gate

These fixed state labels isolate regression/HAC/multiplicity behavior. They do **not** reproduce the endogenous AMS-V1 state estimator, its 744-bar warm-up, realistic heavy tails, all 28 historical segments or row-selection effects. No assertion of full finite-sample calibration follows from passing. Full-pipeline endogenous-state and support/continuity calibration, including asynchronous cross-asset observations, remains necessary before the original empirical preregistration can be frozen and independently released. This pilot is an engineering step and cannot promote a strategy.
