from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zipfile import ZipFile

from research_core.data_ingestion import parse_timestamp, verify_sha256_bytes

PREREG = Path("docs/GATE2_CYCLE9_DERIVATIVES_SOURCE_PROBE_PREREGISTRATION_V1.md")
ROOT = Path(__file__).resolve().parents[1]
SYMBOLS = ("BTCUSDT", "ETHUSDT")
MONTHS = ((2021, 1), (2021, 6))

KLINE_FIELDS = (
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_asset_volume",
    "number_of_trades",
    "taker_buy_base_asset_volume",
    "taker_buy_quote_asset_volume",
    "ignore",
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch(url: str) -> bytes:
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=90) as response:
                return response.read()
        except Exception as exc:
            last = exc
            if attempt < 2:
                time.sleep(2 ** attempt)
    raise last


def kline_url(symbol: str, year: int, month: int) -> str:
    stamp = f"{year:04d}-{month:02d}"
    return (
        "https://data.binance.vision/data/futures/um/monthly/klines/"
        f"{symbol}/1h/{symbol}-1h-{stamp}.zip"
    )


def funding_url(symbol: str, year: int, month: int) -> str:
    stamp = f"{year:04d}-{month:02d}"
    return (
        "https://data.binance.vision/data/futures/um/monthly/fundingRate/"
        f"{symbol}/{symbol}-fundingRate-{stamp}.zip"
    )


def _rows_from_zip(payload: bytes):
    with ZipFile(io.BytesIO(payload)) as archive:
        members = [name for name in archive.namelist() if not name.endswith("/")]
        if len(members) != 1:
            raise ValueError(f"expected one data member, found {len(members)}")
        member = members[0]
        text = archive.read(member).decode("utf-8")
    rows = list(csv.reader(text.splitlines()))
    return member, rows


def _looks_integer(value: str) -> bool:
    return bool(re.fullmatch(r"[+-]?\d+", value.strip()))


def _normalized_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.strip().lower())


def parse_epoch_timestamp(value: str):
    integer = int(value)
    if 10**11 <= integer < 10**14:
        unit, divisor = "milliseconds", 1_000
    elif 10**14 <= integer < 10**17:
        unit, divisor = "microseconds", 1_000_000
    else:
        raise ValueError("unsupported timestamp precision")
    seconds, remainder = divmod(integer, divisor)
    microseconds = remainder * 1_000 if unit == "milliseconds" else remainder
    return datetime.fromtimestamp(seconds, tz=timezone.utc).replace(microsecond=microseconds), unit


def probe_kline(payload: bytes) -> dict:
    member, rows = _rows_from_zip(payload)
    if not rows:
        raise ValueError("empty CSV")

    header_present = not _looks_integer(rows[0][0])
    header = rows[0] if header_present else None
    data_rows = rows[1:] if header_present else rows

    malformed = 0
    parsed = []
    timestamp_units = Counter()

    for row in data_rows:
        try:
            if len(row) != 12:
                raise ValueError("unexpected kline column count")
            open_ts, open_unit = parse_timestamp(row[0])
            close_ts, close_unit = parse_epoch_timestamp(row[6])
            values = [Decimal(row[i]) for i in (1, 2, 3, 4, 5)]
            open_, high, low, close, volume = values
            if min(open_, high, low, close) <= 0:
                raise ValueError("non-positive OHLC")
            if volume < 0:
                raise ValueError("negative volume")
            if not (low <= open_ <= high and low <= close <= high):
                raise ValueError("invalid OHLC relationship")
            if not (
                open_ts.minute == 0
                and open_ts.second == 0
                and open_ts.microsecond == 0
            ):
                raise ValueError("open timestamp not exact UTC hour")
            parsed.append((open_ts, close_ts))
            timestamp_units[(open_unit, close_unit)] += 1
        except (ValueError, InvalidOperation, OverflowError):
            malformed += 1

    open_times = [item[0] for item in parsed]
    duplicate_count = len(open_times) - len(set(open_times))
    strictly_increasing = all(a < b for a, b in zip(open_times, open_times[1:]))

    passed = bool(parsed) and malformed == 0 and duplicate_count == 0 and strictly_increasing
    return {
        "member": member,
        "header_present": header_present,
        "header": header,
        "schema": list(KLINE_FIELDS) if not header_present else header,
        "source_column_count": len(data_rows[0]) if data_rows else 0,
        "raw_row_count": len(data_rows),
        "parsed_row_count": len(parsed),
        "malformed_row_count": malformed,
        "duplicate_timestamp_count": duplicate_count,
        "strictly_increasing": strictly_increasing,
        "first_parsed_timestamp": open_times[0].isoformat() if open_times else None,
        "last_parsed_timestamp": open_times[-1].isoformat() if open_times else None,
        "timestamp_units": {
            f"{open_unit}/{close_unit}": count
            for (open_unit, close_unit), count in timestamp_units.items()
        },
        "first_raw_row": data_rows[0] if data_rows else None,
        "last_raw_row": data_rows[-1] if data_rows else None,
        "pass": passed,
    }


