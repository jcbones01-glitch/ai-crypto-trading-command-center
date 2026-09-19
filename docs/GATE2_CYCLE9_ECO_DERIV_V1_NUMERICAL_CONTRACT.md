# Gate 2 Cycle 9 — ECO-DERIV-V1 Numerical Contract

## Status

**FROZEN BEFORE FEATURE GENERATION**

This contract makes the frozen ECO-DERIV-V1 feature specification numerically
deterministic.

## Decimal arithmetic

All basis calculations use Python `Decimal` under a local decimal context:

- precision: **50 decimal digits**
- rounding: `ROUND_HALF_EVEN`

For positive futures close `F` and spot close `S`:

`log_basis = ln(F / S)`

The division and natural logarithm occur inside the same 50-digit local
context.

The resulting Decimal is canonicalized using the Cycle 9 canonical Decimal
rule:

- zero → `0`;
- otherwise `format(value.normalize(), "f")`;
- no binary-float conversion.

No quantization to a shorter display precision is permitted before feature
identity calculation.

## Timestamp representation

Spot/futures source-open timestamps and hourly feature-availability timestamps
serialize as:

`YYYY-MM-DDTHH:MM:SS.000Z`

Funding timestamps retain their certified source precision.

Funding age is exact integer microseconds between the feature timestamp and
selected funding `calc_time`.

## As-of join ordering

Funding observations are ordered by exact certified epoch time.

For feature availability time `T`, select the greatest funding epoch
satisfying:

`funding_epoch <= T`.

Ties are not permitted because the certified funding stream contains no
duplicate primary timestamps.

No epsilon, rounding tolerance, or nominal funding-boundary adjustment is
applied to the as-of selection.

## Feature canonicalization

Each complete feature row is serialized as compact sorted-key UTF-8 JSON plus
LF.

Per-asset feature identity:

SHA-256(uncompressed canonical JSONL bytes).

Combined ECO-DERIV-V1 identity:

SHA-256 of compact sorted-key canonical JSON containing exactly:

- `feature_spec_sha256`;
- `spot_dataset_identities` for BTCUSDT and ETHUSDT;
- `derivatives_combined_dataset_identity`;
- `feature_identities` for BTCUSDT and ETHUSDT.

No runtime metadata enters a feature identity.

## Failure behavior

Nonpositive prices, nonfinite Decimals, duplicate feature timestamps, negative
funding age, source identity mismatch, protected-partition access, or
unexpected timestamp ordering fail closed.

No numerical setting in this contract may be changed after feature values are
generated without a new feature-layer version.
