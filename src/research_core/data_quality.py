"""Explicit Gate 1 source-data quality events and certification."""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zipfile import ZipFile

from .archive_security import archive_member_symbol
from .data_ingestion import TIMEFRAME, _timestamp_unit, parse_timestamp
from .data_interfaces import MarketBar

KNOWN_BINANCE_ISSUE_77_ARCHIVES = {
    "BTCUSDT-1h-2018-01.zip", "BTCUSDT-1h-2018-02.zip", "BTCUSDT-1h-2018-06.zip",
    "BTCUSDT-1h-2018-07.zip", "BTCUSDT-1h-2018-10.zip", "BTCUSDT-1h-2018-11.zip",
    "BTCUSDT-1h-2019-03.zip", "BTCUSDT-1h-2019-05.zip", "BTCUSDT-1h-2019-08.zip",
    "BTCUSDT-1h-2019-11.zip", "BTCUSDT-1h-2020-02.zip", "BTCUSDT-1h-2020-03.zip",
    "BTCUSDT-1h-2020-04.zip", "BTCUSDT-1h-2020-06.zip", "BTCUSDT-1h-2020-11.zip",
    "BTCUSDT-1h-2020-12.zip", "BTCUSDT-1h-2021-02.zip", "BTCUSDT-1h-2021-03.zip",
    "BTCUSDT-1h-2021-04.zip", "BTCUSDT-1h-2021-08.zip",
}
KNOWN_BINANCE_ISSUE_77_TIMESTAMPS = {"1518168494789", "1518319694789"}


@dataclass(frozen=True)
class DataQualityEvent:
    symbol: str
    timeframe: str
    archive: str
    member: str | None
    row: int | None
    raw_timestamp: str | None
    parsed_timestamp: str | None
    anomaly_type: str
    validation_rule: str
    severity: str
    source_provenance: str
    message: str


@dataclass(frozen=True)
class ArchiveQualityReport:
    symbol: str
    archive: str
    rows_processed: int
    events: tuple[DataQualityEvent, ...]
    checksum_verified: bool
    valid_timestamps: tuple[datetime, ...] = ()

    @property
    def invalid_rows(self) -> int:
        return len({event.row for event in self.events if event.row is not None})


def _event(*, symbol: str, archive: Path, member: str | None, row: int | None,
           raw_timestamp: str | None, parsed_timestamp: datetime | None,
           anomaly_type: str, validation_rule: str, message: str,
           source_provenance: str = "Binance Public Data archive") -> DataQualityEvent:
    return DataQualityEvent(symbol, TIMEFRAME, archive.name, member, row, raw_timestamp,
                            parsed_timestamp.isoformat() if parsed_timestamp else None,
                            anomaly_type, validation_rule, "ERROR", source_provenance, message)


def _parsed_timestamp(value: str) -> datetime | None:
    try:
        unit = _timestamp_unit(value)
        integer = int(value)
        divisor = 1_000 if unit == "milliseconds" else 1_000_000
        seconds, remainder = divmod(integer, divisor)
        microseconds = remainder if unit == "microseconds" else remainder * 1_000
        return datetime.fromtimestamp(seconds, tz=timezone.utc).replace(microsecond=microseconds)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _decimal(value: str, field: str) -> Decimal:
    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid decimal in {field}") from exc
    if not result.is_finite():
        raise ValueError(f"non-finite decimal in {field}")
    return result