def _find_header_index(header: list[str], aliases: set[str]) -> int | None:
    normalized = [_normalized_header(value) for value in header]
    for i, value in enumerate(normalized):
        if value in aliases:
            return i
    return None


def probe_funding(payload: bytes) -> dict:
    member, rows = _rows_from_zip(payload)
    if not rows:
        raise ValueError("empty CSV")

    header_present = not _looks_integer(rows[0][0])
    header = rows[0] if header_present else None
    data_rows = rows[1:] if header_present else rows

    if not header_present:
        return {
            "member": member,
            "header_present": False,
            "header": None,
            "schema": None,
            "raw_row_count": len(data_rows),
            "parsed_row_count": 0,
            "malformed_row_count": len(data_rows),
            "duplicate_timestamp_count": 0,
            "strictly_increasing": False,
            "first_parsed_timestamp": None,
            "last_parsed_timestamp": None,
            "timestamp_units": {},
            "funding_interval_hours_observed": [],
            "timestamp_spacing_seconds": {},
            "first_raw_row": data_rows[0] if data_rows else None,
            "last_raw_row": data_rows[-1] if data_rows else None,
            "failure_reason": "funding header required for unambiguous field identification",
            "pass": False,
        }

    ts_idx = _find_header_index(
        header,
        {"calctime", "fundingtime", "timestamp", "time"},
    )
    rate_idx = _find_header_index(
        header,
        {"lastfundingrate", "fundingrate", "rate"},
    )
    interval_idx = _find_header_index(
        header,
        {"fundingintervalhours", "fundingintervalhour", "intervalhours"},
    )

    if ts_idx is None or rate_idx is None:
        return {
            "member": member,
            "header_present": True,
            "header": header,
            "schema": header,
            "raw_row_count": len(data_rows),
            "parsed_row_count": 0,
            "malformed_row_count": len(data_rows),
            "duplicate_timestamp_count": 0,
            "strictly_increasing": False,
            "first_parsed_timestamp": None,
            "last_parsed_timestamp": None,
            "timestamp_units": {},
            "funding_interval_hours_observed": [],
            "timestamp_spacing_seconds": {},
            "first_raw_row": data_rows[0] if data_rows else None,
            "last_raw_row": data_rows[-1] if data_rows else None,
            "failure_reason": "required funding timestamp/rate columns not identified",
            "pass": False,
        }

    parsed = []
    malformed = 0
    units = Counter()
    intervals = Counter()

    for row in data_rows:
        try:
            if len(row) != len(header):
                raise ValueError("funding row/header column mismatch")
            ts, unit = parse_epoch_timestamp(row[ts_idx])
            rate = Decimal(row[rate_idx])
            if not rate.is_finite():
                raise ValueError("non-finite funding rate")
            if interval_idx is not None and row[interval_idx].strip():
                interval = Decimal(row[interval_idx])
                if not interval.is_finite() or interval <= 0:
                    raise ValueError("invalid funding interval")
                intervals[str(interval)] += 1
            parsed.append((ts, rate))
            units[unit] += 1
        except (ValueError, InvalidOperation, OverflowError):
            malformed += 1

    timestamps = [item[0] for item in parsed]
    duplicate_count = len(timestamps) - len(set(timestamps))
    strictly_increasing = all(a < b for a, b in zip(timestamps, timestamps[1:]))
    spacing = Counter(
        int((b - a).total_seconds())
        for a, b in zip(timestamps, timestamps[1:])
    )

    passed = bool(parsed) and malformed == 0 and duplicate_count == 0 and strictly_increasing
    return {
        "member": member,
        "header_present": True,
        "header": header,
        "schema": header,
        "raw_row_count": len(data_rows),
        "parsed_row_count": len(parsed),
        "malformed_row_count": malformed,
        "duplicate_timestamp_count": duplicate_count,
        "strictly_increasing": strictly_increasing,
        "first_parsed_timestamp": timestamps[0].isoformat() if timestamps else None,
        "last_parsed_timestamp": timestamps[-1].isoformat() if timestamps else None,
        "timestamp_units": dict(units),
        "funding_interval_hours_observed": dict(intervals),
        "timestamp_spacing_seconds": {
            str(seconds): count for seconds, count in sorted(spacing.items())
        },
        "first_raw_row": data_rows[0] if data_rows else None,
        "last_raw_row": data_rows[-1] if data_rows else None,
        "pass": passed,
    }


