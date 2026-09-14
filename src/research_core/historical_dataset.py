"""Deterministic assembly of validated Gate 1 historical archives."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .data_ingestion import (
    DatasetMetadata,
    SUPPORTED_SYMBOLS,
    TIMEFRAME,
    combined_source_identity,
    find_missing_intervals,
    make_metadata,
    read_archive,
    validate_dataset,
)
from .data_interfaces import MarketBar


@dataclass(frozen=True)
class HistoricalDataset:
    symbol: str
    bars: tuple[MarketBar, ...]
    metadata: DatasetMetadata


def _verify_archive_filename(path: Path, expected_symbol: str) -> None:
    """Bind the caller's expected symbol to Binance's internal archive filename."""
    if expected_symbol not in SUPPORTED_SYMBOLS:
        raise ValueError("unsupported symbol")
    names = path.name
    prefix = f"{expected_symbol}-{TIMEFRAME}-"
    if not names.startswith(prefix) or not names.endswith(".zip"):
        raise ValueError(f"archive path symbol mismatch: expected {expected_symbol}")


def ingest_archives(paths: list[Path], source_symbol: str, expected_start: datetime | None = None, expected_end: datetime | None = None) -> HistoricalDataset:
    """Read raw Binance archives in supplied order and require a research-ready result."""
    if not paths:
        raise ValueError("at least one archive is required")
    all_bars: list[MarketBar] = []
    units: set[str] = set()
    for path in paths:
        _verify_archive_filename(path, source_symbol)
        bars, unit = read_archive(path, source_symbol)
        all_bars.extend(bars)
        units.add(unit)
    if not units:
        raise ValueError("no timestamp precision detected")
    report = validate_dataset(all_bars, source_symbol, ",".join(sorted(units)))
    if not report.valid:
        details = "; ".join(f"{issue.code}: {issue.message}" for issue in report.issues[:5])
        raise ValueError(f"historical dataset failed validation: {details}")
    if expected_start is not None and all_bars[0].timestamp != expected_start.astimezone(timezone.utc):
        raise ValueError("dataset start does not match required boundary")
    if expected_end is not None and all_bars[-1].timestamp >= expected_end.astimezone(timezone.utc):
        raise ValueError("dataset contains a bar at or beyond the exclusive end")
    timestamp_unit = ",".join(sorted(units))
    metadata = make_metadata(
        all_bars,
        source_symbol,
        timestamp_unit,
        source_identity=combined_source_identity(paths),
    )
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
