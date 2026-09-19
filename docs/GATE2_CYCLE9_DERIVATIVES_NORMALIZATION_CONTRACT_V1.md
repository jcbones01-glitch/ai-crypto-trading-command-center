# Gate 2 Cycle 9 — Derivatives Normalization Implementation Contract V1

## Status

**FROZEN BEFORE FULL-HISTORY ACQUISITION**

This contract makes the already-frozen Development certification protocol
numerically and operationally explicit. It does not change the research scope,
source families, symbols, calendar, or certification decision rules.

## HTTP/source outcome contract

For each registered ZIP URL:

- make one request with a 90-second timeout;
- HTTP 404 is a source-not-found result, not a transient retry candidate;
- HTTP 404 before the stream's first accepted archive is
  `PRE_SOURCE_AVAILABILITY`;
- HTTP 404 after first accepted availability is
  `INTERIOR_COVERAGE_FAILURE`;
- non-404 HTTP errors, timeouts, connection errors, or decode errors are
  retried up to three total attempts with deterministic sleeps of 1 second
  after attempt 1 and 2 seconds after attempt 2;
- unresolved non-404 errors are `SOURCE_ACCESS_FAILURE`.

If a ZIP exists but its checksum object is missing, inaccessible, malformed, or
does not verify, the month is a source-integrity failure. It is never
reclassified as pre-source availability.

## Timestamp contract

Supported epoch precision:

- milliseconds: integer in `[10^11, 10^14)`;
- microseconds: integer in `[10^14, 10^17)`.

Canonical timestamp strings are UTC ISO-8601:

- millisecond input → `YYYY-MM-DDTHH:MM:SS.sssZ`;
- microsecond input → `YYYY-MM-DDTHH:MM:SS.ffffffZ`.

The source integer timestamp remains in the per-archive validation metadata.

## Funding spacing tolerance

For adjacent funding rows, let:

- `delta_ms` = exact difference between successive raw `calc_time` epochs;
- `expected_ms` = previous row's positive
  `funding_interval_hours * 3,600,000`.

The spacing is compatible when:

`abs(delta_ms - expected_ms) <= 1,000 milliseconds`.

This one-second tolerance is frozen before full-history acquisition. It is
only a source-cadence integrity rule; exact raw timestamps remain preserved
and are never rounded.

Any interval change supplied by the source is allowed if the adjacent spacing
satisfies the previous observation's source-supplied interval under this
tolerance.

## Decimal canonicalization

Required numeric source fields parse with Python `Decimal` and must be finite.

Canonical decimal serialization:

1. if numerical value is zero, serialize `0`;
2. otherwise normalize the Decimal and render fixed-point with `format(x, "f")`;
3. remove a trailing decimal point only if one would otherwise remain;
4. never convert through binary floating point.

Equivalent decimal source spellings therefore produce one canonical value.

## Kline close-time rule

For each hourly kline:

- `close_time > open_time`;
- `close_time < open_time + 3,600,000 milliseconds` when represented at
  millisecond precision, or the exact equivalent at microsecond precision.

The close timestamp may be the conventional final millisecond/microsecond of
the hour. It may not reach or cross the next hourly open.

## Canonical record format

Normalized stream files are UTF-8 JSON Lines.

Each line:

- uses JSON object keys in lexicographically sorted order;
- uses separators `,` and `:` with no insignificant whitespace;
- ends with LF;
- contains canonical strings for Decimal and timestamp values.

Stream normalized-data identity is SHA-256 over the **uncompressed** canonical
JSONL bytes.

Artifact copies may be gzip-compressed deterministically with `mtime=0`.
Compression bytes do not define the normalized-data identity.

## Manifest canonicalization

The candidate-month ledger is ordered by:

1. stream identifier;
2. year;
3. month.

Manifest identity uses UTF-8 canonical JSON with sorted object keys and compact
separators. Runtime durations, temporary paths, exception tracebacks, and
download timing are excluded from the identity.

Stable source outcome codes and source URLs are included.

## Failure policy

No integrity threshold in this contract may be relaxed after full-history
results. Any implementation correction must preserve the failed run and receive
a new implementation version before rerun.

## Firewall

This contract authorizes data certification only:

- Validation/OOS access: NO
- predictive testing: NO
- strategy thresholds: NO
- P&L/signals: NO
- paper/live execution: NO
