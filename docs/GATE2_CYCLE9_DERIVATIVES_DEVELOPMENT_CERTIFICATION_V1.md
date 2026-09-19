# Gate 2 Cycle 9 — Derivatives Development Dataset Certification V1

## Certification result

**DERIVATIVES_DEVELOPMENT_DATASET_CERTIFIED**

This certification covers source integrity and deterministic normalization only.
It does not establish predictability, economic edge, strategy performance, or
execution authorization.

## Provenance

- Branch: `gate2-cycle9-market-ecology-data`
- Executing/checked-out commit: `2950b7b8f8ab063f12ba97d55de6c43a264aeca1`
- Specification commit: `8c003792dcf8c4d3de4f5a24e6fb54ea9a82961b`
- Workflow: `Gate 2 Cycle 9 Derivatives Development Certification`
- Workflow run: `35436123315`
- Artifact: `gate2-cycle9-derivatives-development-v1`
- Artifact ID: `10582390406`
- Artifact digest: `sha256:46a5898721e2506d1442d2095e4da1726e4aac8561cb94ea294eb43f055c868a`
- Certification protocol SHA-256:
  `12e9e0902d7f3cacae507a79b743dc8e5b08180c7efb48fa5b6904dccec9de97`
- Normalization contract SHA-256:
  `29438ba79cf725477d1e852bc9fc172fbbb5a54a653a7dcaab85d220a252dc90`
- Combined Cycle 9 derivatives dataset identity:
  **`061c7b85e1fef9fcff1bc761f8c1198db9ae2a9e49277b8b0e80ab7ea2c56e11`**

Research firewall:
- Validation/OOS accessed: **NO**
- strategy P&L calculated: **NO**
- strategy signals generated: **NO**
- strategy thresholds searched: **NO**

## Source-native availability

The frozen calendar scan tested all 53 Development candidate months from
2017-08 through 2021-12 for each stream.

For all four streams:

- 2017-08 through 2019-12: 29 months classified
  `PRE_SOURCE_AVAILABILITY`;
- first accepted monthly archive: **2020-01**;
- 2020-01 through 2021-12: **24 / 24 accepted monthly archives**;
- no interior missing archive after availability began.

The source-native availability boundary was discovered under the frozen rule;
it was not manually entered after observing source contents.

## Certified streams

| Stream | Source manifest identity | Normalized-data identity | Rows | First | Last |
| --- | --- | --- | ---: | --- | --- |
| BTCUSDT futures 1h | `80484ae0c3ff033592fe9770c6dda4f351f06ceb584529ec498278733b70a98e` | `6ec4f168e97736d6a5481280e82eb0b56eb5a5247e113d2467e7f31d473b5ea0` | 17,544 | 2020-01-01 00:00 UTC | 2021-12-31 23:00 UTC |
| BTCUSDT funding | `ecb6f0047c0354a1bd187147a1fe980c49aecdfa8fe246320b0a1f57b3eac8dc` | `afa2f2a40031e4d4000c3e0f79f83f210d104e49b33876eaeb506a92b716aa08` | 2,193 | 2020-01-01 00:00 UTC | 2021-12-31 16:00 UTC |
| ETHUSDT futures 1h | `7c4a74db4881e8f35d3fc31b31d994b3f5a03f093d6283b9236951ec7be6bdf6` | `51c5accee0ae609be005fdeeb744dbfe64a6e5a7f35a3bb5cb96cc2439430745` | 17,544 | 2020-01-01 00:00 UTC | 2021-12-31 23:00 UTC |
| ETHUSDT funding | `3f72af848a189637cc9b94a9a6d5e46171ecf6fd658885d88c39c92683575789` | `61ebc26000bee2452e15b79487a6fb6ec202e6a4e717a00f30c9bfd4a57759a2` | 2,193 | 2020-01-01 00:00 UTC | 2021-12-31 16:00 UTC |

## Continuity and integrity

### Futures 1-hour klines

Both BTCUSDT and ETHUSDT:

- 17,544 normalized hourly rows;
- zero duplicate primary timestamps;
- zero missing hourly opens from 2020-01-01 00:00 through
  2021-12-31 23:00 UTC;
- all accepted archives/checksums passed;
- millisecond timestamp precision throughout all 24 accepted months.

### Funding

Both BTCUSDT and ETHUSDT:

- 2,193 normalized observations;
- zero duplicate primary timestamps;
- zero funding-spacing failures under the frozen one-second source-cadence
  tolerance;
- all 24 accepted monthly archives reported source
  `funding_interval_hours = 8`;
- millisecond timestamp precision throughout.

The 8-hour observation is a fact about this certified Development dataset, not
a permanent assumption for future data.

Exact funding `calc_time` values remain preserved. The feature layer may not
round a funding record backward to a nominal boundary.

## Deterministic normalized artifacts

The workflow artifact contains deterministic gzip-compressed canonical JSONL
for all four streams plus the complete 53-month-per-stream source ledger.

Uncompressed JSONL SHA-256 equals each stream's normalized-data identity.

Deterministic gzip SHA-256:

- BTCUSDT kline:
  `abf6b9cf0a4dd0559b728cbae5ac1950477a32bb207fae76f77279b76d0da9fd`
- BTCUSDT funding:
  `a5615138ba6081fd81dfee31d5a2a001bd643a36c77f7750f1c04ba9e1f0630c`
- ETHUSDT kline:
  `158a3826ab3eff2b0bc64bee396e2139fd72bce8e536de8355d4211799a9e96b`
- ETHUSDT funding:
  `c2355ea98b77b507f7458a1c706bba20bc6fab2ac6c5a278795f32a3a9bb33b7`

## Interpretation

Cycle 9 now has a certified Development-only source for two economically
distinct derivatives-market observations:

- futures market prices/activity;
- perpetual funding/carrying pressure.

This materially broadens the information set beyond spot OHLCV, consistent
with the Andrew Lo / Adaptive Markets market-ecology direction.

It does **not** tell us whether funding, futures basis, or any derivative
variable predicts future crypto returns.

## Next gate

Before using these data in research, define and freeze deterministic,
point-in-time-safe market-ecology feature semantics.

The feature-definition stage may calculate transformations such as a
futures-vs-spot basis only after specifying:

- exact certified source identities;
- timestamp alignment and availability;
- formula and numeric representation;
- missing-data behavior;
- no-look-ahead rules;
- dataset/feature identity.

It may not inspect forward returns or optimize thresholds.

Any later predictive or trading experiment requires a separate economic
mechanism, prospective preregistration, multiplicity accounting, and the
existing evidence gates.

## Decision

**DERIVATIVES DEVELOPMENT DATA CERTIFICATION: PASS**

No Validation/OOS, strategy promotion, paper trading, or live trading is
authorized.
