# Gate 2 Cycle 7 — Prospective Preregistration V1

## Status

**FROZEN PROSPECTIVE REGISTRATION — BEFORE CYCLE 7 EVIDENCE GENERATION**

Cycle 7 is a material strategy-design change motivated by the repeated failure of ultra-short one-bar candidates under the frozen transaction-cost model. It does not rescue, retune, or relabel HYP-0001 through HYP-0022. Those hypotheses remain closed for promotion purposes.

External research motivation is limited to mechanism selection, not parameter selection. Published hourly cryptocurrency research reports both intraday momentum/reversal and predictive candlestick structure, including Bitcoin and Ethereum. Cycle 7 therefore tests lower-turnover, multi-hour versions of distinct mechanisms prospectively.

## Firewall

- Market: Binance Spot
- Assets: BTCUSDT and ETHUSDT
- Timeframe: 1 hour
- Development: `[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`
- Validation: `[2022-01-01T00:00:00Z, 2024-01-01T00:00:00Z)` — inaccessible
- Locked OOS: `[2024-01-01T00:00:00Z, 2026-01-01T00:00:00Z)` — inaccessible
- Data: Gate 1A-certified observations only; continuity breaks are never bridged
- Positioning: spot-only, long-only, 0–100% exposure, no leverage, no shorting

## Common causal execution contract

1. Signal uses information available through close of bar `t`.
2. Entry is at the open of the next eligible bar (`t+1`) in baseline timing.
3. Registered timing stress also evaluates entry at `t+2`.
4. Directional slippage is adverse to the position.
5. Baseline commission = 10 bps/side; baseline slippage = 5 bps/side.
6. Fee/slippage stress cases = 15/10 bps and 25/15 bps per side.
7. Exit occurs at the close of the registered holding-period bar after entry.
8. One active position per hypothesis/asset; overlapping signals are ignored until flat.
9. No intrabar fills, synthetic observations, interpolation, forward-fill, timestamp repair, or continuity-gap bridging.
10. If required lookback crosses a continuity break, the signal is invalid.

## HYP-0023 — Rolling 24h Abnormal-Return Continuation

**Hypothesis:** After a large positive rolling 24-hour return accompanied by continued positive hourly direction, positive drift persists over the next multi-hour holding window strongly enough to survive registered costs.

**Signal at close t:**
- trailing 24-hour return `close[t]/close[t-24]-1 >= A`
- current hourly return `close[t]/close[t-1]-1 >= H`

**Grid:**
- A = {5%, 10%}
- H = {0%, 0.5%}
- holding period = {6, 12, 24} eligible bars
- total = **12 cells**
- baseline = A 10%, H 0.5%, hold 12h

**Mechanism:** abnormal-return momentum / delayed information incorporation.

**Invalidation:** fails any mandatory Gate 2 Development criterion or frozen robustness requirement.

## HYP-0024 — Volatility-Contraction Breakout Continuation

**Hypothesis:** Breakouts emerging from unusually compressed 24-hour ranges have positive multi-hour continuation after costs.

**Causal compression state at close t:**
- Compute each completed rolling 24h high-low range ratio `(max(high)-min(low))/close`.
- Compare the most recent fully completed pre-signal 24h range ratio with the empirical distribution of the preceding 30 days (720 completed hourly observations), excluding the current signal bar.
- Compression condition: pre-signal range ratio is at or below registered rolling percentile Q.

**Breakout signal at close t:**
- `close[t] >= prior_24h_high * (1 + B)`, where prior_24h_high uses only bars t-24 through t-1.

**Grid:**
- Q = {20th percentile, 30th percentile}
- B = {0%, 0.25%}
- holding period = {12, 24} eligible bars
- total = **8 cells**
- baseline = Q 20%, B 0.25%, hold 12h

**Mechanism:** volatility clustering and expansion after compression.

**Invalidation:** fails any mandatory Gate 2 Development criterion or frozen robustness requirement.

## HYP-0025 — Bullish-Harami Multi-Hour Reversal

