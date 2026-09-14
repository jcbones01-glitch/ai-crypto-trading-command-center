"""Gate 1 Binance Spot kline ingestion, normalization, and validation."""
from __future__ import annotations

import csv
import hashlib
import io
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable, TextIO

from .data_interfaces import MarketBar, validate_market_data

BINANCE_BASE_URL = "https://data.binance.vision/data/spot"
SUPPORTED_SYMBOLS = {"BTCUSDT": "BTC/USDT", "ETHUSDT": "ETH/USDT"}
TIMEFRAME = "1h"
NORMALIZATION_VERSION = "gate1-v1"
RESEARCH_START = datetime(2017, 8, 17, tzinfo=timezone.utc)
RESEARCH_END = datetime(2026, 1, 1, tzinfo=timezone.utc)
PARTITIONS = {
    "development": (RESEARCH_START, datetime(2022, 1, 1, tzinfo=timezone.utc)),
    "validation": (datetime(2022, 1, 1, tzinfo=timezone.utc), datetime(2024, 1, 1, tzinfo=timezone.utc)),
    "oos": (datetime(2024, 1, 1, tzinfo=timezone.utc), RESEARCH_END),
}


@dataclass(frozen=True)
class RawKline:
    """Lossless source-row representation for provenance; not a MarketBar."""
    fields: tuple[str, ...]
    timestamp_unit: str


@dataclass(frozen=True)
class DataQualityIssue:
    code: str
    message: str
    timestamp: datetime | None = None


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    row_count: int
    issues: tuple[DataQualityIssue, ...]
    timestamp_unit: str | None


@dataclass(frozen=True)
class DatasetMetadata:
    dataset_id: str
    source: str
    source_symbol: str
    canonical_symbol: str
    market: str
    timeframe: str
    timezone: str
    start_timestamp: str
    end_timestamp: str
    row_count: int
    timestamp_unit: str
    normalization_version: str
    validation_status: str
    content_hash: str
    source_identity: str | None = None

    def to_record(self) -> dict[str, str | int | None]:
        return self.__dict__.copy()


def _timestamp_unit(value: str) -> str:
    try:
        integer = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid timestamp: expected integer milliseconds or microseconds") from exc
    if integer < 0:
        raise ValueError("invalid timestamp: negative value")
    if 10**11 <= integer < 10**14:
        return "milliseconds"
    if 10**14 <= integer < 10**17:
        return "microseconds"
    raise ValueError("ambiguous or unsupported timestamp precision")


def parse_timestamp(value: str) -> tuple[datetime, str]:
    unit = _timestamp_unit(value)
    integer = int(value)
    divisor = 1_000 if unit == "milliseconds" else 1_000_000
    seconds, remainder = divmod(integer, divisor)
    microseconds = remainder if unit == "microseconds" else remainder * 1_000
    try:
        timestamp = datetime.fromtimestamp(seconds, tz=timezone.utc).replace(microsecond=microseconds)
    except (OverflowError, OSError, ValueError) as exc:
        raise ValueError("invalid timestamp value") from exc
    if timestamp.minute or timestamp.second or timestamp.microsecond:
        raise ValueError("1-hour kline timestamp must be on an exact UTC hour boundary")
    return timestamp, unit


def _decimal(value: str, field: str) -> Decimal:
    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid decimal in {field}") from exc
    if not result.is_finite():
        raise ValueError(f"non-finite decimal in {field}")
    return result


def normalize_row(row: list[str] | tuple[str, ...], expected_symbol: str) -> tuple[MarketBar, RawKline]:
    """Convert one Binance kline row. Symbol is supplied by archive identity."""
    if expected_symbol not in SUPPORTED_SYMBOLS:
        raise ValueError("unsupported symbol")
    if len(row) < 6:
        raise ValueError("malformed kline row: expected at least 6 fields")
    timestamp, unit = parse_timestamp(row[0])
    bar = MarketBar(
        timestamp=timestamp,
        symbol=SUPPORTED_SYMBOLS[expected_symbol],
        open=_decimal(row[1], "open"),
        high=_decimal(row[2], "high"),
        low=_decimal(row[3], "low"),
        close=_decimal(row[4], "close"),
        volume=_decimal(row[5], "volume"),
    )
    return bar, RawKline(tuple(row), unit)


def read_csv_rows(stream: TextIO) -> Iterable[list[str]]:
    reader = csv.reader(stream)
    for row in reader:
        if not row or all(not cell.strip() for cell in row):
            continue
        if row[0].strip().lower() in {"open time", "timestamp"}:
            raise ValueError("unexpected header row in Binance kline archive")
        yield row


def normalize_csv(stream: TextIO, expected_symbol: str) -> tuple[list[MarketBar], str]:
    bars: list[MarketBar] = []
    units: set[str] = set()
    for row in read_csv_rows(stream):
        bar, raw = normalize_row(row, expected_symbol)
        bars.append(bar)
        units.add(raw.timestamp_unit)
    if not bars:
        raise ValueError("empty kline dataset")
    if len(units) != 1:
        raise ValueError("mixed timestamp precision in dataset")
    validate_market_data(bars)
    return bars, next(iter(units))


