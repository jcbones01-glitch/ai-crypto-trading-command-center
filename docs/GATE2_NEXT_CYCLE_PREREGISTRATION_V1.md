# Gate 2 — Next Research Cycle Preregistration V1

## Status

**FROZEN PROSPECTIVE REGISTRATION — BEFORE EVIDENCE-GENERATING BACKTEST**

This registration governs a new Development-only research cycle. It does not modify, rescue, retune, or relabel HYP-0001 through HYP-0004. Those hypotheses remain closed after their recorded robustness failure.

No result from this registration may be treated as evidence until the registered execution completes and produces an auditable artifact.

## Scope and firewall

- Assets: BTCUSDT and ETHUSDT
- Market: Binance Spot
- Timeframe: 1 hour
- Development: `[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`
- Validation: `[2022-01-01T00:00:00Z, 2024-01-01T00:00:00Z)` — inaccessible
- Locked OOS: `[2024-01-01T00:00:00Z, 2026-01-01T00:00:00Z)` — inaccessible
- Data: Gate 1A-certified observations only; continuity breaks are never bridged
- Execution: spot-only, long-only, 0–100% exposure, no leverage, no shorting, no intrabar fills

The Gate 2 protocol remains controlling.

## Common causal execution contract

For every candidate:

1. Calculate the signal using information available through the close of bar `t`.
2. Entry occurs at the open of the next eligible bar (`t+1`).
3. Directional slippage is applied against the position.
4. Commission is 10 basis points per side in the baseline.
5. No same-bar/zero-delay execution is permitted.
6. No synthetic observation, interpolation, forward-fill, timestamp repair, or gap bridging is permitted.
7. If required history crosses a continuity break, the signal is invalid.
8. A position cannot be carried through an unresolved research-continuity boundary for performance accounting.
9. **Non-overlap rule:** each candidate may have at most one active position. For HYP-0005, HYP-0006, and HYP-0007, a new signal observed while that candidate already has an active one-bar position is ignored. A new event becomes eligible only after the position is flat. This rule is fixed across every parameter and robustness cell and is not a selection/tuning parameter.
10. **One-bar holding rule:** for HYP-0005 and HYP-0007, an executed entry is held for exactly one eligible bar and exits at that bar's close for research return accounting. HYP-0006 follows the same one-eligible-bar holding period on ETH.

## Registered candidates

### HYP-0005 — Volume-Shock Directional Persistence

**Exact hypothesis:** When an hourly bar closes with unusually high trading volume and a positive return, the next eligible hourly return will have a positive conditional mean relative to the unconditional eligible-bar baseline, after registered costs and slippage.

**Mechanism:** unusually high participation accompanying directional movement may indicate information arrival or persistent order-flow pressure that is not fully incorporated within one hour.

**Baseline rules:**
- Volume baseline: trailing median volume over the previous 24 completed bars before `t`.
- Volume shock: `volume[t] >= 3.0 * baseline`.
- Positive directional threshold: `return[t] >= +1.0%`, where return is `close[t]/close[t-1]-1`.
- Entry: long at next eligible open.
- Exit: after exactly one eligible completed bar using the close of that bar for research return accounting.

**Registered parameter grid:**
- Volume baseline length: 24, 48 hours.
- Volume shock multiplier: 2.0, 3.0, 4.0.
- Positive return threshold: 0.5%, 1.0%, 1.5%.
- Holding period: exactly 1 eligible bar; fixed and not searched.

All 18 Cartesian cells are required. The baseline cell is explicitly `(24, 3.0, 1.0%)` and is not selected after observing results.

**Failure modes:** volume may proxy volatility; extreme-volume observations may be sparse; the effect may disappear after costs or delayed execution; threshold selection may overfit.

**Invalidation:** reject if the frozen Development decision rule is not satisfied, if the effect fails cost/timing robustness, or if concentration/sample stability fails.

### HYP-0006 — Cross-Asset BTC Lead/Lag Response

