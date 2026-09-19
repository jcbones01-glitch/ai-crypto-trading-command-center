from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Iterable, Mapping, Sequence

HOUR_US = 3_600_000_000
DECIMAL_PRECISION = 50


class MarketEcologyError(ValueError):
    """Invalid or causally unavailable market-ecology input."""


@dataclass(frozen=True)
class SpotPoint:
    open_epoch_us: int
    close: Decimal


@dataclass(frozen=True)
class FuturesPoint:
    open_epoch_us: int
    close: Decimal


@dataclass(frozen=True)
class FundingPoint:
    calc_epoch_us: int
    rate: Decimal
    interval_hours: Decimal
    calc_time_text: str


def canonical_decimal(value: Decimal | str) -> str:
    try:
        number = value if isinstance(value, Decimal) else Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise MarketEcologyError("invalid decimal") from exc
    if not number.is_finite():
        raise MarketEcologyError("non-finite decimal")
    if number == 0:
        return "0"
    return format(number.normalize(), "f")


def iso_to_epoch_us(text: str) -> int:
    if not isinstance(text, str) or not text.endswith("Z"):
        raise MarketEcologyError("UTC Z timestamp required")
    try:
        stamp = datetime.fromisoformat(text[:-1] + "+00:00")
    except ValueError as exc:
        raise MarketEcologyError("invalid ISO timestamp") from exc
    if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
        raise MarketEcologyError("UTC timestamp required")
    epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
    delta = stamp - epoch
    return (
        delta.days * 86_400_000_000
        + delta.seconds * 1_000_000
        + delta.microseconds
    )


def hourly_iso(epoch_us: int) -> str:
    if isinstance(epoch_us, bool) or not isinstance(epoch_us, int):
        raise MarketEcologyError("integer epoch microseconds required")
    if epoch_us < 0 or epoch_us % HOUR_US != 0:
        raise MarketEcologyError("exact UTC hour required")
    seconds, micros = divmod(epoch_us, 1_000_000)
    stamp = datetime.fromtimestamp(seconds, tz=timezone.utc).replace(microsecond=micros)
    return stamp.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def log_basis(spot_close: Decimal, futures_close: Decimal) -> Decimal:
    if not isinstance(spot_close, Decimal) or not isinstance(futures_close, Decimal):
        raise MarketEcologyError("Decimal prices required")
    if not spot_close.is_finite() or not futures_close.is_finite():
        raise MarketEcologyError("finite prices required")
    if spot_close <= 0 or futures_close <= 0:
        raise MarketEcologyError("strictly positive prices required")
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        context.rounding = ROUND_HALF_EVEN
        return +(futures_close / spot_close).ln()


def canonical_jsonl(rows: Iterable[Mapping]) -> bytes:
    chunks = []
    for row in rows:
        chunks.append(
            json.dumps(
                dict(row),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
            + b"\n"
        )
    return b"".join(chunks)


def feature_identity(rows: Iterable[Mapping]) -> str:
    return hashlib.sha256(canonical_jsonl(rows)).hexdigest()


def _validate_unique_sorted(points: Sequence, field: str) -> None:
    values = [getattr(point, field) for point in points]
    if any(isinstance(v, bool) or not isinstance(v, int) for v in values):
        raise MarketEcologyError("integer epoch values required")
    if any(a >= b for a, b in zip(values, values[1:])):
        raise MarketEcologyError("timestamps must be unique and strictly increasing")


def build_eco_deriv_rows(
    symbol: str,
    spot_points: Sequence[SpotPoint],
    futures_points: Sequence[FuturesPoint],
    funding_points: Sequence[FundingPoint],
    protected_boundary_epoch_us: int,
) -> tuple[list[dict], dict]:
    """Create point-in-time ECO-DERIV-V1 rows.

    Candidate hours are certified futures opens. Spot must match exactly.
    Funding is an exact <= feature-time as-of join.
    """
    if symbol not in {"BTCUSDT", "ETHUSDT"}:
        raise MarketEcologyError("unsupported symbol")
    if isinstance(protected_boundary_epoch_us, bool) or not isinstance(
        protected_boundary_epoch_us, int
    ):
        raise MarketEcologyError("integer protected boundary required")

    _validate_unique_sorted(spot_points, "open_epoch_us")
    _validate_unique_sorted(futures_points, "open_epoch_us")
    _validate_unique_sorted(funding_points, "calc_epoch_us")

    spot_by_epoch = {point.open_epoch_us: point for point in spot_points}
    exact_intersection_count = sum(
        point.open_epoch_us in spot_by_epoch for point in futures_points
    )

    output: list[dict] = []
    omitted = {
        "spot_unavailable_or_uncertified": 0,
        "funding_not_yet_available": 0,
        "feature_at_or_after_protected_boundary": 0,
    }

    funding_i = -1
    last_funding: FundingPoint | None = None

    for future in futures_points:
        if future.open_epoch_us % HOUR_US != 0:
            raise MarketEcologyError("futures open must be exact hour")

        feature_epoch = future.open_epoch_us + HOUR_US
        while (
            funding_i + 1 < len(funding_points)
            and funding_points[funding_i + 1].calc_epoch_us <= feature_epoch
        ):
            funding_i += 1
            last_funding = funding_points[funding_i]

        if feature_epoch >= protected_boundary_epoch_us:
            omitted["feature_at_or_after_protected_boundary"] += 1
            continue

        spot = spot_by_epoch.get(future.open_epoch_us)
        if spot is None:
            omitted["spot_unavailable_or_uncertified"] += 1
            continue

        if spot.open_epoch_us != future.open_epoch_us:
            raise MarketEcologyError("spot/futures timestamp mismatch")

        if last_funding is None:
            omitted["funding_not_yet_available"] += 1
            continue

        funding_age = feature_epoch - last_funding.calc_epoch_us
        if funding_age < 0:
            raise MarketEcologyError("negative funding age")

        basis = log_basis(spot.close, future.close)
        row = {
            "feature_available_at": hourly_iso(feature_epoch),
            "funding_age_microseconds": funding_age,
            "futures_close": canonical_decimal(future.close),
            "last_funding_calc_time": last_funding.calc_time_text,
            "last_funding_interval_hours": canonical_decimal(last_funding.interval_hours),
            "last_funding_rate": canonical_decimal(last_funding.rate),
            "log_basis": canonical_decimal(basis),
            "spot_close": canonical_decimal(spot.close),
            "spot_open_time": hourly_iso(spot.open_epoch_us),
            "symbol": symbol,
        }
        output.append(row)

    if len({row["feature_available_at"] for row in output}) != len(output):
        raise MarketEcologyError("duplicate feature timestamps")

    diagnostics = {
        "futures_candidate_hour_count": len(futures_points),
        "spot_futures_exact_timestamp_intersection_count": exact_intersection_count,
        "complete_feature_row_count": len(output),
        "omitted_by_reason": omitted,
        "first_complete_feature_timestamp": (
            output[0]["feature_available_at"] if output else None
        ),
        "last_complete_feature_timestamp": (
            output[-1]["feature_available_at"] if output else None
        ),
    }
    return output, diagnostics
