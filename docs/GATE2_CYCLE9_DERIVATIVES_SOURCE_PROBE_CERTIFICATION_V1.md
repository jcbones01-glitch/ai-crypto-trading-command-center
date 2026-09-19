# Gate 2 Cycle 9 — Derivatives Source Probe Certification V1

## Certification result

**DERIVATIVES_SOURCE_PROBE_PASS**

This is a source/data-quality certification only. It does not establish predictive
value, profitability, strategy eligibility, or execution authorization.

## Provenance

- Branch: `gate2-cycle9-market-ecology-data`
- Executing/checked-out commit: `30f2d4a4283ef53f9517e2c612a689ef344ce46b`
- Workflow: `Gate 2 Cycle 9 Derivatives Source Probe`
- Workflow run: `35435886941`
- Artifact: `gate2-cycle9-derivatives-source-probe-v1`
- Artifact ID: `10581239140`
- Artifact digest: `sha256:8d76c7273783c4417dc9f83bd55e829d53d5a9bc9814f083a5c96ceae533d740`
- Registered archive count: 8
- Passed: **8 / 8**
- Validation/OOS accessed: **NO**
- Strategy P&L calculated: **NO**
- Strategy signals generated: **NO**

All registered ZIP archives downloaded from the preregistered Binance Data
Collection USD-M Futures paths, all corresponding `.CHECKSUM` objects
downloaded, and all checksums verified.

## Observed source contract

### Monthly USD-M 1-hour futures klines

Observed for BTCUSDT and ETHUSDT in both registered months (2021-01, 2021-06):

- exactly one CSV member per ZIP;
- **no CSV header**;
- 12 source columns;
- source schema interpreted under the preregistered fixed Binance kline field
  order;
- open and close timestamps represented in milliseconds;
- open timestamps exactly on UTC-hour boundaries;
- strictly increasing open timestamps;
- zero duplicate timestamps;
- zero malformed rows;
- OHLC/volume integrity checks passed.

Registered-month row counts:

| Symbol | Month | Rows |
| --- | --- | ---: |
| BTCUSDT | 2021-01 | 744 |
| BTCUSDT | 2021-06 | 720 |
| ETHUSDT | 2021-01 | 744 |
| ETHUSDT | 2021-06 | 720 |

### Monthly funding-rate archives

Observed header for both assets and both months:

`calc_time,funding_interval_hours,last_funding_rate`

Observed properties:

- timestamps represented in milliseconds;
- explicit `funding_interval_hours = 8` on every probed row;
- strictly increasing timestamps;
- zero duplicates;
- zero malformed rows;
- finite funding-rate values;
- 93 rows in January 2021 and 90 rows in June 2021 for each asset.

The raw `calc_time` is not always exactly on the nominal 8-hour boundary.
Examples in the registered probe include offsets of 1–5 milliseconds. Integer
second-spacing summaries therefore included both 28,799 and 28,800 seconds.

**Normalization rule implied by this observation:** preserve the exact raw
funding timestamp and its millisecond precision. Do not round a funding record
backward to the nominal 00:00/08:00/16:00 boundary for point-in-time research.
Any later feature must become visible no earlier than its certified raw
`calc_time`.

The presence of an explicit interval field means later ingestion must use the
source-supplied interval rather than assume that all historical observations
are always 8-hour intervals.

## Registered archive hashes

| Kind | Symbol | Month | SHA-256 |
| --- | --- | --- | --- |
| kline | BTCUSDT | 2021-01 | `00de1eb2f3e3bc7f21b7ab321f1681385726fe7ba55306a7337acfd8f81fedfa` |
| funding | BTCUSDT | 2021-01 | `cff916dc4b638ec3de97828e8911cd91cf7d7a3d0836ec0175869c374e66823d` |
| kline | BTCUSDT | 2021-06 | `5134cef4361e0819b721776da6e99f715141d122e3cfbf4be729e3dfc153ac33` |
| funding | BTCUSDT | 2021-06 | `7b8d9bfb8816636b800764dafb2aa2307d19166c695bfa245adbf7d01d61f766` |
| kline | ETHUSDT | 2021-01 | `52b01b6937e57c3299003a91ec93fe8c2560b1ee6cacb24a60c110bf696b6118` |
| funding | ETHUSDT | 2021-01 | `4c18c1df8904dea9770aeba5326d26b3fa9a3ffac4891f5f7125d4be2da847c0` |
| kline | ETHUSDT | 2021-06 | `625a8c04b76cc9fa096599bd1498b24b28ea31d9900dfddb86995046bd6b2ebf` |
| funding | ETHUSDT | 2021-06 | `8e58ccf8f52c69c55754492daafadab92d4ca8c8bd027f4532582d06e9f36063` |

## Decision

The registered probe satisfies the V1 completion rule.

**Next permitted action:** prospectively define and freeze a full-history
Development ingestion/certification protocol before downloading the additional
historical archive set.

No strategy test, threshold search, AMS-V1 conditioning, Validation/OOS access,
paper trading, or live execution is authorized by this certification.
