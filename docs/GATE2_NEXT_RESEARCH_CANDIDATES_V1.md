# Gate 2 — Next Research Candidates V1

## Status

**DISCOVERY ONLY — NO BACKTEST EVIDENCE**

This document defines genuinely new research hypotheses after the HYP-0001 through HYP-0004 development/robustness cycle. It does not modify, rescue, retune, or relabel any prior hypothesis.

The governing Gate 2 protocol remains unchanged: Development only; Validation and locked OOS remain inaccessible for discovery and selection. A hypothesis is not evidence of an edge until it is separately preregistered and tested.

## Prior-cycle boundary

The prior candidates HYP-0001 through HYP-0004 are closed for this research cycle after the recorded robustness failure. Their parameter spaces must not be reused as an optimization exercise. Any materially different strategy receives a new hypothesis ID and version.

## Candidate screening standard

A candidate is retained only if it has:

- a distinct proposed mechanism rather than a parameter variation of the prior families;
- inputs available from the current certified BTCUSDT/ETHUSDT 1-hour Spot dataset, or a clearly identified new data requirement;
- deterministic rules that can be implemented without discretionary interpretation;
- a causal execution specification using information available at the signal close and a later executable price;
- explicit failure modes and falsification criteria;
- a realistic path to preregistration before any candidate backtest is treated as evidence.

No candidate below has been backtested as part of this document.

---

## HYP-0005 — Volume-Shock Directional Persistence

### Falsifiable statement

When an hourly crypto bar closes with an unusually large trading-volume shock and a positive directional price response, the probability and magnitude of a positive return over the next eligible hourly bar will be greater than the corresponding unconditional return distribution; the effect should persist after explicit transaction costs and directional slippage.

The converse negative-volume-shock/directional condition is not assumed to work and is a separate hypothesis if later justified.

### Proposed mechanism

A large increase in participation accompanied by directional price movement may represent information arrival, broad market participation, or forced repositioning that takes more than one hour to be fully incorporated.

This is a **volume-confirmation / participation** hypothesis, not a trailing-return momentum rule.

### Deterministic model concept

For each asset independently:

1. At close `t`, calculate current volume relative to a trailing volume baseline using only bars ending at or before `t`.
2. Calculate the current bar's close-to-close return.
3. Define a volume shock and directional threshold in the preregistration; no threshold is selected after seeing results.
4. Enter long only when both the volume-shock and positive-direction conditions are satisfied.
5. Execute at the next eligible bar open with registered commission and directional slippage.
6. Exit according to a fixed, preregistered holding rule rather than discretionary observation.
7. Never bridge a Gate 1A continuity break.

### Required data

Existing certified 1-hour OHLCV fields are sufficient: timestamp, close, and volume at minimum.

### Key confounds

- volume is strongly state-dependent and may proxy for volatility;
- exchange-wide volume spikes can coincide with large market moves;
- the effect could disappear after realistic costs;
- repeated threshold testing could manufacture apparent significance.

### Explicit invalidation criteria

The hypothesis should be rejected if the preregistered development test fails to show positive net expectancy relative to its benchmark, if the effect disappears under modest cost/slippage stress, if timing degradation destroys the effect, or if the apparent result is concentrated in too few segments/trades.

### Preregistration requirement

Before any evidence-generating backtest, freeze the exact volume baseline definition, shock thresholds, holding/exit rule, cost/slippage assumptions, timing, benchmarks, robustness battery, and decision thresholds.

---

## HYP-0006 — Cross-Asset BTC Lead/Lag Response

### Falsifiable statement

A sufficiently large BTCUSDT hourly return that is not contemporaneously matched by ETHUSDT will contain predictive information about ETHUSDT's next eligible hourly return, beyond the predictive information contained in ETH's own immediately available return.

This is a **cross-asset lead/lag** hypothesis rather than a single-asset momentum or mean-reversion hypothesis.

### Proposed mechanism

BTC is the larger and more widely followed crypto asset. A market-wide information shock may first appear in BTC and then propagate into ETH as correlated participants update positions. The test asks whether measurable lagged transmission exists rather than assuming it does.

### Deterministic model concept

At a synchronized hourly close `t`:

1. Compute BTC's close-to-close return using only data through `t`.
2. Compute ETH's corresponding return through `t`.
3. Define a preregistered condition for a BTC directional shock and a relative-response gap between BTC and ETH.
4. If the condition is satisfied, generate an ETH long signal for the next eligible bar.
5. Execute at ETH's next eligible open with registered costs and directional slippage.
6. Require synchronized certified continuity for the BTC and ETH observations used by the signal.
7. Do not infer or fill a missing bar in either asset.