def probe_archive(kind: str, symbol: str, year: int, month: int) -> dict:
    url = kline_url(symbol, year, month) if kind == "kline" else funding_url(symbol, year, month)
    checksum_url = f"{url}.CHECKSUM"
    result = {
        "kind": kind,
        "symbol": symbol,
        "year": year,
        "month": month,
        "url": url,
        "checksum_url": checksum_url,
        "downloaded": False,
        "checksum_downloaded": False,
        "checksum_verified": False,
        "archive_sha256": None,
        "validation": None,
        "pass": False,
        "error": None,
    }
    try:
        payload = fetch(url)
        result["downloaded"] = True
        checksum = fetch(checksum_url).decode("utf-8")
        result["checksum_downloaded"] = True
        result["checksum_verified"] = verify_sha256_bytes(payload, checksum)
        result["archive_sha256"] = sha256_bytes(payload)
        if not result["checksum_verified"]:
            raise ValueError("checksum verification failed")
        validation = probe_kline(payload) if kind == "kline" else probe_funding(payload)
        result["validation"] = validation
        result["pass"] = bool(validation["pass"])
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main() -> None:
    results = []
    for symbol in SYMBOLS:
        for year, month in MONTHS:
            results.append(probe_archive("kline", symbol, year, month))
            results.append(probe_archive("funding", symbol, year, month))

    expected = 8
    if len(results) != expected:
        raise RuntimeError(f"registered archive count mismatch: {len(results)}")

    report = {
        "experiment_version": "gate2-cycle9-derivatives-source-probe-v1",
        "github_sha": os.environ.get("GITHUB_SHA", "UNKNOWN"),
        "checked_out_sha": os.environ.get("CHECKED_OUT_SHA", "UNKNOWN"),
        "preregistration": {
            "path": str(PREREG),
            "sha256": sha256_file(ROOT / PREREG),
        },
        "validation_or_oos_accessed": False,
        "strategy_pnl_calculated": False,
        "strategy_signals_generated": False,
        "registered_archive_count": expected,
        "archives": results,
        "pass_count": sum(item["pass"] for item in results),
        "status": (
            "DERIVATIVES_SOURCE_PROBE_PASS"
            if all(item["pass"] for item in results)
            else "DERIVATIVES_SOURCE_PROBE_FAIL"
        ),
    }

    outdir = Path("gate2_cycle9_derivatives_source_probe_results")
    outdir.mkdir(exist_ok=True)
    (outdir / "cycle9_derivatives_source_probe.json").write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(report["status"])


if __name__ == "__main__":
    main()