**Hypothesis:** A bullish Harami-type reversal after a materially bearish parent candle predicts positive multi-hour returns after costs.

**Signal at close t:**
- bar t-1 is bearish: `close[t-1] < open[t-1]`
- parent body/range ratio is at least P
- bar t is bullish: `close[t] > open[t]`
- current real body is fully inside the prior real body:
  - `open[t] >= close[t-1]`
  - `close[t] <= open[t-1]`
- current close-location within its own range is at least L

**Grid:**
- P = {0.50, 0.70}
- L = {0.50, 0.75}
- holding period = {6, 12} eligible bars
- total = **8 cells**
- baseline = P 0.50, L 0.75, hold 12h

**Mechanism:** exhaustion/overreaction reversal expressed through two-candle price structure.

**Invalidation:** fails any mandatory Gate 2 Development criterion or frozen robustness requirement.

## Registered search size

- HYP-0023: 12 cells
- HYP-0024: 8 cells
- HYP-0025: 8 cells
- Total: **28 prospective parameter cells**

All 28 cells must be attempted on both BTCUSDT and ETHUSDT. Errors count as attempted cells and may not be silently dropped.

## Benchmarks

For each asset and eligible segment universe:
- cash/no-position
- buy-and-hold with the same continuity boundaries and eligible universe
- raw conditional forward return before strategy costs as a descriptive comparator

## Promotion criteria

The controlling `docs/GATE2_RESEARCH_PROTOCOL.md` criteria apply without relaxation. A candidate must satisfy all mandatory Development-to-Validation requirements, including:
- net compound return > cash and >= +10% on Development
- positive mean eligible-segment return
- at least 20 eligible strategy segments
- at least 300 completed trades across the preregistered BTC/ETH Development universe
- profitability after costs on both BTC and ETH
- drawdown <70% on each asset and no segment loss worse than -50%
- reproducibility, benchmark comparability, and completed robustness battery

## Frozen robustness battery

1. **Parameter neighborhood:** at least 60% of valid parameter cells have positive mean eligible-segment return on each required asset; median cell compound return > cash.
2. **Fee/slippage:** baseline, 15/10 bps stress, and 25/15 bps stress. Highest-cost baseline cell must remain above cash with positive mean segment return on each asset.
3. **Timing:** entry delays 1 and 2 bars. Two-bar baseline must remain above cash with positive mean segment return on each asset.
4. **Regime:** trailing 168h return at signal close: Bull >+10%, Bear <-10%, Neutral otherwise. At least two qualifying regimes must be positive on each asset when each has >=100 eligible signal bars.
5. **Asset transferability:** positive baseline compound and mean segment return on both BTC and ETH.
6. **Sample stability:** leave-one-eligible-segment-out; >=75% variants above cash on each asset. Non-positive full baseline automatically fails this dimension.
7. **Concentration:** no single segment >50% of positive log-return contribution; top 10% of positive trades/events <=50% of positive P&L. Non-positive denominators fail.
8. **Drawdown/recovery:** max drawdown <70%; no segment loss worse than -50%; longest recovery <=50% of eligible historical duration.
9. **Overall:** all mandatory protocol criteria and all robustness dimensions must pass. No weighted score or discretionary override.

## Evidence artifact requirements

Artifact must include:
- preregistration SHA-256
- executing/checked-out commit
- dataset identities
- all 28 registered cells on both assets
- all fee/slippage and timing stress cells
- benchmark results
- segment IDs/counts and trade counts
- regime, leave-one-out, concentration, drawdown/recovery results
- explicit `validation_or_oos_accessed: false`
- candidate-specific binary promotion decision

## Stop conditions

Do not:
- access Validation or OOS
- modify or rescue HYP-0001 through HYP-0022
- add/remove Cycle 7 parameter values after evidence is seen
- choose only the best observed cell for promotion
- weaken costs, timing, sample, cross-asset, or robustness thresholds after results
- begin paper or live trading

**Cycle 7 is frozen only after this file is committed. Evidence generation must use this exact committed registration.**