A short ETH leg is **not** assumed. The initial research implementation remains spot-only and long-only.

### Required data

Existing certified BTCUSDT and ETHUSDT 1-hour close/OHLCV data, synchronized on canonical hourly timestamps.

### Key confounds

- BTC and ETH returns are correlated, so the apparent effect may be common-factor exposure rather than lead/lag;
- timestamp alignment errors could create false prediction;
- large shocks may be rare, reducing sample size;
- selection of shock/gap thresholds is highly vulnerable to multiple testing.

### Explicit invalidation criteria

Reject if the effect does not exceed the preregistered benchmark after costs, if it disappears when execution is delayed by one additional bar, if synchronized continuity restrictions materially eliminate the sample, or if the result is attributable to a small number of shock events.

### Preregistration requirement

Freeze the shock definition, relative-response definition, direction, holding/exit rule, synchronized eligibility rule, cost/slippage assumptions, timing, benchmarks, robustness tests, and decision rule before evidence-generating backtests.

---

## HYP-0007 — Volume-Capitulation Reversal

### Falsifiable statement

After an unusually high-volume hourly selloff, when the magnitude of the negative return is large relative to recent activity, the next eligible hourly return will have a positive conditional mean that exceeds the unconditional baseline after costs and slippage.

This is a **capitulation / liquidity-event reversal** hypothesis. It is not a parameter variation of HYP-0002 because the proposed mechanism requires an abnormal volume event jointly with the directional shock.

### Proposed mechanism

A sharp selloff accompanied by exceptional participation may include forced liquidation, panic selling, or temporary liquidity imbalance. If sellers become exhausted, subsequent buying pressure could produce a short-horizon rebound.

The hypothesis is deliberately agnostic about whether this mechanism exists in crypto; the test is intended to falsify it.

### Deterministic model concept

For each asset independently:

1. At close `t`, calculate the current hourly return.
2. Calculate current volume relative to a trailing volume baseline using only information available through `t`.
3. Trigger only when both the negative-return shock and abnormal-volume conditions meet preregistered thresholds.
4. Enter long at the next eligible bar open.
5. Exit using a fixed preregistered holding/exit rule.
6. Treat continuity breaks as research boundaries and never manufacture missing observations.

### Required data

Existing certified 1-hour OHLCV fields are sufficient.

### Key confounds

- this may simply rediscover ordinary short-term mean reversion;
- volume shocks can be correlated with volatility regimes;
- extreme events are sparse and can dominate aggregate results;
- threshold selection creates substantial multiple-testing risk.

### Explicit invalidation criteria

Reject if the conditional return is not positive after costs, if the result fails modest cost/slippage stress, if it is unstable across BTC and ETH, if delayed execution removes the effect, or if concentration analysis shows that a small number of events account for the result.

### Preregistration requirement

Freeze the volume baseline, negative-return shock threshold, volume threshold, holding/exit rule, timing, costs/slippage, benchmarks, robustness cells, and decision rule before testing.

---

## Candidate ranking for preregistration consideration

This is a **research-priority ranking, not a performance ranking**. No candidate has Development evidence yet.

| Priority | Hypothesis | Why it merits testing | Main risk |
|---|---|---|---|
| 1 | HYP-0006 Cross-Asset BTC Lead/Lag | Uses existing BTC/ETH data and tests a genuinely cross-asset mechanism | Correlation can masquerade as lead/lag |
| 2 | HYP-0005 Volume-Shock Directional Persistence | Tests whether participation adds information beyond price-only rules | Volume may simply proxy for volatility |
| 3 | HYP-0007 Volume-Capitulation Reversal | Tests a distinct event-driven reversal mechanism using existing data | Could collapse into ordinary mean reversion |

## Deliberately excluded from this cycle

- Parameter variations of HYP-0001 through HYP-0004.
- Any candidate requiring inspection of Validation or locked OOS results.
- Any candidate whose rules depend on discretionary chart interpretation.
- Funding-rate/carry hypotheses requiring a new derivatives dataset; those may be researched in a separate data-expansion phase.
- Strategies requiring leverage, shorting, or live execution.

## Next gate

No candidate should be backtested as preregistered evidence yet.

The next research action is to convert the strongest candidate set into a **new prospective preregistration** with exact parameter grids, decision rules, benchmark definitions, and robustness tests. Only after that registration is frozen may the corresponding Development experiments run.

**Classification:** OBSERVATION/RESEARCH HYPOTHESES ONLY — NOT BACKTEST RESULTS — NOT PROVEN EDGE.