def scan_archive(path: Path, symbol: str, checksum_verified: bool = True) -> ArchiveQualityReport:
    """Scan every source row and record validation failures without repairing data."""
    events: list[DataQualityEvent] = []
    rows_processed = 0
    valid_timestamps: list[datetime] = []
    with ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
        if len(names) != 1:
            events.append(_event(symbol=symbol, archive=path, member=None, row=None, raw_timestamp=None,
                                 parsed_timestamp=None, anomaly_type="SCHEMA_ERROR",
                                 validation_rule="exactly one non-directory ZIP member",
                                 message="unexpected archive structure"))
            return ArchiveQualityReport(symbol, path.name, 0, tuple(events), checksum_verified, tuple())
        member = names[0]
        try:
            if archive_member_symbol(member) != symbol:
                events.append(_event(symbol=symbol, archive=path, member=member, row=None, raw_timestamp=None,
                                     parsed_timestamp=None, anomaly_type="SCHEMA_ERROR",
                                     validation_rule="archive member symbol must match expected symbol",
                                     message="archive member symbol mismatch"))
        except ValueError as exc:
            events.append(_event(symbol=symbol, archive=path, member=member, row=None, raw_timestamp=None,
                                 parsed_timestamp=None, anomaly_type="SCHEMA_ERROR",
                                 validation_rule="Binance archive member naming", message=str(exc)))
        with archive.open(member, "r") as binary:
            text = io.TextIOWrapper(binary, encoding="utf-8", newline="")
            previous_timestamp = None
            seen: set[datetime] = set()
            for row_number, row in enumerate(csv.reader(text), start=1):
                if not row or all(not cell.strip() for cell in row):
                    continue
                rows_processed += 1
                if row[0].strip().lower() in {"open time", "timestamp"}:
                    events.append(_event(symbol=symbol, archive=path, member=member, row=row_number,
                                         raw_timestamp=row[0], parsed_timestamp=None, anomaly_type="SCHEMA_ERROR",
                                         validation_rule="source CSV must not contain a header row",
                                         message="unexpected header row"))
                    continue
                if len(row) < 6:
                    events.append(_event(symbol=symbol, archive=path, member=member, row=row_number,
                                         raw_timestamp=row[0], parsed_timestamp=None, anomaly_type="SCHEMA_ERROR",
                                         validation_rule="kline row has at least 6 fields", message="malformed kline row"))
                    continue
                raw_timestamp = row[0]
                try:
                    timestamp, _ = parse_timestamp(raw_timestamp)
                except ValueError as exc:
                    anomaly_type = "NON_ALIGNED_TIMESTAMP" if "exact UTC hour boundary" in str(exc) else "SCHEMA_ERROR"
                    provenance = "Binance Public Data issue #77" if raw_timestamp in KNOWN_BINANCE_ISSUE_77_TIMESTAMPS else "Binance Public Data archive"
                    events.append(_event(symbol=symbol, archive=path, member=member, row=row_number,
                                         raw_timestamp=raw_timestamp, parsed_timestamp=_parsed_timestamp(raw_timestamp),
                                         anomaly_type=anomaly_type,
                                         validation_rule="1-hour kline timestamp must be on an exact UTC hour boundary",
                                         message=str(exc), source_provenance=provenance))
                    continue
                duplicate = timestamp in seen
                if duplicate:
                    events.append(_event(symbol=symbol, archive=path, member=member, row=row_number,
                                         raw_timestamp=raw_timestamp, parsed_timestamp=timestamp,
                                         anomaly_type="DUPLICATE_TIMESTAMP", validation_rule="timestamps must be unique",
                                         message="duplicate timestamp"))
                if previous_timestamp is not None and timestamp < previous_timestamp:
                    events.append(_event(symbol=symbol, archive=path, member=member, row=row_number,
                                         raw_timestamp=raw_timestamp, parsed_timestamp=timestamp,
                                         anomaly_type="OUT_OF_ORDER_TIMESTAMP",
                                         validation_rule="timestamps must be strictly increasing",
                                         message="timestamp is earlier than the previous valid timestamp"))
                try:
                    MarketBar(timestamp=timestamp, symbol=symbol, open=_decimal(row[1], "open"),
                              high=_decimal(row[2], "high"), low=_decimal(row[3], "low"),
                              close=_decimal(row[4], "close"), volume=_decimal(row[5], "volume"))
                except ValueError as exc:
                    anomaly_type = "INVALID_VOLUME" if "volume" in str(exc) else "INVALID_OHLC"
                    events.append(_event(symbol=symbol, archive=path, member=member, row=row_number,
                                         raw_timestamp=raw_timestamp, parsed_timestamp=timestamp,
                                         anomaly_type=anomaly_type, validation_rule=str(exc), message=str(exc)))
                    previous_timestamp = timestamp
                    seen.add(timestamp)
                    continue
                if not duplicate:
                    valid_timestamps.append(timestamp)
                seen.add(timestamp)
                previous_timestamp = timestamp
            provenance = "Binance Public Data issue #77" if path.name in KNOWN_BINANCE_ISSUE_77_ARCHIVES else "Binance Public Data archive"
            for previous, current in zip(valid_timestamps, valid_timestamps[1:]):
                cursor = previous + timedelta(hours=1)
                while cursor < current:
                    events.append(_event(symbol=symbol, archive=path, member=member, row=None,
                                         raw_timestamp=None, parsed_timestamp=cursor,
                                         anomaly_type="MISSING_INTERVAL", validation_rule="hourly intervals must be complete",
                                         message="missing hourly interval", source_provenance=provenance))
                    cursor += timedelta(hours=1)
    return ArchiveQualityReport(symbol, path.name, rows_processed, tuple(events), checksum_verified, tuple(valid_timestamps))


def certify(reports: list[ArchiveQualityReport]) -> str:
    events = [event for report in reports for event in report.events]
    if not events:
        return "VALID"
    if all(event.source_provenance.startswith("Binance Public Data issue #") for event in events):
        return "VALID WITH DOCUMENTED SOURCE ANOMALIES"
    return "UNUSABLE"
