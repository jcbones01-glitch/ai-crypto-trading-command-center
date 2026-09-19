# Gate 2 Cycle 2 — Preregistration V1

## Status

FROZEN PROSPECTIVE REGISTRATION. This file must exist before the Cycle 2 evidence-generating workflow. It does not modify HYP-0001 through HYP-0007.

## Firewall

- Assets: BTCUSDT and ETHUSDT, Binance Spot, 1-hour bars.
- Development only: `[2017-08-17T00:00:00Z, 2022-01-01T00:00:00Z)`.
- Validation and Locked OOS are inaccessible.
- Gate 1A-certified observations only; continuity breaks are never bridged.
- Signal uses information through close of bar t.
- Delay 1 means entry at open of t+1; delay 2 means entry at open of t+2.
- Baseline commission is 10 bps per side and baseline slippage is 5 bps per side.
- Stress cases are 15/10 bps and 25/15 bps respectively.
- Long-only, spot-only, one active position per candidate, no intrabar fills.
- Every registered cell is run; no post-result parameter selection.

## Candidate HYP-0008 — Volatility-Normalized Momentum Shock

Mechanism: a large recent directional move relative to recent typical hourly movement may contain short-horizon continuation information.

Signal at t when:
- lookback absolute-return median is computed only from the previous completed bars;
- current 4-hour close-to-close return is positive and at least `K` times the previous-24-hour median absolute hourly return;
- current 4-hour return is at least `R`.

Registered grid: lookback 24/48 hours × multiplier K 2/3/4 × return threshold R 1%/1.5%/2% = 18 cells.

Entry: next eligible open. Exit: close of exactly that one eligible bar.

Invalidation: reject if the preregistered Development decision criteria fail, if the effect is not stable under fee/slippage or timing stress, or if concentration/sample-size review is materially unstable.

## Candidate HYP-0009 — Volatility-Compression Breakout

Mechanism: a compressed recent volatility state followed by a fresh upside breakout may represent a transition from information compression to directional price discovery.

Signal at t when:
- previous-12-bar realized volatility is at most C times the median realized volatility of the previous 48 completed bars;
- close[t] exceeds the maximum close of the preceding B bars by at least X;
- no lookahead information is used.

Registered grid: compression ratio C 0.5/0.7/0.9 × breakout lookback B 12/24 hours × breakout threshold X 0.1%/0.5%/1% = 27 cells.

Entry: next eligible open. Exit: close of exactly that one eligible bar.

Invalidation: same frozen Development criteria and robustness requirements.

## Candidate HYP-0010 — Two-Bar Selloff Reversal

Mechanism: two consecutive materially negative bars followed by a recovery close may indicate short-horizon selling exhaustion.

Signal at t when:
- return[t-1] <= -R;
- return[t] <= -R;
- close[t] > open[t] (recovery candle);
- optional minimum volume condition V is satisfied relative to the previous 24 completed bars.

Registered grid: selloff threshold R 0.5%/1%/1.5% × volume multiplier V 0/1.0/1.5 = 9 cells. V=0 means no volume filter and is registered, not selected post-result.

Entry: next eligible open. Exit: close of exactly that one eligible bar.

Invalidation: same frozen Development criteria and robustness requirements.

## Robustness battery

For every candidate, complete and record:

1. parameter neighborhood — every registered cell;
2. fee/slippage stress — baseline plus both registered stress cases;
3. execution timing — 1 and 2 bars;
4. regime segmentation — bull/neutral/bear using a fixed 168-hour return classification;
5. asset transferability — report BTC and ETH separately;
6. leave-one-segment-out sample stability;
7. concentration — top-10%-positive-event contribution;
8. drawdown and recovery;
9. benchmark comparison — cash and buy-and-hold on the same eligible segments.

Errors are recorded, not silently omitted. No Validation/OOS data may be accessed.

## Promotion firewall

A candidate may enter Validation only if all frozen Gate 2 mandatory criteria pass, including positive net Development performance, economic significance, sample support, cross-asset support where applicable, drawdown/segment-loss constraints, comparable benchmarks, reproducibility, and completed robustness. Validation cannot rescue a failed Development candidate.

## Cycle closure

HYP-0008 through HYP-0010 are a new research family. Results must not be used to retune the candidate after the evidence run. Any materially changed hypothesis requires a new hypothesis ID/version and a new preregistration.