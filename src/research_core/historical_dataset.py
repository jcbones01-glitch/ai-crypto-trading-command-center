"""Deterministic assembly of validated Gate 1 historical archives."""
from __future__ import annotations

import csv
import hashlib
import io
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zipfile import ZipFile

from .archive_security import archive_member_symbol
from .data_ingestion import DatasetMetadata, SUPPORTED_SYMBOLS, TIMEFRAME, _timestamp_unit, find_missing_intervals, make_metadata, parse_timestamp, read_archive, validate_dataset
from .data_interfaces import MarketBar


@dataclass(frozen=True)
class HistoricalDataset:
    symbol: str
    bars: tuple[MarketBar, ...]
    metadata: DatasetMetadata


def _verify_archive_filename(path: Path, expected_symbol: str) -> None:
    """Bind the caller's expected symbol to the archive filename."""
    if expected_symbol not in SUPPORTED_SYMBOLS:
        raise ValueError("unsupported symbol")
    if not path.name.startswith(f"{expected_symbol}-{TIMEFRAME}-") or not path.name.endswith(".zip"):
        raise ValueError(f"archive path symbol mismatch: expected {expected_symbol}")


def _verify_archive_member(path: Path, expected_symbol: str) -> None:
    with ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        if len(names) != 1:
            raise ValueError("unexpected archive structure: expected exactly one data file")
        actual = archive_member_symbol(names[0])
        if actual != expected_symbol:
            raise ValueError(f"archive symbol mismatch: expected {expected_symbol}, found {actual}")


def _diagnose_timestamp_failure(path: Path, expected_symbol: str) -> None:
    """Re-run only timestamp parsing to enrich a rejection without changing validation."""
    with ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        if len(names) != 1:
            return
        member = names[0]
        with archive.open(member, "r") as binary:
            text = io.TextIOWrapper(binary, encoding="utf-8", newline="")
            for row_number, row in enumerate(csv.reader(text), start=1):
                if not row or all(not cell.strip() for cell in row):
                    continue
                if row[0].strip().lower() in {"open time", "timestamp"}:
                    continue
                raw_timestamp = row[0]
                try:
                    parse_timestamp(raw_timestamp)
                except ValueError as exc:
                    unit = _timestamp_unit(raw_timestamp)
                    integer = int(raw_timestamp)
                    divisor = 1_000 if unit == "milliseconds" else 1_000_000
                    seconds, remainder = divmod(integer, divisor)
                    microseconds = remainder if unit == "microseconds" else remainder * 1_000
                    parsed_utc = datetime.fromtimestamp(seconds, tz=timezone.utc).replace(microsecond=microseconds)
                    raise ValueError(
                        f"{exc}; ARCHIVE={path}; MEMBER={member}; ROW={row_number}; "
                        f"RAW_TIMESTAMP={raw_timestamp}; UNIT={unit}; PARSED_UTC={parsed_utc.isoformat()}; "
                        f"SYMBOL={expected_symbol}; TIMEFRAME={TIMEFRAME}"
                    ) from exc


def _archive_set_identity(paths: list[Path]) -> str:
    records = []
    for path in paths:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        records.append(f"{path.name}:{digest}")
    payload = ("\n".join(records) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def ingest_archives(paths: list[Path], source_symbol: str, expected_start: datetime | None = None, expected_end: datetime | None = None) -> HistoricalDataset:
    """Read raw Binance archives in supplied order and require a research-ready result."""
    if not paths:
        raise ValueError("at least one archive is required")
    all_bars: list[MarketBar] = []
    units: set[str] = set()
    for path in paths:
        _verify_archive_filename(path, source_symbol)
        _verify_archive_member(path, source_symbol)
        try:
            bars, unit = read_archive(path, source_symbol)
        except ValueError:
            _diagnose_timestamp_failure(path, source_symbol)
            raise
        all_bars.extend(bars)
        units.add(unit)
    report = validate_dataset(all_bars, source_symbol, ",".join(sorted(units)))
    if not report.valid:
        details = "; ".join(f"{issue.code}: {issue.message}" for issue in report.issues[:5])
        raise ValueError(f"historical dataset failed validation: {details}")
    if expected_start is not None and all_bars[0].timestamp != expected_start.astimezone(timezone.utc):
        raise ValueError("dataset start does not match required boundary")
    if expected_end is not None and all_bars[-1].timestamp >= expected_end.astimezone(timezone.utc):
        raise ValueError("dataset contains a bar at or beyond the exclusive end")
    timestamp_unit = ",".join(sorted(units))
    metadata = make_metadata(all_bars, source_symbol, timestamp_unit, source_identity=_archive_set_identity(paths))
    return HistoricalDataset(source_symbol, tuple(all_bars), metadata)


def require_complete_hourly_window(data: HistoricalDataset, start: datetime, end: datetime) -> None:
    """Require exact half-open coverage; no missing bars are tolerated."""
    start = start.astimezone(timezone.utc)
    end = end.astimezone(timezone.utc)
    if not data.bars or data.bars[0].timestamp != start:
        raise ValueError("dataset does not begin at the requested boundary")
    expected_last = end - timedelta(hours=1)
    if data.bars[-1].timestamp != expected_last:
        raise ValueError("dataset does not end at the requested exclusive boundary")
    missing = find_missing_intervals(list(data.bars))
    if missing:
        raise ValueError("dataset contains missing hourly intervals")
