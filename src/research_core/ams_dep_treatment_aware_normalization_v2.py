"""Treatment-aware raw-row normalization for AMS-DEP Development V2.

This module does not acquire market data and does not redefine Gate 1A anomaly
classification. It consumes frozen ArchiveQualityReport objects, rejects only
explicitly localized anomalous physical rows, and applies the frozen strict
normalize_row() function to every accepted row.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

from .ams_dep_pipeline import DEVELOPMENT_END, DEVELOPMENT_START
from .archive_security import archive_member_symbol
from .data_ingestion import normalize_row
from .data_interfaces import MarketBar, validate_market_data
from .data_quality import ArchiveQualityReport, DataQualityEvent
from .data_quality_treatment_v2 import ResearchTreatmentManifest, event_id, hour

ACCOUNTING_DOMAIN = "AMS_DEP_DEVELOPMENT_V2_RAW_ROW_ACCOUNTING"
ACCOUNTING_VERSION = 2
AGGREGATE_KINDS = (
    "ALL_RAW_KEYS",
    "ACCEPTED_RAW_KEYS",
    "REJECTED_RAW_RECORDS",
)


class TreatmentAwareNormalizationError(RuntimeError):
    """Raised when scanner/treatment/normalization evidence is inconsistent."""


@dataclass(frozen=True)
class RejectedRawRow:
    symbol: str
    archive: str
    member: str
    physical_row_number: int
    raw_timestamp: str
    sorted_unique_parsed_timestamp_strings: tuple[str, ...]
    sorted_anomaly_ids: tuple[str, ...]
    sorted_anomaly_types: tuple[str, ...]

    def to_record(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ArchiveRowAccounting:
    filename: str
    member: str
    raw_data_rows: int
    normalized_accepted_raw_rows: int
    explicitly_rejected_raw_rows: int
    accounting_equal: bool
    all_raw_row_keys_sha256: str
    accepted_raw_row_keys_sha256: str
    rejected_raw_row_records_sha256: str
    rejected_raw_rows: tuple[RejectedRawRow, ...]

    def to_record(self, *, include_rejected_rows: bool = True) -> dict:
        value = {
            "filename": self.filename,
            "member": self.member,
            "raw_data_rows": self.raw_data_rows,
            "normalized_accepted_raw_rows":
                self.normalized_accepted_raw_rows,
            "explicitly_rejected_raw_rows":
                self.explicitly_rejected_raw_rows,
            "accounting_equal": self.accounting_equal,
            "all_raw_row_keys_sha256": self.all_raw_row_keys_sha256,
            "accepted_raw_row_keys_sha256":
                self.accepted_raw_row_keys_sha256,
            "rejected_raw_row_records_sha256":
                self.rejected_raw_row_records_sha256,
        }
        if include_rejected_rows:
            value["rejected_raw_rows"] = [
                item.to_record() for item in self.rejected_raw_rows
            ]
        return value


@dataclass(frozen=True)
class TreatmentAwareNormalizationResult:
    symbol: str
    bars: tuple[MarketBar, ...]
    timestamp_unit: str
    archive_accounting: tuple[ArchiveRowAccounting, ...]
    aggregate_accounting: dict


def _json_ascii(value, *, sort_keys: bool = False) -> bytes:
    return json.dumps(
        value,
        sort_keys=sort_keys,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def key_sequence_sha256(sequence: list[str] | tuple[str, ...]) -> str:
    return _sha256(_json_ascii(list(sequence)))


def rejected_records_sha256(records: list[dict] | tuple[dict, ...]) -> str:
    return _sha256(_json_ascii(list(records), sort_keys=True))


def asset_aggregate_sha256(
    symbol: str,
    kind: str,
    archive_records: list[dict] | tuple[dict, ...],
) -> str:
    if kind not in AGGREGATE_KINDS:
        raise TreatmentAwareNormalizationError(
            "unexpected accounting aggregate kind"
        )
    record = {
        "domain": ACCOUNTING_DOMAIN,
        "version": ACCOUNTING_VERSION,
        "symbol": symbol,
        "kind": kind,
        "archives": list(archive_records),
    }
    return _sha256(_json_ascii(record, sort_keys=True))


def _member(path: Path, symbol: str) -> str:
    with ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
    if len(names) != 1:
        raise TreatmentAwareNormalizationError(
            "unexpected archive structure: expected exactly one data file"
        )
    member = names[0]
    if archive_member_symbol(member) != symbol:
        raise TreatmentAwareNormalizationError(
            "archive member symbol mismatch"
        )
    return member


def _manifest_development_partition(manifest: ResearchTreatmentManifest):
    matches = [
        item for item in manifest.partitions if item.partition == "development"
    ]
    if len(matches) != 1:
        raise TreatmentAwareNormalizationError(
            "exactly one Development partition required"
        )
    return matches[0]


def _dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise TreatmentAwareNormalizationError(
            "treatment timestamp must be timezone-aware"
        )
    return parsed.astimezone(timezone.utc)


def _event_linked_to_development_treatment(
    event: DataQualityEvent,
    manifest: ResearchTreatmentManifest,
) -> bool:
    if event.parsed_timestamp is None:
        return False
    parsed = _dt(event.parsed_timestamp)
    affected = hour(parsed)
    if not (DEVELOPMENT_START <= affected < DEVELOPMENT_END):
        return True
    identifier = event_id(event)
    partition = _manifest_development_partition(manifest)
    for exclusion in partition.exclusions:
        start, end = _dt(exclusion.start), _dt(exclusion.end)
        if start <= affected < end and identifier in exclusion.anomaly_ids:
            return True
    return False


def _row_events(
    report: ArchiveQualityReport,
    *,
    symbol: str,
    archive_name: str,
    member: str,
    row_number: int,
    raw_timestamp: str,
) -> tuple[DataQualityEvent, ...]:
    matches = []
    for event in report.events:
        if event.row is None:
            continue
        if event.row != row_number:
            continue
        if (
            event.symbol != symbol
            or event.archive != archive_name
            or event.member != member
        ):
            raise TreatmentAwareNormalizationError(
                "scanner event physical-row identity mismatch"
            )
        if (
            event.raw_timestamp is not None
            and event.raw_timestamp != raw_timestamp
        ):
            raise TreatmentAwareNormalizationError(
                "scanner event raw-timestamp mismatch"
            )
        matches.append(event)
    return tuple(matches)


def _validate_report_scope(
    path: Path,
    symbol: str,
    report: ArchiveQualityReport,
    member: str,
) -> None:
    if report.symbol != symbol or report.archive != path.name:
        raise TreatmentAwareNormalizationError(
            "scanner report archive identity mismatch"
        )
    manifest_unusable = [
        event
        for event in report.events
        if event.anomaly_type != "CHECKSUM_FAILURE"
        and event.parsed_timestamp is None
    ]
    if manifest_unusable:
        raise TreatmentAwareNormalizationError(
            "unlocalized scanner event makes source unusable"
        )
    for event in report.events:
        if event.member is not None and event.member != member:
            raise TreatmentAwareNormalizationError(
                "scanner event member mismatch"
            )


def normalize_archive_with_treatment(
    path: Path,
    symbol: str,
    report: ArchiveQualityReport,
    manifest: ResearchTreatmentManifest,
) -> tuple[tuple[MarketBar, ...], tuple[str, ...], ArchiveRowAccounting]:
    path = Path(path)
    member = _member(path, symbol)
    _validate_report_scope(path, symbol, report, member)

    manifest_ids = set(manifest.anomaly_ids)
    bars: list[MarketBar] = []
    units: list[str] = []
    all_keys: list[str] = []
    accepted_keys: list[str] = []
    rejected_rows: list[RejectedRawRow] = []

    with ZipFile(path) as archive:
        with archive.open(member, "r") as binary:
            text = io.TextIOWrapper(binary, encoding="utf-8", newline="")
            for row_number, row in enumerate(csv.reader(text), start=1):
                if not row or all(not cell.strip() for cell in row):
                    continue
                raw_timestamp = row[0] if row else ""
                key = (
                    f"{path.name}|{member}|{row_number}|{raw_timestamp}"
                )
                all_keys.append(key)
                events = _row_events(
                    report,
                    symbol=symbol,
                    archive_name=path.name,
                    member=member,
                    row_number=row_number,
                    raw_timestamp=raw_timestamp,
                )
                if events:
                    ids = tuple(sorted({event_id(event) for event in events}))
                    if not all(event.parsed_timestamp is not None for event in events):
                        raise TreatmentAwareNormalizationError(
                            "row-level scanner event is unlocalized"
                        )
                    if not set(ids).issubset(manifest_ids):
                        raise TreatmentAwareNormalizationError(
                            "scanner anomaly ID missing from treatment manifest"
                        )
                    if not all(
                        _event_linked_to_development_treatment(event, manifest)
                        for event in events
                    ):
                        raise TreatmentAwareNormalizationError(
                            "Development scanner event lacks treatment/exclusion linkage"
                        )
                    rejected_rows.append(
                        RejectedRawRow(
                            symbol=symbol,
                            archive=path.name,
                            member=member,
                            physical_row_number=row_number,
                            raw_timestamp=raw_timestamp,
                            sorted_unique_parsed_timestamp_strings=tuple(
                                sorted(
                                    {
                                        str(event.parsed_timestamp)
                                        for event in events
                                        if event.parsed_timestamp is not None
                                    }
                                )
                            ),
                            sorted_anomaly_ids=ids,
                            sorted_anomaly_types=tuple(
                                sorted({event.anomaly_type for event in events})
                            ),
                        )
                    )
                    continue

                try:
                    bar, raw = normalize_row(row, symbol)
                except Exception as exc:
                    raise TreatmentAwareNormalizationError(
                        "accepted raw row failed strict normalization; "
                        "scanner/normalizer mismatch"
                    ) from exc
                bars.append(bar)
                units.append(raw.timestamp_unit)
                accepted_keys.append(key)

    if len(all_keys) != report.rows_processed:
        raise TreatmentAwareNormalizationError(
            "scanner/raw-row accounting population mismatch"
        )
    if len(set(all_keys)) != len(all_keys):
        raise TreatmentAwareNormalizationError(
            "duplicate raw-row accounting key"
        )
    if len(all_keys) != len(accepted_keys) + len(rejected_rows):
        raise TreatmentAwareNormalizationError(
            "raw-row accounting mismatch"
        )

    rejected_records = [value.to_record() for value in rejected_rows]
    accounting = ArchiveRowAccounting(
        filename=path.name,
        member=member,
        raw_data_rows=len(all_keys),
        normalized_accepted_raw_rows=len(accepted_keys),
        explicitly_rejected_raw_rows=len(rejected_rows),
        accounting_equal=(
            len(all_keys) == len(accepted_keys) + len(rejected_rows)
        ),
        all_raw_row_keys_sha256=key_sequence_sha256(all_keys),
        accepted_raw_row_keys_sha256=key_sequence_sha256(accepted_keys),
        rejected_raw_row_records_sha256=
            rejected_records_sha256(rejected_records),
        rejected_raw_rows=tuple(rejected_rows),
    )
    return tuple(bars), tuple(units), accounting


def _aggregate_record(
    accounting: tuple[ArchiveRowAccounting, ...],
    kind: str,
) -> tuple[dict, ...]:
    field = {
        "ALL_RAW_KEYS": ("all_raw_row_keys_sha256", "raw_data_rows"),
        "ACCEPTED_RAW_KEYS": (
            "accepted_raw_row_keys_sha256",
            "normalized_accepted_raw_rows",
        ),
        "REJECTED_RAW_RECORDS": (
            "rejected_raw_row_records_sha256",
            "explicitly_rejected_raw_rows",
        ),
    }[kind]
    digest_field, count_field = field
    return tuple(
        {
            "filename": item.filename,
            "digest": getattr(item, digest_field),
            "count": getattr(item, count_field),
        }
        for item in accounting
    )


def normalize_development_archives(
    symbol: str,
    paths: tuple[Path, ...] | list[Path],
    reports: tuple[ArchiveQualityReport, ...] | list[ArchiveQualityReport],
    manifest: ResearchTreatmentManifest,
) -> TreatmentAwareNormalizationResult:
    ordered_paths = tuple(sorted((Path(path) for path in paths), key=lambda p: p.name))
    report_by_archive = {report.archive: report for report in reports}
    if len(report_by_archive) != len(reports):
        raise TreatmentAwareNormalizationError(
            "duplicate scanner report archive"
        )
    if tuple(report_by_archive) != tuple(sorted(report_by_archive)):
        # Dict iteration is irrelevant to identity; this check is intentionally
        # not used as ordering evidence.
        pass
    if set(report_by_archive) != {path.name for path in ordered_paths}:
        raise TreatmentAwareNormalizationError(
            "scanner report inventory differs from raw archive inventory"
        )

    bars: list[MarketBar] = []
    units: set[str] = set()
    accounting: list[ArchiveRowAccounting] = []
    for path in ordered_paths:
        archive_bars, archive_units, archive_accounting = (
            normalize_archive_with_treatment(
                path,
                symbol,
                report_by_archive[path.name],
                manifest,
            )
        )
        bars.extend(archive_bars)
        units.update(archive_units)
        accounting.append(archive_accounting)

    if not bars:
        raise TreatmentAwareNormalizationError(
            "treatment-aware normalization produced no bars"
        )
    if len(units) != 1:
        raise TreatmentAwareNormalizationError(
            "mixed timestamp precision across accepted rows"
        )

    bars.sort(key=lambda bar: bar.timestamp)
    try:
        validate_market_data(bars)
    except ValueError as exc:
        raise TreatmentAwareNormalizationError(
            f"accepted normalized bars fail strict ordering: {exc}"
        ) from exc

    accounting_tuple = tuple(accounting)
    total_raw = sum(item.raw_data_rows for item in accounting_tuple)
    total_accepted = sum(
        item.normalized_accepted_raw_rows for item in accounting_tuple
    )
    total_rejected = sum(
        item.explicitly_rejected_raw_rows for item in accounting_tuple
    )
    if total_raw != total_accepted + total_rejected:
        raise TreatmentAwareNormalizationError(
            "aggregate raw-row accounting mismatch"
        )

    aggregate = {
        "raw_data_rows": total_raw,
        "normalized_accepted_raw_rows": total_accepted,
        "explicitly_rejected_raw_rows": total_rejected,
        "accounting_equal": total_raw == total_accepted + total_rejected,
    }
    for kind, output in (
        ("ALL_RAW_KEYS", "all_raw_row_keys_sha256"),
        ("ACCEPTED_RAW_KEYS", "accepted_raw_row_keys_sha256"),
        ("REJECTED_RAW_RECORDS", "rejected_raw_row_records_sha256"),
    ):
        aggregate[output] = asset_aggregate_sha256(
            symbol,
            kind,
            _aggregate_record(accounting_tuple, kind),
        )

    return TreatmentAwareNormalizationResult(
        symbol=symbol,
        bars=tuple(bars),
        timestamp_unit=next(iter(units)),
        archive_accounting=accounting_tuple,
        aggregate_accounting=aggregate,
    )
