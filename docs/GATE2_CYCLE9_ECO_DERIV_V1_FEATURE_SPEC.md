# Gate 2 Cycle 9 — ECO-DERIV-V1 Market-Ecology Feature Specification

## Status

**FROZEN BEFORE FEATURE GENERATION**

This specification defines the first deterministic market-ecology feature layer
built from already-certified Development data.

It is infrastructure, not a predictive experiment or trading strategy.

## Certified inputs

### Spot

Binance Spot 1-hour Gate 1A-certified Development data:

- BTCUSDT dataset identity:
  `1590cf8e69ed757eeb6701a218d561448beb2eb6ea09dcd0ae31d15a8f5197cf`
- ETHUSDT dataset identity:
  `d35bf21e309820abc88090bad29601adc1d1ea6b31dcddf0b80d510af4cf542f`

Only observations accepted by the existing Gate 1A treatment/continuity
pipeline may enter the feature layer.

### Derivatives

Cycle 9 derivatives Development dataset identity:

`061c7b85e1fef9fcff1bc761f8c1198db9ae2a9e49277b8b0e80ab7ea2c56e11`

Certified stream normalized-data identities:

- BTCUSDT futures: `6ec4f168e97736d6a5481280e82eb0b56eb5a5247e113d2467e7f31d473b5ea0`
- BTCUSDT funding: `afa2f2a40031e4d4000c3e0f79f83f210d104e49b33876eaeb506a92b716aa08`
- ETHUSDT futures: `51c5accee0ae609be005fdeeb744dbfe64a6e5a7f35a3bb5cb96cc2439430745`
- ETHUSDT funding: `61ebc26000bee2452e15b79487a6fb6ec202e6a4e717a00f30c9bfd4a57759a2`

Derivatives source-native availability begins 2020-01-01 and ends with the
Development boundary at 2022-01-01.

No source identity may be silently recertified or substituted.

## Feature-time convention

For an hourly spot/futures bar whose source open timestamp is `t`:

- its close is treated as available at `t + 1 hour`;
- the ECO-DERIV-V1 feature timestamp is that availability time;
- spot and futures bars must have the exact same source open timestamp;
- both bars must be certified and inside Development.

No feature row is emitted from a nonmatching or uncertified timestamp.

## Feature 1 — Perpetual futures log basis

At feature time `t + 1h`:

`LOG_BASIS = ln(FUTURES_CLOSE_t / SPOT_CLOSE_t)`

where both closes are from the same hourly source-open timestamp `t`.

Rules:

- both closes must be strictly positive;
- calculation uses Python `Decimal` arithmetic and `Decimal.ln()`;
- output is serialized as a deterministic canonical Decimal string;
- no annualization;
- no threshold, sign classification, percentile, clipping, winsorization,
  smoothing, or parameter search.

Interpretation is limited to contemporaneous futures-vs-spot price
dislocation/carry context. It is not a forecast.

## Feature 2 — Exact-as-of last known funding observation

For each hourly feature timestamp `T`, select the funding record with the
greatest certified raw `calc_time <= T`.

Store:

- `last_funding_calc_time`;
- `last_funding_rate`;
- `last_funding_interval_hours`;
- `funding_age_microseconds = T - last_funding_calc_time`.

Rules:

- exact raw millisecond/microsecond timing is preserved;
- a funding record a few milliseconds **after** an hourly feature timestamp is
  not visible at that timestamp;
- no backward rounding to a nominal 00:00/08:00/16:00 boundary;
- no interpolation between funding observations;
- no averaging or cumulative-funding window;
- if no certified funding observation is yet available, the hourly feature row
  is not complete and is omitted from the complete feature dataset.

Using the most recently published funding observation is an as-of join, not a
claim that its economic effect persists for any particular horizon. The age
field makes staleness explicit.

## Complete ECO-DERIV-V1 row

Canonical fields:

- `symbol`
- `spot_open_time`
- `feature_available_at`
- `spot_close`
- `futures_close`
- `log_basis`
- `last_funding_calc_time`
- `last_funding_rate`
- `last_funding_interval_hours`
- `funding_age_microseconds`

A row is complete only when all listed fields are available under the causal
rules above.

## Dataset scope

The possible feature period is the intersection of:

- certified spot Development observations;
- certified futures Development observations;
- at least one causally available certified funding observation.

No row before source-native derivatives availability can be synthesized.

No row at or after `2022-01-01T00:00:00Z` may be emitted.

## Continuity and missing-data rules

- never forward-fill a missing spot or futures bar;
- never synthesize a basis across a gap;
- funding uses only the explicit exact-as-of rule above;
- report every omitted hourly timestamp after derivatives availability and its
  reason;
- report feature coverage by asset and exact first/last complete timestamp;
- do not repair missing input data merely to increase coverage.

## Numerical/canonical representation

- input prices/rates remain Decimal;
- canonical Decimal strings use the Cycle 9 normalization convention;
- canonical timestamps are UTC ISO-8601;
- `funding_age_microseconds` is a non-negative integer;
- feature rows are UTF-8 canonical JSON Lines with sorted keys/compact
  separators/LF;
- feature identity is SHA-256 over uncompressed canonical JSONL bytes.

## Integrity tests required before certification

1. futures basis at time T uses only spot/futures bars closed no later than T;
2. a future price mutation cannot change an already emitted earlier feature;
3. funding record with `calc_time > T` is excluded;
4. funding record with `calc_time <= T` may be selected only if it is the
   latest such certified record;
5. millisecond-offset funding immediately after T is deferred until a later
   feature timestamp;
6. exact timestamp mismatch between spot and futures bars does not produce a
   row;
7. nonpositive price fails closed;
8. expected input dataset identities are verified before feature generation;
9. Validation/OOS cannot be requested/read;
10. no forward-return, signal, threshold, or P&L field exists.

## Registered outputs

For each asset:

- expected input identities;
- spot/futures exact timestamp intersection count;
- complete feature row count;
- omitted row counts by reason;
- first/last complete feature timestamp;
- feature JSONL identity.

Combined ECO-DERIV-V1 identity is SHA-256 over:

- this specification SHA-256;
- both certified spot dataset identities;
- certified combined derivatives identity;
- BTC feature identity;
- ETH feature identity.

Do **not** report or rank favorable feature values, thresholds, future-return
relationships, Sharpe ratios, or state-conditioned performance in this
certification.

## Allowed status

- `ECO_DERIV_V1_READY`
- `ECO_DERIV_V1_INVALID`

READY is infrastructure only.

## Andrew Lo / Adaptive Markets rationale

The feature layer operationalizes two observable components of market ecology:

- carrying/positioning pressure through funding;
- futures-versus-spot relative pricing through basis.

It does not assume those variables predict returns. A later hypothesis must
state an economic mechanism and be prospectively registered before any
forward-return relationship is inspected.

## Final authorization

**IMPLEMENTATION AND FEATURE CERTIFICATION MAY PROCEED EXACTLY AS SPECIFIED.
NO PREDICTIVE OR TRADING TEST IS AUTHORIZED.**