**Exact hypothesis:** A sufficiently large BTCUSDT hourly return that is not contemporaneously matched by ETHUSDT contains predictive information about ETHUSDT's next eligible hourly return beyond ETH's own immediately available return.

**Mechanism:** market-wide information may propagate first through BTC and subsequently into ETH. The test is designed to determine whether measurable lagged transmission exists.

**Baseline rules:**
- BTC shock threshold: `>= +1.5%` hourly return.
- Relative-response gap: `BTC_return[t] - ETH_return[t] >= +0.50%`.
- Signal: long ETH at next eligible ETH open.
- Exit: after exactly one eligible ETH bar.
- BTC and ETH observations must share the exact canonical hourly timestamp and both be certified/continuous.

**Registered parameter grid:**
- BTC shock threshold: 1.0%, 1.5%, 2.0%.
- Relative-response gap: 0.25%, 0.50%, 1.00%.
- Holding period: exactly 1 eligible ETH bar; fixed and not searched.

All 9 Cartesian cells are required. The baseline cell is `(1.5%, 0.50%)` and is not selected after observing results.

**Additional control observation:** report the unconditional ETH next-bar return and the ETH own-return-only directional condition on the same eligible synchronized sample. These controls are descriptive comparators and do not authorize post-result rule changes.

**Failure modes:** BTC/ETH correlation may masquerade as lead/lag; rare shocks may create low sample support; synchronization errors could create false prediction; threshold selection can overfit.

**Invalidation:** reject if the frozen Development decision rule is not satisfied, if the effect fails the two-bar timing stress, if synchronized continuity restrictions materially eliminate the sample, or if concentration is excessive.

### HYP-0007 — Volume-Capitulation Reversal

**Exact hypothesis:** After an unusually high-volume hourly selloff whose negative return is large relative to recent activity, the next eligible hourly return has a positive conditional mean exceeding the unconditional eligible-bar baseline after costs and slippage.

**Mechanism:** an extreme, high-participation selloff may include forced liquidation or temporary liquidity imbalance followed by short-horizon exhaustion.

**Baseline rules:**
- Volume baseline: trailing median volume over the previous 24 completed bars before `t`.
- Volume shock: `volume[t] >= 3.0 * baseline`.
- Negative directional threshold: `return[t] <= -1.5%`.
- Entry: long at next eligible open.
- Exit: after exactly one eligible completed bar.

**Registered parameter grid:**
- Volume baseline length: 24, 48 hours.
- Volume shock multiplier: 2.0, 3.0, 4.0.
- Negative return threshold: -1.0%, -1.5%, -2.0%.
- Holding period: exactly 1 eligible bar; fixed and not searched.

All 18 Cartesian cells are required. The baseline cell is `(24, 3.0, -1.5%)` and is not selected after observing results.

**Failure modes:** may collapse into ordinary mean reversion; volume may proxy volatility; extreme events may be sparse; a few historical shocks may dominate results.

**Invalidation:** reject if the frozen Development decision rule is not satisfied, if cost/timing stress destroys the effect, if cross-asset stability fails, or if concentration/sample stability fails.

## Benchmarks

For every asset and every strategy cell:

1. **Cash:** zero return over the same eligible strategy observations.
2. **Buy-and-hold:** same eligible segment universe and continuity boundaries, with warm-up/eligibility explicitly matched.
3. **Conditional-bar comparator:** for HYP-0005/HYP-0007, report the raw next-bar conditional return before strategy costs as a descriptive observation; this does not replace net strategy evaluation.
4. **ETH own-return control:** for HYP-0006, report the preregistered descriptive control described above.

Benchmarks cannot bridge excluded regions or use a larger eligible universe than the strategy.

## Registered robustness battery

The robustness battery is fixed before execution and every attempted cell must be recorded, including errors.

### 1. Parameter neighborhood

The full grids above are the registered parameter neighborhood. No additional values may be tested for evidence in this cycle.