def find_missing_intervals(data: list[MarketBar]) -> tuple[datetime, ...]:
    missing: list[datetime] = []
    for previous, current in zip(data, data[1:]):
        cursor = previous.timestamp + timedelta(hours=1)
        while cursor < current.timestamp:
            missing.append(cursor)
            cursor += timedelta(hours=1)
    return tuple(missing)


def validate_dataset(data: list[MarketBar], expected_symbol: str, timestamp_unit: str | None = None) -> ValidationReport:
    issues: list[DataQualityIssue] = []
    if expected_symbol not in SUPPORTED_SYMBOLS:
        issues.append(DataQualityIssue("symbol", "unsupported symbol"))
    expected_canonical = SUPPORTED_SYMBOLS.get(expected_symbol)
    for bar in data:
        if bar.symbol != expected_canonical:
            issues.append(DataQualityIssue("symbol", "unexpected canonical symbol", bar.timestamp))
        if bar.timestamp.tzinfo is None or bar.timestamp.utcoffset() is None:
            issues.append(DataQualityIssue("timezone", "timestamp is not timezone-aware", bar.timestamp))
        elif bar.timestamp.utcoffset() != timedelta(0):
            issues.append(DataQualityIssue("timezone", "timestamp is not UTC", bar.timestamp))
        if bar.timestamp.minute or bar.timestamp.second or bar.timestamp.microsecond:
            issues.append(DataQualityIssue("interval", "timestamp is not an hourly boundary", bar.timestamp))
    try:
        validate_market_data(data)
    except ValueError as exc:
        issues.append(DataQualityIssue("ordering", str(exc)))
    issues.extend(DataQualityIssue("missing_interval", "missing hourly interval", ts) for ts in find_missing_intervals(data))
    return ValidationReport(not issues, len(data), tuple(issues), timestamp_unit)


def canonical_content(data: Iterable[MarketBar]) -> bytes:
    lines = ["|".join((bar.timestamp.isoformat(), bar.symbol, str(bar.open), str(bar.high), str(bar.low), str(bar.close), str(bar.volume))) for bar in data]
    return ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")


def content_hash(data: Iterable[MarketBar]) -> str:
    return hashlib.sha256(canonical_content(data)).hexdigest()


def dataset_identity(data: Iterable[MarketBar], normalization_version: str = NORMALIZATION_VERSION) -> str:
    payload = b"normalization_version=" + normalization_version.encode("utf-8") + b"\n" + canonical_content(data)
    return hashlib.sha256(payload).hexdigest()


def make_metadata(data: list[MarketBar], source_symbol: str, timestamp_unit: str, source_identity: str | None = None, validation_status: str = "validated") -> DatasetMetadata:
    if source_symbol not in SUPPORTED_SYMBOLS:
        raise ValueError("unsupported symbol")
    if not data:
        raise ValueError("cannot create metadata for empty dataset")
    normalized_hash = content_hash(data)
    return DatasetMetadata(
        dataset_id=dataset_identity(data), source="Binance Public Data", source_symbol=source_symbol,
        canonical_symbol=SUPPORTED_SYMBOLS[source_symbol], market="spot", timeframe=TIMEFRAME, timezone="UTC",
        start_timestamp=data[0].timestamp.isoformat(), end_timestamp=data[-1].timestamp.isoformat(), row_count=len(data),
        timestamp_unit=timestamp_unit, normalization_version=NORMALIZATION_VERSION, validation_status=validation_status,
        content_hash=normalized_hash, source_identity=source_identity,
    )


def archive_url(symbol: str, year: int, month: int) -> str:
    if symbol not in SUPPORTED_SYMBOLS:
        raise ValueError("unsupported symbol")
    return f"{BINANCE_BASE_URL}/monthly/klines/{symbol}/{TIMEFRAME}/{symbol}-{TIMEFRAME}-{year:04d}-{month:02d}.zip"


def checksum_url(archive: str) -> str:
    return archive + ".CHECKSUM"


def verify_sha256_bytes(payload: bytes, checksum_text: str) -> bool:
    expected = checksum_text.strip().split()[0].lower()
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        raise ValueError("invalid SHA-256 checksum document")
    return hashlib.sha256(payload).hexdigest() == expected


def download_archive(url: str, destination: Path, verify_checksum: bool = True) -> str | None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as response:
        payload = response.read()
    source_checksum = None
    if verify_checksum:
        with urllib.request.urlopen(checksum_url(url), timeout=60) as response:
            checksum_text = response.read().decode("utf-8")
        if not verify_sha256_bytes(payload, checksum_text):
            raise ValueError("Binance archive SHA-256 checksum mismatch")
        source_checksum = checksum_text.strip().split()[0].lower()
    destination.write_bytes(payload)
    return source_checksum


def read_archive(path: Path, expected_symbol: str) -> tuple[list[MarketBar], str]:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        if len(names) != 1:
            raise ValueError("unexpected archive structure: expected exactly one data file")
        with archive.open(names[0], "r") as binary:
            text = io.TextIOWrapper(binary, encoding="utf-8", newline="")
            return normalize_csv(text, expected_symbol)
