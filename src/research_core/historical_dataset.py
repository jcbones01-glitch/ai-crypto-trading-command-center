"""Deterministic assembly of validated Gate 1 historical archives."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zipfile import ZipFile

from .archive_security import archive_member_symbol
from .data_ingestion import DatasetMetadata, SUPPORTED_SYMBOLS, TIMEFRAME, find_missing_intervals, make_metadata, read_archive, validate_dataset
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
        bars, unit = read_archive(path, source_symbol)
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