**Pass:** for each asset, at least 60% of valid perturbation cells have positive mean eligible-segment return and the median perturbation compound return is above cash. Baseline is reported separately.

### 2. Fee/slippage stress

Evaluate baseline 10/5 bps, stress 15/10 bps, and stress 25/15 bps commission/slippage per side.

**Pass:** highest-cost cell remains above cash with positive mean eligible-segment return on each asset.

### 3. Timing stress

Evaluate exactly 1-bar and 2-bar entry delays.

**Pass:** at 2 bars, each asset has positive mean eligible-segment return and remains above cash.

### 4. Regime stability

Use only information available at each signal close:
- Bull: trailing 168-hour return > +10%
- Bear: trailing 168-hour return < -10%
- Neutral: otherwise

**Pass:** no positive result may be entirely attributable to one regime; at least two regimes must be positive on each asset when each has at least 100 eligible bars.

### 5. Asset transferability

For HYP-0005 and HYP-0007, evaluate BTC and ETH independently under the same registered cell definitions. HYP-0006 inherently evaluates BTC as the predictor and ETH as the target.

**Pass:** HYP-0005/HYP-0007 require positive mean eligible-segment and positive compound return on both assets. HYP-0006 requires positive mean eligible-segment and positive compound return on ETH plus a positive conditional-vs-control difference under the frozen rule.

### 6. Sample-size stability

Run leave-one-eligible-segment-out analysis and report completed trade/event counts.

**Pass:** at least 75% of leave-one-out variants remain above cash on each required asset; if the full baseline is non-positive, this dimension fails promotion regardless of leave-one-out results.

### 7. Concentration

Report segment log-return concentration and top-10%-trade/event P&L concentration.

**Pass:** no single segment >50% of positive log-return contribution and top 10% of positive trades/events <=50% of positive P&L. Non-positive denominators fail rather than becoming exempt.

### 8. Drawdown/recovery

Report maximum drawdown, maximum segment drawdown, longest recovery, and segment losses worse than -50%.

**Pass:** max drawdown <70%, no segment loss worse than -50%, and no recovery >50% of eligible historical duration.

### 9. Overall decision

All nine dimensions must pass. No weighted score, discretionary override, best-cell selection, or post-result threshold change is permitted.

Classification:
- `ROBUSTNESS_PASS`
- `ROBUSTNESS_FAIL`
- `ROBUSTNESS_INCONCLUSIVE`

`ROBUSTNESS_INCONCLUSIVE` is not a promotion. A material strategy change requires a new hypothesis/strategy version and new preregistration.

## Multiple-testing accounting

Registered evidence cells before robustness stress:
- HYP-0005: 18 parameter cells
- HYP-0006: 9 parameter cells
- HYP-0007: 18 parameter cells
- Total baseline parameter cells: 45

Every parameter cell and every robustness stress cell must be enumerated in the final artifact. Errors count as attempted cells and cannot be silently dropped.

## Evidence artifact requirements

The execution artifact must contain:
- this preregistration SHA-256
- executing code commit
- dataset identity for BTCUSDT and ETHUSDT
- all 45 registered parameter cells
- all robustness cells and outcomes
- baseline and benchmark results
- eligible segment IDs/counts
- trade/event counts
- cost/slippage assumptions
- timing results
- regime results
- concentration results
- sample-size results
- drawdown/recovery results
- explicit `oos_accessed: false`
- final binary decision for each hypothesis

## Stop conditions

Do not:
- access Validation or OOS data;
- modify HYP-0001 through HYP-0004;
- add parameter values after observing results;
- remove poor-performing cells;
- tune thresholds based on Development outcomes;
- begin paper or live trading;
- interpret a profitable result as proof of a durable edge.

## Final status

**FROZEN REGISTRATION. DEVELOPMENT EVIDENCE MAY NOW BE GENERATED ONLY BY AN IMPLEMENTATION THAT EXECUTES THIS SPECIFICATION EXACTLY.**
