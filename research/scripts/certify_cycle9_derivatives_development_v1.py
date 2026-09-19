"""Cycle 9 derivatives Development data certification.

Data infrastructure only. This module must not calculate predictive features,
strategy thresholds, P&L, or access Validation/OOS observations.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = Path("docs/GATE2_CYCLE9_DERIVATIVES_DEVELOPMENT_CERTIFICATION_PROTOCOL_V1.md")
CONTRACT = Path("docs/GATE2_CYCLE9_DERIVATIVES_NORMALIZATION_CONTRACT_V1.md")
SPEC_COMMIT = "8c003792dcf8c4d3de4f5a24e6fb54ea9a82961b"

BASE = "https://data.binance.vision/data/futures/um/monthly"
SYMBOLS = ("BTCUSDT", "ETHUSDT")
KINDS = ("kline", "funding")
DEV_START = datetime(2017, 8, 17, tzinfo=timezone.utc)
DEV_END = datetime(2022, 1, 1, tzinfo=timezone.utc)
FUNDING_TOLERANCE_US = 1_000_000

KLINE_FIELDS = (
    "open_time", "open", "high", "low", "close", "volume", "close_time",
    "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume",
    "taker_buy_quote_asset_volume", "ignore",
)
FUNDING_HEADER_NORMALIZED = (
    "calctime", "fundingintervalhours", "lastfundingrate",
)


class CertificationError(ValueError):
    pass


@dataclass(frozen=True)
class FetchResult:
    outcome: str
    payload: bytes | None
    detail: str | None = None


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_decimal(value: str) -> str:
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise CertificationError("invalid decimal") from exc
    if not number.is_finite():
        raise CertificationError("non-finite decimal")
    if number == 0:
        return "0"
    return format(number.normalize(), "f")


def decimal_value(value: str) -> Decimal:
    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise CertificationError("invalid decimal") from exc
    if not result.is_finite():
        raise CertificationError("non-finite decimal")
    return result


def timestamp_unit(raw: str) -> str:
    try:
        value = int(raw)
    except ValueError as exc:
        raise CertificationError("timestamp must be integer") from exc
    if value < 0:
        raise CertificationError("negative timestamp")
    if 10**11 <= value < 10**14:
        return "milliseconds"
    if 10**14 <= value < 10**17:
        return "microseconds"
    raise CertificationError("unsupported timestamp precision")


def timestamp_parts(raw: str) -> tuple[datetime, str, int]:
    unit = timestamp_unit(raw)
    value = int(raw)
    divisor = 1_000 if unit == "milliseconds" else 1_000_000
    seconds, remainder = divmod(value, divisor)
    microseconds = remainder * 1_000 if unit == "milliseconds" else remainder
    try:
        stamp = datetime.fromtimestamp(seconds, tz=timezone.utc).replace(microsecond=microseconds)
    except (OverflowError, OSError, ValueError) as exc:
        raise CertificationError("invalid timestamp") from exc
    epoch_us = value * (1_000 if unit == "milliseconds" else 1)
    return stamp, unit, epoch_us


def canonical_timestamp(raw: str) -> tuple[str, str, int]:
    stamp, unit, epoch_us = timestamp_parts(raw)
    timespec = "milliseconds" if unit == "milliseconds" else "microseconds"
    text = stamp.isoformat(timespec=timespec).replace("+00:00", "Z")
    return text, unit, epoch_us


def archive_url(kind: str, symbol: str, year: int, month: int) -> str:
    stamp = f"{year:04d}-{month:02d}"
    if kind == "kline":
        return f"{BASE}/klines/{symbol}/1h/{symbol}-1h-{stamp}.zip"
    if kind == "funding":
        return f"{BASE}/fundingRate/{symbol}/{symbol}-fundingRate-{stamp}.zip"
    raise ValueError("unknown stream kind")


def candidate_months() -> list[tuple[int, int]]:
    result = []
    year, month = 2017, 8
    while (year, month) <= (2021, 12):
        result.append((year, month))
        month += 1
        if month == 13:
            year += 1
            month = 1
    if len(result) != 53:
        raise RuntimeError("frozen candidate calendar must contain 53 months")
    return result


def fetch(url: str) -> FetchResult:
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "ai-crypto-trading-command-center/1"})
            with urllib.request.urlopen(request, timeout=90) as response:
                return FetchResult("OK", response.read(), None)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return FetchResult("HTTP_404", None, "HTTP 404")
            detail = f"HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            detail = f"{type(exc).__name__}: {exc}"
        if attempt < 2:
            time.sleep((1, 2)[attempt])
    return FetchResult("SOURCE_ACCESS_FAILURE", None, detail)


def checksum_expected(text: bytes) -> str:
    try:
        decoded = text.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise CertificationError("checksum is not UTF-8") from exc
    token = decoded.split()[0].lower() if decoded else ""
    if len(token) != 64 or any(ch not in "0123456789abcdef" for ch in token):
        raise CertificationError("invalid SHA-256 checksum document")
    return token


def zip_rows(payload: bytes) -> tuple[str, list[list[str]]]:
    try:
        with ZipFile(io.BytesIO(payload)) as archive:
            members = [name for name in archive.namelist() if not name.endswith("/")]
            if len(members) != 1:
                raise CertificationError(f"expected one data member, found {len(members)}")
            member = members[0]
            try:
                text = archive.read(member).decode("utf-8")
            except UnicodeDecodeError as exc:
                raise CertificationError("archive member is not UTF-8") from exc
    except CertificationError:
        raise
    except Exception as exc:
        raise CertificationError(f"invalid ZIP: {exc}") from exc
    rows = [row for row in csv.reader(text.splitlines()) if row and any(cell.strip() for cell in row)]
    if not rows:
        raise CertificationError("empty CSV")
    return member, rows


def normalized_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.strip().lower())


def validate_kline_archive(payload: bytes, symbol: str, archive_sha: str) -> tuple[dict, list[dict]]:
    member, rows = zip_rows(payload)
    # V1 source contract is explicitly headerless.
    try:
        int(rows[0][0])
    except ValueError as exc:
        raise CertificationError("unexpected kline header/schema change") from exc

    normalized: list[dict] = []
    units: set[str] = set()
    previous_open_us = None
    malformed = 0

    for row_number, row in enumerate(rows, start=1):
        try:
            if len(row) != 12:
                raise CertificationError("kline row must contain exactly 12 columns")
            open_text, open_unit, open_us = canonical_timestamp(row[0])
            close_text, close_unit, close_us = canonical_timestamp(row[6])
            units.update((open_unit, close_unit))
            open_dt, _, _ = timestamp_parts(row[0])
            if open_dt.minute or open_dt.second or open_dt.microsecond:
                raise CertificationError("kline open not exact UTC hour")
            if not (DEV_START <= open_dt < DEV_END):
                raise CertificationError("kline row outside Development partition")
            if close_us <= open_us:
                raise CertificationError("kline close time not after open")
            if close_us >= open_us + 3_600_000_000:
                raise CertificationError("kline close time reaches/crosses next hour")
            if previous_open_us is not None and open_us <= previous_open_us:
                raise CertificationError("kline timestamps not strictly increasing")
            previous_open_us = open_us

            open_d, high_d, low_d, close_d = [decimal_value(row[i]) for i in (1,2,3,4)]
            volume_d = decimal_value(row[5])
            quote_d = decimal_value(row[7])
            taker_base_d = decimal_value(row[9])
            taker_quote_d = decimal_value(row[10])
            if min(open_d, high_d, low_d, close_d) <= 0:
                raise CertificationError("non-positive OHLC")
            if not (low_d <= open_d <= high_d and low_d <= close_d <= high_d):
                raise CertificationError("invalid OHLC relationship")
            if min(volume_d, quote_d, taker_base_d, taker_quote_d) < 0:
                raise CertificationError("negative volume")
            try:
                trades = int(row[8])
            except ValueError as exc:
                raise CertificationError("trade count not integer") from exc
            if trades < 0 or str(trades) != row[8].strip().lstrip("+"):
                raise CertificationError("invalid trade count")

            normalized.append({
                "close": canonical_decimal(row[4]),
                "close_time": close_text,
                "high": canonical_decimal(row[2]),
                "low": canonical_decimal(row[3]),
                "market": "USD_M_FUTURES",
                "number_of_trades": trades,
                "open": canonical_decimal(row[1]),
                "open_time": open_text,
                "quote_asset_volume": canonical_decimal(row[7]),
                "source_archive_sha256": archive_sha,
                "source_member": member,
                "symbol": symbol,
                "taker_buy_base_asset_volume": canonical_decimal(row[9]),
                "taker_buy_quote_asset_volume": canonical_decimal(row[10]),
                "volume": canonical_decimal(row[5]),
                "_primary_epoch_us": open_us,
            })
        except CertificationError:
            malformed += 1
            raise CertificationError(f"kline validation failure at row {row_number}") from None

    validation = {
        "member": member,
        "header": None,
        "source_column_count": 12,
        "raw_row_count": len(rows),
        "malformed_row_count": malformed,
        "timestamp_units": sorted(units),
        "first_timestamp": normalized[0]["open_time"],
        "last_timestamp": normalized[-1]["open_time"],
        "first_source_epoch": rows[0][0],
        "last_source_epoch": rows[-1][0],
    }
    return validation, normalized


def validate_funding_archive(payload: bytes, symbol: str, archive_sha: str) -> tuple[dict, list[dict]]:
    member, rows = zip_rows(payload)
    header = rows[0]
    if tuple(normalized_header(x) for x in header) != FUNDING_HEADER_NORMALIZED:
        raise CertificationError(f"unexpected funding header: {header}")
    data = rows[1:]
    if not data:
        raise CertificationError("funding archive has no data rows")

    normalized: list[dict] = []
    units: set[str] = set()
    intervals: set[str] = set()
    previous_us = None
    previous_interval = None

    for row_number, row in enumerate(data, start=2):
        if len(row) != len(header):
            raise CertificationError(f"funding row/header mismatch at row {row_number}")
        calc_text, unit, calc_us = canonical_timestamp(row[0])
        calc_dt, _, _ = timestamp_parts(row[0])
        if not (DEV_START <= calc_dt < DEV_END):
            raise CertificationError(f"funding row outside Development at row {row_number}")
        rate = decimal_value(row[2])
        interval = decimal_value(row[1])
        if interval <= 0:
            raise CertificationError(f"non-positive funding interval at row {row_number}")
        if previous_us is not None:
            if calc_us <= previous_us:
                raise CertificationError(f"funding timestamps not strictly increasing at row {row_number}")
            expected_us = previous_interval * Decimal(3_600_000_000)
            delta_us = Decimal(calc_us - previous_us)
            if abs(delta_us - expected_us) > FUNDING_TOLERANCE_US:
                raise CertificationError(f"funding spacing incompatible with source interval at row {row_number}")
        previous_us = calc_us
        previous_interval = interval
        units.add(unit)
        intervals.add(canonical_decimal(row[1]))
        normalized.append({
            "calc_time": calc_text,
            "funding_interval_hours": canonical_decimal(row[1]),
            "last_funding_rate": canonical_decimal(row[2]),
            "market": "USD_M_FUTURES",
            "source_archive_sha256": archive_sha,
            "source_member": member,
            "symbol": symbol,
            "_primary_epoch_us": calc_us,
            "_interval_decimal": canonical_decimal(row[1]),
        })

    return {
        "member": member,
        "header": header,
        "raw_row_count": len(data),
        "malformed_row_count": 0,
        "timestamp_units": sorted(units),
        "funding_interval_hours_observed": sorted(intervals),
        "first_timestamp": normalized[0]["calc_time"],
        "last_timestamp": normalized[-1]["calc_time"],
        "first_source_epoch": data[0][0],
        "last_source_epoch": data[-1][0],
    }, normalized


def stream_id(kind: str, symbol: str) -> str:
    return f"{symbol}_{kind}".lower()


def canonical_output_rows(rows: Iterable[dict]) -> bytes:
    chunks = []
    for source in rows:
        row = {k: v for k, v in source.items() if not k.startswith("_")}
        chunks.append(canonical_json_bytes(row) + b"\n")
    return b"".join(chunks)


def certify_stream(kind: str, symbol: str) -> dict:
    ledger = []
    accepted_rows: list[dict] = []
    availability_started = False
    first_archive_month = None
    stream_failures: list[dict] = []

    for year, month in candidate_months():
        url = archive_url(kind, symbol, year, month)
        checksum_url = url + ".CHECKSUM"
        entry = {
            "kind": kind,
            "symbol": symbol,
            "year": year,
            "month": month,
            "url": url,
            "checksum_url": checksum_url,
            "availability_classification": None,
            "archive_sha256": None,
            "checksum_expected_sha256": None,
            "checksum_verified": False,
            "validation": None,
            "status": None,
            "failure_reason": None,
        }

        got = fetch(url)
        if got.outcome == "HTTP_404":
            if availability_started:
                entry["availability_classification"] = "POST_AVAILABILITY"
                entry["status"] = "INTERIOR_COVERAGE_FAILURE"
                entry["failure_reason"] = "monthly ZIP returned HTTP 404 after source availability began"
                stream_failures.append({"year":year,"month":month,"code":"INTERIOR_COVERAGE_FAILURE"})
            else:
                entry["availability_classification"] = "PRE_SOURCE_AVAILABILITY"
                entry["status"] = "PRE_SOURCE_AVAILABILITY"
            ledger.append(entry)
            continue
        if got.outcome != "OK":
            entry["status"] = "SOURCE_ACCESS_FAILURE"
            entry["failure_reason"] = got.detail
            stream_failures.append({"year":year,"month":month,"code":"SOURCE_ACCESS_FAILURE"})
            ledger.append(entry)
            continue

        entry["availability_classification"] = "SOURCE_OBJECT_EXISTS"
        payload = got.payload
        archive_sha = sha256_bytes(payload)
        entry["archive_sha256"] = archive_sha

        check = fetch(checksum_url)
        if check.outcome != "OK":
            entry["status"] = "SOURCE_INTEGRITY_FAILURE"
            entry["failure_reason"] = f"checksum fetch outcome: {check.outcome}"
            stream_failures.append({"year":year,"month":month,"code":"SOURCE_INTEGRITY_FAILURE"})
            ledger.append(entry)
            continue

        try:
            expected = checksum_expected(check.payload)
            entry["checksum_expected_sha256"] = expected
            if expected != archive_sha:
                raise CertificationError("archive checksum mismatch")
            entry["checksum_verified"] = True
            validation, rows = (
                validate_kline_archive(payload, symbol, archive_sha)
                if kind == "kline"
                else validate_funding_archive(payload, symbol, archive_sha)
            )
            entry["validation"] = validation
        except CertificationError as exc:
            entry["status"] = "ARCHIVE_VALIDATION_FAILURE"
            entry["failure_reason"] = str(exc)
            stream_failures.append({"year":year,"month":month,"code":"ARCHIVE_VALIDATION_FAILURE"})
            ledger.append(entry)
            continue

        if not availability_started:
            availability_started = True
            first_archive_month = f"{year:04d}-{month:02d}"
        entry["availability_classification"] = "AVAILABLE"
        entry["status"] = "PASS"
        accepted_rows.extend(rows)
        ledger.append(entry)

    if not availability_started:
        stream_failures.append({"code":"NO_SOURCE_AVAILABILITY"})

    # Global cross-archive checks.
    continuity = {
        "duplicate_primary_timestamps": None,
        "missing_hour_count": None,
        "gap_spans": [],
        "funding_spacing_failures": [],
    }
    if accepted_rows:
        epochs = [row["_primary_epoch_us"] for row in accepted_rows]
        duplicate_count = len(epochs) - len(set(epochs))
        continuity["duplicate_primary_timestamps"] = duplicate_count
        if any(a >= b for a, b in zip(epochs, epochs[1:])):
            stream_failures.append({"code":"GLOBAL_ORDERING_FAILURE"})
        if duplicate_count:
            stream_failures.append({"code":"GLOBAL_DUPLICATE_FAILURE","count":duplicate_count})

        if kind == "kline":
            hour_us = 3_600_000_000
            missing = 0
            spans = []
            for a, b in zip(epochs, epochs[1:]):
                delta = b - a
                if delta != hour_us:
                    if delta > hour_us and delta % hour_us == 0:
                        count = delta // hour_us - 1
                        missing += count
                        spans.append({"after_epoch_us":a,"before_epoch_us":b,"missing_hours":count})
                    else:
                        spans.append({"after_epoch_us":a,"before_epoch_us":b,"invalid_delta_us":delta})
                        stream_failures.append({"code":"KLINE_CADENCE_FAILURE","delta_us":delta})
            continuity["missing_hour_count"] = int(missing)
            continuity["gap_spans"] = spans
            if missing:
                stream_failures.append({"code":"CONTINUITY_FAILURE","missing_hours":int(missing)})
        else:
            failures = []
            for previous, current in zip(accepted_rows, accepted_rows[1:]):
                expected_us = Decimal(previous["_interval_decimal"]) * Decimal(3_600_000_000)
                delta_us = Decimal(current["_primary_epoch_us"] - previous["_primary_epoch_us"])
                if abs(delta_us - expected_us) > FUNDING_TOLERANCE_US:
                    failures.append({
                        "previous": previous["calc_time"],
                        "current": current["calc_time"],
                        "delta_us": str(delta_us),
                        "expected_us": str(expected_us),
                    })
            continuity["funding_spacing_failures"] = failures
            if failures:
                stream_failures.append({"code":"FUNDING_CADENCE_FAILURE","count":len(failures)})

    stream_ok = availability_started and not stream_failures
    manifest_identity = sha256_bytes(canonical_json_bytes({
        "stream": stream_id(kind,symbol),
        "protocol_sha256": sha256_file(ROOT / PROTOCOL),
        "normalization_contract_sha256": sha256_file(ROOT / CONTRACT),
        "ledger": ledger,
    }))

    normalized_bytes = canonical_output_rows(accepted_rows) if stream_ok else b""
    normalized_identity = sha256_bytes(normalized_bytes) if stream_ok else None

    return {
        "stream": stream_id(kind, symbol),
        "kind": kind,
        "symbol": symbol,
        "status": "PASS" if stream_ok else "FAIL",
        "first_source_native_archive_month": first_archive_month,
        "accepted_archive_count": sum(x["status"] == "PASS" for x in ledger),
        "normalized_row_count": len(accepted_rows) if stream_ok else 0,
        "first_timestamp": (
            next((({k:v for k,v in accepted_rows[0].items() if not k.startswith("_")}).get("open_time") or
                  ({k:v for k,v in accepted_rows[0].items() if not k.startswith("_")}).get("calc_time")), None)
            if accepted_rows else None
        ),
        "last_timestamp": (
            next((({k:v for k,v in accepted_rows[-1].items() if not k.startswith("_")}).get("open_time") or
                  ({k:v for k,v in accepted_rows[-1].items() if not k.startswith("_")}).get("calc_time")), None)
            if accepted_rows else None
        ),
        "failures": stream_failures,
        "continuity": continuity,
        "source_manifest_identity": manifest_identity,
        "normalized_data_identity": normalized_identity,
        "ledger": ledger,
        "_normalized_bytes": normalized_bytes,
    }


def provenance() -> dict:
    executing = subprocess.check_output(["git","rev-parse","HEAD"], cwd=ROOT, text=True).strip()
    subprocess.run(["git","diff","--exit-code","HEAD","--"], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    for path in (PROTOCOL, CONTRACT):
        frozen = subprocess.check_output(["git","show",f"{SPEC_COMMIT}:{path.as_posix()}"], cwd=ROOT)
        if frozen != (ROOT/path).read_bytes():
            raise RuntimeError(f"frozen certification specification changed: {path}")
    return {
        "executing_commit": executing,
        "checked_out_commit": executing,
        "specification_commit": SPEC_COMMIT,
        "protocol_path": str(PROTOCOL),
        "protocol_sha256": sha256_file(ROOT/PROTOCOL),
        "normalization_contract_path": str(CONTRACT),
        "normalization_contract_sha256": sha256_file(ROOT/CONTRACT),
    }


def main() -> None:
    meta = provenance()
    streams = [certify_stream(kind, symbol) for symbol in SYMBOLS for kind in KINDS]
    all_pass = all(item["status"] == "PASS" for item in streams)

    identity_inputs = {
        item["stream"]: {
            "source_manifest_identity": item["source_manifest_identity"],
            "normalized_data_identity": item["normalized_data_identity"],
        }
        for item in streams
    }
    combined_identity = (
        sha256_bytes(canonical_json_bytes({
            "protocol_sha256": meta["protocol_sha256"],
            "normalization_contract_sha256": meta["normalization_contract_sha256"],
            "streams": identity_inputs,
        }))
        if all_pass else None
    )

    outdir = ROOT / "gate2_cycle9_derivatives_development_results"
    outdir.mkdir(exist_ok=True)
    stream_reports = []
    for item in streams:
        normalized_bytes = item.pop("_normalized_bytes")
        if item["status"] == "PASS":
            gz = gzip.compress(normalized_bytes, mtime=0)
            (outdir / f"{item['stream']}.jsonl.gz").write_bytes(gz)
            item["normalized_jsonl_sha256"] = sha256_bytes(normalized_bytes)
            item["normalized_gzip_sha256"] = sha256_bytes(gz)
        stream_reports.append(item)

    report = {
        "experiment_version": "gate2-cycle9-derivatives-development-certification-v1",
        "classification": "DATA_CERTIFICATION_NOT_TRADING_EVIDENCE",
        "provenance": meta,
        "candidate_month_count_per_stream": 53,
        "streams": stream_reports,
        "combined_dataset_identity": combined_identity,
        "validation_or_oos_accessed": False,
        "strategy_pnl_calculated": False,
        "strategy_signals_generated": False,
        "strategy_thresholds_searched": False,
        "status": (
            "DERIVATIVES_DEVELOPMENT_DATASET_CERTIFIED"
            if all_pass else
            "DERIVATIVES_DEVELOPMENT_DATASET_CERTIFICATION_FAILED"
        ),
    }
    (outdir/"certification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(report["status"])
    for item in stream_reports:
        print(json.dumps({
            "stream":item["stream"],
            "status":item["status"],
            "first_source_native_archive_month":item["first_source_native_archive_month"],
            "accepted_archive_count":item["accepted_archive_count"],
            "normalized_row_count":item["normalized_row_count"],
            "first_timestamp":item["first_timestamp"],
            "last_timestamp":item["last_timestamp"],
            "failures":item["failures"],
            "continuity":item["continuity"],
            "source_manifest_identity":item["source_manifest_identity"],
            "normalized_data_identity":item["normalized_data_identity"],
        }, sort_keys=True))


if __name__ == "__main__":
    main()
