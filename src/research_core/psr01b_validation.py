"""PSR-01B Validation V1 bounded implementation.

This module is prospective implementation only.  It contains no authorization
to access protected Validation/OOS source data and no live source acquisition
path.  Scientific calculations delegate to the frozen PSR-01B modules.
"""
from __future__ import annotations

import csv
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import logging
import math
from pathlib import Path
import warnings
from typing import Any, Callable, Mapping, Sequence
from urllib.parse import urlparse
from zipfile import ZipFile

import numpy as np

from . import psr01b_runner as parent_runner
from .ams_dep_treatment_aware_normalization_v2 import (
    ArchiveRowAccounting,
    RejectedRawRow,
    TreatmentAwareNormalizationError,
    key_sequence_sha256,
    normalize_archive_with_treatment,
    rejected_records_sha256,
)
from .archive_security import archive_member_symbol
from .data_ingestion import normalize_row
from .data_interfaces import MarketBar, validate_market_data
from .data_quality import ArchiveQualityReport, DataQualityEvent
from .data_quality_treatment_v2 import (
    ResearchTreatmentManifest,
    build_manifest,
    event_id,
    hour,
)
from .psr01b_core import ARM_ORDER, PSR01BError, classify_success, paired_segment_bootstrap, performance_metrics, split_origin_eligible


UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "research/governance/psr01b_validation_spec_v1.json"
SPEC_MD_PATH = ROOT / "docs/PSR01B_VALIDATION_SPEC_V1.md"
APPROVED_SPEC_HEAD = "e6f20db11aaff9f9ce1e2ac73ce9324ae2a4897a"
APPROVED_SPEC_JSON_BLOB = "bd6b1a325a921ee60559ec44c54d97b3dc40e72a"
APPROVED_SPEC_MD_BLOB = "fd16d0e9c408b96e596ef3b8f86786fcde2c9e08"
REGISTRATION_ID = "PSR01B-BOUNDED-VALIDATION-SPOT-V1"
SOURCE_START = datetime(2020, 8, 31, tzinfo=UTC)
VALIDATION_START = datetime(2022, 1, 1, tzinfo=UTC)
HARD_END = datetime(2024, 1, 1, tzinfo=UTC)
PRIMARY_BLOCK_HOURS = 168
ROBUSTNESS_BLOCK_HOURS = (24, 72)
ARM_INDEX = {"PAPER_FILL": 0, "PROJECT_GAP_PRESERVING": 1}

SCIENTIFIC_NON_REPLICATION = "SCIENTIFIC_NON_REPLICATION"
TECHNICAL_INDETERMINATE = "TECHNICAL_INDETERMINATE"
PRACTICAL_BENCHMARK_FAIL = "PRACTICAL_BENCHMARK_FAIL"
VALIDATION_PASS = "PSR01B_VALIDATION_BOUNDED_H2_REPLICATION"
VALIDATION_FAIL = "PSR01B_VALIDATION_BOUNDED_H2_NOT_REPLICATED"
VALIDATION_TECHNICAL = "PSR01B_VALIDATION_TECHNICAL_INDETERMINATE"
PRACTICAL_PASS = "PSR01B_VALIDATION_PRACTICAL_BENCHMARK_PASS"
PRACTICAL_FAIL = "PSR01B_VALIDATION_PRACTICAL_BENCHMARK_FAIL"

EXPECTED_FOLD_ROWS = (
    (12, 11, "2020-10-01T00:00:00Z", "2021-10-01T00:00:00Z", "2022-01-01T00:00:00Z", "2022-04-01T00:00:00Z"),
    (13, 12, "2021-01-01T00:00:00Z", "2022-01-01T00:00:00Z", "2022-04-01T00:00:00Z", "2022-07-01T00:00:00Z"),
    (14, 13, "2021-04-01T00:00:00Z", "2022-04-01T00:00:00Z", "2022-07-01T00:00:00Z", "2022-10-01T00:00:00Z"),
    (15, 14, "2021-07-01T00:00:00Z", "2022-07-01T00:00:00Z", "2022-10-01T00:00:00Z", "2023-01-01T00:00:00Z"),
    (16, 15, "2021-10-01T00:00:00Z", "2022-10-01T00:00:00Z", "2023-01-01T00:00:00Z", "2023-04-01T00:00:00Z"),
    (17, 16, "2022-01-01T00:00:00Z", "2023-01-01T00:00:00Z", "2023-04-01T00:00:00Z", "2023-07-01T00:00:00Z"),
    (18, 17, "2022-04-01T00:00:00Z", "2023-04-01T00:00:00Z", "2023-07-01T00:00:00Z", "2023-10-01T00:00:00Z"),
    (19, 18, "2022-07-01T00:00:00Z", "2023-07-01T00:00:00Z", "2023-10-01T00:00:00Z", "2024-01-01T00:00:00Z"),
)


class ValidationContractError(PSR01BError):
    """Fail-closed technical Validation implementation error."""

    def __init__(self, message: str, *, failure_code: str = "VALIDATION_CONTRACT_ERROR"):
        super().__init__(message)
        self.failure_code = failure_code


@dataclass(frozen=True)
class TreatmentDecision:
    partition: str
    linked: bool
    failure_code: str | None


@dataclass(frozen=True)
class PhaseNormalizationResult:
    bars: tuple[MarketBar, ...]
    timestamp_unit: str
    archive_accounting: tuple[ArchiveRowAccounting, ...]


@dataclass(frozen=True)
class TerminalDecision:
    classification: str
    validation_result_token: str | None
    parent_h2_classification: str | None
    practical_benchmark_token: str | None


def _git_blob_sha1_bytes(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def git_blob_sha1(path: Path) -> str:
    try:
        payload = Path(path).read_bytes()
    except OSError as exc:
        raise ValidationContractError(
            f"cannot read pinned path: {path}",
            failure_code="PINNED_PATH_READ_FAIL",
        ) from exc
    return _git_blob_sha1_bytes(payload)


def load_validation_spec(path: Path = SPEC_PATH) -> dict[str, Any]:
    try:
        payload = Path(path).read_bytes()
        data = json.loads(payload)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationContractError(
            "cannot load PSR-01B Validation V1 specification",
            failure_code="VALIDATION_SPEC_LOAD_FAIL",
        ) from exc
    if data.get("registration_id") != REGISTRATION_ID:
        raise ValidationContractError(
            "unexpected Validation registration identity",
            failure_code="VALIDATION_REGISTRATION_ID_MISMATCH",
        )
    if Path(path).resolve() == SPEC_PATH.resolve():
        if _git_blob_sha1_bytes(payload) != APPROVED_SPEC_JSON_BLOB:
            raise ValidationContractError(
                "approved Validation JSON specification blob mismatch",
                failure_code="VALIDATION_SPEC_BLOB_MISMATCH",
            )
        if git_blob_sha1(SPEC_MD_PATH) != APPROVED_SPEC_MD_BLOB:
            raise ValidationContractError(
                "approved Validation Markdown specification blob mismatch",
                failure_code="VALIDATION_SPEC_MARKDOWN_BLOB_MISMATCH",
            )
    return data


def verify_pinned_module_identities(
    root: Path = ROOT,
    spec: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    registration = dict(spec or load_validation_spec())
    expected: dict[str, str] = {}
    expected.update(
        registration["psr_scientific_module_pin_contract"][
            "inherited_scientific_modules_git_blob_sha1"
        ]
    )
    expected.update(registration["row_treatment_contract"]["required_blob_sha1"])
    observed: dict[str, str] = {}
    for relative, wanted in expected.items():
        actual = git_blob_sha1(Path(root) / relative)
        if actual != wanted:
            raise ValidationContractError(
                f"pinned module blob mismatch: {relative}",
                failure_code="PINNED_MODULE_BLOB_MISMATCH",
            )
        observed[relative] = actual
    return observed


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ValidationContractError(
            "registered Validation timestamp must be UTC",
            failure_code="VALIDATION_TIMESTAMP_NOT_UTC",
        )
    parsed = parsed.astimezone(UTC)
    if parsed.minute or parsed.second or parsed.microsecond:
        raise ValidationContractError(
            "registered Validation boundary must be an exact hour",
            failure_code="VALIDATION_TIMESTAMP_NOT_EXACT_HOUR",
        )
    return parsed


def registered_validation_folds(
    spec: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], ...]:
    registration = dict(spec or load_validation_spec())
    raw = registration.get("folds")
    if not isinstance(raw, list) or len(raw) != 8:
        raise ValidationContractError(
            "Validation must contain exactly eight folds",
            failure_code="VALIDATION_FOLD_COUNT_DRIFT",
        )
    observed = tuple(
        (
            int(item.get("fold", -1)),
            int(item.get("fold_index", -1)),
            item.get("train_start"),
            item.get("train_end_validation_start"),
            item.get("validation_end_test_start"),
            item.get("test_end"),
        )
        for item in raw
    )
    if observed != EXPECTED_FOLD_ROWS:
        raise ValidationContractError(
            "Validation fold definitions/order drift",
            failure_code="VALIDATION_FOLD_DEFINITION_DRIFT",
        )
    out = []
    for item in raw:
        train_start = _parse_utc(item["train_start"])
        validation_start = _parse_utc(item["train_end_validation_start"])
        test_start = _parse_utc(item["validation_end_test_start"])
        test_end = _parse_utc(item["test_end"])
        if not train_start < validation_start < test_start < test_end:
            raise ValidationContractError(
                "invalid Validation fold chronology",
                failure_code="VALIDATION_FOLD_CHRONOLOGY_FAIL",
            )
        out.append(
            {
                "fold": int(item["fold"]),
                "fold_index": int(item["fold_index"]),
                "train_start": train_start,
                "validation_start": validation_start,
                "test_start": test_start,
                "test_end": test_end,
            }
        )
    return tuple(out)


def registered_archive_inventory(
    spec: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    registration = dict(spec or load_validation_spec())
    inventory = tuple(registration["source"]["registered_archive_inventory"])
    if len(inventory) != 41:
        raise ValidationContractError(
            "Validation archive inventory must contain exactly 41 archives",
            failure_code="VALIDATION_ARCHIVE_COUNT_DRIFT",
        )
    expected = []
    year, month = 2020, 8
    while (year, month) <= (2023, 12):
        expected.append(f"BTCUSDT-1h-{year:04d}-{month:02d}.zip")
        month += 1
        if month == 13:
            year, month = year + 1, 1
    if inventory != tuple(expected):
        raise ValidationContractError(
            "Validation archive inventory/order drift",
            failure_code="VALIDATION_ARCHIVE_INVENTORY_DRIFT",
        )
    return inventory


def validate_reports_for_manifest(
    reports: Sequence[ArchiveQualityReport],
    *,
    spec: Mapping[str, Any] | None = None,
) -> tuple[ArchiveQualityReport, ...]:
    registration = dict(spec or load_validation_spec())
    inventory = registered_archive_inventory(registration)
    ordered = tuple(reports)
    names = tuple(report.archive for report in ordered)
    if names != inventory:
        raise ValidationContractError(
            "scanner report inventory/order differs from registered archive inventory",
            failure_code="VALIDATION_REPORT_INVENTORY_MISMATCH",
        )
    if len(set(names)) != len(names):
        raise ValidationContractError(
            "duplicate scanner report archive",
            failure_code="VALIDATION_DUPLICATE_REPORT",
        )
    for report in ordered:
        if report.symbol != "BTCUSDT":
            raise ValidationContractError(
                "scanner report symbol mismatch",
                failure_code="VALIDATION_REPORT_SYMBOL_MISMATCH",
            )
        if not report.checksum_verified:
            raise ValidationContractError(
                "scanner report checksum is not verified",
                failure_code="VALIDATION_CHECKSUM_UNVERIFIED",
            )
        for event in report.events:
            if event.anomaly_type == "CHECKSUM_FAILURE":
                raise ValidationContractError(
                    "checksum-failure event in registered report",
                    failure_code="VALIDATION_CHECKSUM_FAILURE_EVENT",
                )
            if event.parsed_timestamp is None:
                raise ValidationContractError(
                    "unlocalized non-checksum event in registered report",
                    failure_code="VALIDATION_UNLOCALIZED_EVENT",
                )
    return ordered


def build_validation_manifest(
    reports: Sequence[ArchiveQualityReport],
    *,
    spec: Mapping[str, Any] | None = None,
) -> ResearchTreatmentManifest:
    registration = dict(spec or load_validation_spec())
    ordered = validate_reports_for_manifest(reports, spec=registration)
    manifest = build_manifest(
        "BTCUSDT",
        list(ordered),
        research_start=SOURCE_START,
        research_end=HARD_END,
    )
    if _parse_utc(manifest.research_start) != SOURCE_START:
        raise ValidationContractError(
            "Validation manifest research_start drift",
            failure_code="VALIDATION_MANIFEST_START_DRIFT",
        )
    if _parse_utc(manifest.research_end) != HARD_END:
        raise ValidationContractError(
            "Validation manifest research_end drift",
            failure_code="VALIDATION_MANIFEST_END_DRIFT",
        )
    if manifest.source_integrity != "SOURCE VERIFIED":
        raise ValidationContractError(
            "Validation manifest source integrity is not verified",
            failure_code="VALIDATION_MANIFEST_SOURCE_UNVERIFIED",
        )
    if manifest.research_certification not in {
        "VALID",
        "VALID WITH DOCUMENTED EXCLUSIONS",
    }:
        raise ValidationContractError(
            "Validation manifest certification unusable",
            failure_code="VALIDATION_MANIFEST_CERTIFICATION_FAIL",
        )
    _registered_partition(manifest, "development")
    _registered_partition(manifest, "validation")
    return manifest


def _registered_partition(manifest: Any, name: str) -> Any:
    if name not in {"development", "validation"}:
        raise ValidationContractError(
            "Validation adapter may select only Development/Validation",
            failure_code="OOS_PARTITION_SELECTION_FORBIDDEN",
        )
    partitions = manifest.partitions
    try:
        if len(partitions) < 2:
            raise ValidationContractError(
                "manifest lacks registered Development/Validation partitions",
                failure_code="VALIDATION_PARTITION_CARDINALITY_FAIL",
            )
        development = partitions[0]
        validation = partitions[1]
    except (IndexError, TypeError) as exc:
        raise ValidationContractError(
            "cannot access registered Development/Validation partitions",
            failure_code="VALIDATION_PARTITION_ACCESS_FAIL",
        ) from exc
    if development.partition != "development":
        raise ValidationContractError(
            "first registered partition is not Development",
            failure_code="DEVELOPMENT_PARTITION_IDENTITY_FAIL",
        )
    if validation.partition != "validation":
        raise ValidationContractError(
            "second registered partition is not Validation",
            failure_code="VALIDATION_PARTITION_IDENTITY_FAIL",
        )
    return development if name == "development" else validation


def partition_name_for_timestamp(timestamp: datetime) -> str:
    affected = hour(timestamp)
    if affected >= HARD_END:
        raise ValidationContractError(
            "timestamp reaches or crosses hard OOS boundary",
            failure_code="HARD_END_REJECTION",
        )
    return "development" if affected < VALIDATION_START else "validation"


def phase_treatment_decision(
    event: DataQualityEvent,
    manifest: Any,
) -> TreatmentDecision:
    if event.parsed_timestamp is None:
        raise ValidationContractError(
            "scanner event is unlocalized",
            failure_code="VALIDATION_UNLOCALIZED_EVENT",
        )
    affected = hour(datetime.fromisoformat(event.parsed_timestamp))
    partition_name = partition_name_for_timestamp(affected)
    partition = _registered_partition(manifest, partition_name)
    identifier = event_id(event)
    linked = False
    for exclusion in partition.exclusions:
        start = datetime.fromisoformat(exclusion.start)
        end = datetime.fromisoformat(exclusion.end)
        if start <= affected < end and identifier in exclusion.anomaly_ids:
            linked = True
            break
    failure_code = None
    if not linked:
        failure_code = (
            "DEVELOPMENT_TREATMENT_LINKAGE_MISSING"
            if partition_name == "development"
            else "VALIDATION_TREATMENT_LINKAGE_MISSING"
        )
    return TreatmentDecision(partition_name, linked, failure_code)


def require_phase_treatment_linkage(
    event: DataQualityEvent,
    manifest: Any,
) -> TreatmentDecision:
    decision = phase_treatment_decision(event, manifest)
    if not decision.linked:
        raise ValidationContractError(
            f"{decision.partition} scanner event lacks treatment/exclusion linkage",
            failure_code=str(decision.failure_code),
        )
    return decision


def normalize_pre_source_august_with_parent(
    path: Path,
    report: ArchiveQualityReport,
    manifest: ResearchTreatmentManifest,
) -> tuple[tuple[MarketBar, ...], tuple[str, ...], ArchiveRowAccounting]:
    path = Path(path)
    if path.name != "BTCUSDT-1h-2020-08.zip":
        raise ValidationContractError(
            "pre-source parent-normalizer helper is restricted to August 2020",
            failure_code="PRE_SOURCE_ARCHIVE_IDENTITY_FAIL",
        )
    bars, units, accounting = normalize_archive_with_treatment(
        path,
        "BTCUSDT",
        report,
        manifest,
    )
    clipped = tuple(
        bar for bar in bars if SOURCE_START <= bar.timestamp < HARD_END
    )
    return clipped, units, accounting


def _archive_member(path: Path, symbol: str) -> str:
    with ZipFile(path) as archive:
        names = [name for name in archive.namelist() if not name.endswith("/")]
    if len(names) != 1:
        raise ValidationContractError(
            "unexpected archive structure",
            failure_code="ARCHIVE_STRUCTURE_INVALID",
        )
    member = names[0]
    try:
        observed = archive_member_symbol(member)
    except ValueError as exc:
        raise ValidationContractError(
            "archive member identity invalid",
            failure_code="ARCHIVE_MEMBER_SYMBOL_INVALID",
        ) from exc
    if observed != symbol:
        raise ValidationContractError(
            "archive member symbol mismatch",
            failure_code="ARCHIVE_MEMBER_SYMBOL_MISMATCH",
        )
    return member


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
        if event.row is None or event.row != row_number:
            continue
        if event.symbol != symbol or event.archive != archive_name or event.member != member:
            raise ValidationContractError(
                "scanner event physical-row identity mismatch",
                failure_code="SCANNER_EVENT_PHYSICAL_ROW_IDENTITY_MISMATCH",
            )
        if event.raw_timestamp is not None and event.raw_timestamp != raw_timestamp:
            raise ValidationContractError(
                "scanner event raw-timestamp mismatch",
                failure_code="SCANNER_EVENT_RAW_TIMESTAMP_MISMATCH",
            )
        matches.append(event)
    return tuple(matches)


def normalize_validation_archive_with_phase_treatment(
    path: Path,
    report: ArchiveQualityReport,
    manifest: ResearchTreatmentManifest,
) -> tuple[tuple[MarketBar, ...], tuple[str, ...], ArchiveRowAccounting]:
    """Normalize one local 2022-2023 synthetic/future archive with phase linkage.

    This function performs no source acquisition.  It exists so the prospective
    Validation implementation can be reviewed and tested before protected access.
    """
    path = Path(path)
    if report.symbol != "BTCUSDT" or report.archive != path.name:
        raise ValidationContractError(
            "scanner report archive identity mismatch",
            failure_code="SCANNER_REPORT_ARCHIVE_IDENTITY_MISMATCH",
        )
    if not report.checksum_verified:
        raise ValidationContractError(
            "scanner report checksum unverified",
            failure_code="VALIDATION_CHECKSUM_UNVERIFIED",
        )
    member = _archive_member(path, "BTCUSDT")
    for event in report.events:
        if event.anomaly_type != "CHECKSUM_FAILURE" and event.parsed_timestamp is None:
            raise ValidationContractError(
                "unlocalized scanner event makes source unusable",
                failure_code="VALIDATION_UNLOCALIZED_EVENT",
            )
        if event.member is not None and event.member != member:
            raise ValidationContractError(
                "scanner event member mismatch",
                failure_code="SCANNER_EVENT_MEMBER_MISMATCH",
            )

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
                key = f"{path.name}|{member}|{row_number}|{raw_timestamp}"
                all_keys.append(key)
                events = _row_events(
                    report,
                    symbol="BTCUSDT",
                    archive_name=path.name,
                    member=member,
                    row_number=row_number,
                    raw_timestamp=raw_timestamp,
                )
                if events:
                    if not all(event.parsed_timestamp is not None for event in events):
                        raise ValidationContractError(
                            "row-level scanner event is unlocalized",
                            failure_code="VALIDATION_UNLOCALIZED_EVENT",
                        )
                    identifiers = tuple(sorted({event_id(event) for event in events}))
                    if not set(identifiers).issubset(manifest_ids):
                        raise ValidationContractError(
                            "scanner anomaly ID missing from treatment manifest",
                            failure_code="SCANNER_ANOMALY_ID_MISSING_FROM_MANIFEST",
                        )
                    for event in events:
                        require_phase_treatment_linkage(event, manifest)
                    parsed = tuple(
                        sorted(
                            {
                                str(event.parsed_timestamp)
                                for event in events
                                if event.parsed_timestamp is not None
                            }
                        )
                    )
                    rejected_rows.append(
                        RejectedRawRow(
                            symbol="BTCUSDT",
                            archive=path.name,
                            member=member,
                            physical_row_number=row_number,
                            raw_timestamp=raw_timestamp,
                            sorted_unique_parsed_timestamp_strings=parsed,
                            sorted_anomaly_ids=identifiers,
                            sorted_anomaly_types=tuple(
                                sorted({event.anomaly_type for event in events})
                            ),
                        )
                    )
                    continue
                try:
                    bar, raw = normalize_row(row, "BTCUSDT")
                except Exception as exc:
                    raise ValidationContractError(
                        "accepted row failed strict normalization",
                        failure_code="SCANNER_NORMALIZER_MISMATCH",
                    ) from exc
                bars.append(bar)
                units.append(raw.timestamp_unit)
                accepted_keys.append(key)

    if len(all_keys) != report.rows_processed:
        raise ValidationContractError(
            "scanner/raw-row accounting population mismatch",
            failure_code="SCANNER_RAW_ROW_POPULATION_MISMATCH",
        )
    if len(set(all_keys)) != len(all_keys):
        raise ValidationContractError(
            "duplicate raw-row accounting key",
            failure_code="DUPLICATE_RAW_ROW_ACCOUNTING_KEY",
        )
    if len(all_keys) != len(accepted_keys) + len(rejected_rows):
        raise ValidationContractError(
            "raw-row accounting mismatch",
            failure_code="RAW_ROW_ACCOUNTING_MISMATCH",
        )

    rejected_records = [item.to_record() for item in rejected_rows]
    accounting = ArchiveRowAccounting(
        filename=path.name,
        member=member,
        raw_data_rows=len(all_keys),
        normalized_accepted_raw_rows=len(accepted_keys),
        explicitly_rejected_raw_rows=len(rejected_rows),
        accounting_equal=True,
        all_raw_row_keys_sha256=key_sequence_sha256(all_keys),
        accepted_raw_row_keys_sha256=key_sequence_sha256(accepted_keys),
        rejected_raw_row_records_sha256=rejected_records_sha256(rejected_records),
        rejected_raw_rows=tuple(rejected_rows),
    )
    return tuple(bars), tuple(units), accounting


def normalize_registered_local_archives(
    paths: Sequence[Path],
    reports: Sequence[ArchiveQualityReport],
    manifest: ResearchTreatmentManifest,
    *,
    spec: Mapping[str, Any] | None = None,
) -> PhaseNormalizationResult:
    """Normalize already-local archives only; never acquire source bytes."""
    registration = dict(spec or load_validation_spec())
    inventory = registered_archive_inventory(registration)
    ordered_paths = tuple(sorted((Path(path) for path in paths), key=lambda p: p.name))
    if tuple(path.name for path in ordered_paths) != inventory:
        raise ValidationContractError(
            "local archive inventory differs from registered inventory",
            failure_code="VALIDATION_LOCAL_ARCHIVE_INVENTORY_MISMATCH",
        )
    ordered_reports = validate_reports_for_manifest(reports, spec=registration)
    report_by_name = {report.archive: report for report in ordered_reports}

    bars: list[MarketBar] = []
    units: set[str] = set()
    accounting: list[ArchiveRowAccounting] = []
    for path in ordered_paths:
        if path.name <= "BTCUSDT-1h-2021-12.zip":
            archive_bars, archive_units, record = normalize_archive_with_treatment(
                path,
                "BTCUSDT",
                report_by_name[path.name],
                manifest,
            )
        else:
            archive_bars, archive_units, record = normalize_validation_archive_with_phase_treatment(
                path,
                report_by_name[path.name],
                manifest,
            )
        bars.extend(
            bar for bar in archive_bars if SOURCE_START <= bar.timestamp < HARD_END
        )
        units.update(archive_units)
        accounting.append(record)

    if not bars:
        raise ValidationContractError(
            "Validation normalization produced no registered rows",
            failure_code="NO_NORMALIZED_BARS",
        )
    if len(units) != 1:
        raise ValidationContractError(
            "mixed timestamp precision across accepted rows",
            failure_code="MIXED_TIMESTAMP_PRECISION",
        )
    bars.sort(key=lambda bar: bar.timestamp)
    try:
        validate_market_data(bars)
    except ValueError as exc:
        raise ValidationContractError(
            f"accepted normalized bars fail strict ordering: {exc}",
            failure_code="NORMALIZED_BAR_VALIDATION_FAIL",
        ) from exc
    if bars[0].timestamp < SOURCE_START or bars[-1].timestamp >= HARD_END:
        raise ValidationContractError(
            "post-normalization source clip failed",
            failure_code="VALIDATION_SOURCE_CLIP_FAIL",
        )
    return PhaseNormalizationResult(tuple(bars), next(iter(units)), tuple(accounting))


def bounded_urlopen(
    url: str,
    *,
    opener: Callable[..., Any] | None = None,
    **kwargs: Any,
) -> Any:
    """Hard firewall: bounded/synthetic mode never performs external HTTP(S) I/O."""
    parsed = urlparse(str(url))
    if parsed.scheme in {"http", "https"}:
        raise ValidationContractError(
            "bounded Validation mode forbids external source URL access",
            failure_code="PROTECTED_URL_FIREWALL",
        )
    raise ValidationContractError(
        "bounded Validation mode accepts no transport URL",
        failure_code="PROTECTED_URL_FIREWALL",
    )


def run_with_operator_log_suppression(
    function: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Suppress empirical progress output without altering scientific arguments."""
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    prior_disable = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        with warnings.catch_warnings(), redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            warnings.simplefilter("ignore")
            return function(*args, **kwargs)
    finally:
        logging.disable(prior_disable)


def classify_egarch_failure(
    *,
    all_registered_orders_unavailable: bool = False,
    structural_exception: bool = False,
) -> str:
    if structural_exception:
        return TECHNICAL_INDETERMINATE
    if all_registered_orders_unavailable:
        return SCIENTIFIC_NON_REPLICATION
    raise ValidationContractError(
        "EGARCH classification requires a registered terminal condition",
        failure_code="EGARCH_CLASSIFICATION_INPUT_INVALID",
    )


def classify_forecast_vector(
    forecasts: Sequence[float],
    *,
    expected_length: int,
    model_returned_normally: bool,
) -> str | None:
    values = np.asarray(forecasts, dtype=np.float64)
    if values.ndim != 1 or len(values) != expected_length:
        return TECHNICAL_INDETERMINATE
    if not np.isfinite(values).all():
        return (
            SCIENTIFIC_NON_REPLICATION
            if model_returned_normally
            else TECHNICAL_INDETERMINATE
        )
    return None


def serialize_registered_metric(
    metric_id: str,
    value: float | int | None,
    *,
    spec: Mapping[str, Any] | None = None,
) -> tuple[float | int | None, str | None]:
    registration = dict(spec or load_validation_spec())
    table = {
        item["metric_id"]: item
        for item in registration["metric_unavailability_contract"]["table"]
    }
    if metric_id not in table:
        raise ValidationContractError(
            "unknown registered metric-unavailability ID",
            failure_code="METRIC_UNAVAILABILITY_ID_UNKNOWN",
        )
    if value is not None:
        numeric = float(value)
        if np.isfinite(numeric):
            return value, None
    item = table[metric_id]
    if item["allowed_serialization"].startswith("JSON_NULL"):
        return None, item["classification"]
    raise ValidationContractError(
        f"nonfinite metric is forbidden for {metric_id}",
        failure_code="NONFINITE_REGISTERED_METRIC_FORBIDDEN",
    )


def classify_exception(exc: BaseException) -> TerminalDecision:
    message = str(exc)
    scientific_fragments = (
        "all four EGARCH orders unavailable",
        "split has no eligible deployed rows",
        "no eligible",
        "target standard deviation",
        "forecast vector must be finite",
    )
    if isinstance(exc, PSR01BError) and any(fragment in message for fragment in scientific_fragments):
        return TerminalDecision(
            SCIENTIFIC_NON_REPLICATION,
            VALIDATION_FAIL,
            "BOUNDED_H2_NOT_REPLICATED",
            None,
        )
    return TerminalDecision(
        TECHNICAL_INDETERMINATE,
        VALIDATION_TECHNICAL,
        None,
        None,
    )


def _concat_segments(segments: Sequence[np.ndarray]) -> np.ndarray:
    if not segments:
        raise ValidationContractError(
            "no evaluation segments",
            failure_code="NO_EVALUATION_SEGMENTS",
        )
    return np.concatenate([np.asarray(segment, dtype=np.float64) for segment in segments])


def _bootstrap_record(result: Any) -> dict[str, Any]:
    return {
        "available": bool(result.available),
        "all_record_mean": result.all_record_mean,
        "inference_universe_mean": result.inference_universe_mean,
        "eligible_segments": result.eligible_segments,
        "p_value": result.p_value,
        "ci_95": result.ci_95,
        "sharpe_difference_available": result.sharpe_difference_available,
        "observed_inference_sharpe_difference": result.observed_inference_sharpe_difference,
        "sharpe_difference_ci_95": result.sharpe_difference_ci_95,
    }


def run_validation_from_normalized_bars(
    normalized_bars: Sequence[MarketBar],
    *,
    spec: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run frozen scientific procedure on already-normalized local/synthetic bars."""
    registration = dict(spec or load_validation_spec())
    folds = registered_validation_folds(registration)
    bars = tuple(normalized_bars)
    if not bars:
        raise ValidationContractError(
            "normalized Validation source rows are empty",
            failure_code="VALIDATION_NORMALIZED_SOURCE_EMPTY",
        )
    if any(bar.timestamp < SOURCE_START or bar.timestamp >= HARD_END for bar in bars):
        raise ValidationContractError(
            "normalized bar is outside registered Validation source interval",
            failure_code="VALIDATION_NORMALIZED_SOURCE_BOUNDARY_FAIL",
        )

    fold_runs_by_arm: dict[str, list[Any]] = {arm: [] for arm in ARM_ORDER}
    for arm in ARM_ORDER:
        for fold in folds:
            fold_runs_by_arm[arm].append(
                run_with_operator_log_suppression(
                    parent_runner._run_arm_fold,
                    bars,
                    arm_name=arm,
                    fold=fold,
                )
            )

    arm_records: dict[str, Any] = {}
    summaries: dict[str, dict[str, float | int | None]] = {}
    for arm in ARM_ORDER:
        runs = fold_runs_by_arm[arm]
        baseline_segments = tuple(
            segment for run in runs for segment in run.baseline_segments
        )
        cost_segments = tuple(
            segment for run in runs for segment in run.cost_aware_segments
        )
        buy_segments = tuple(
            segment for run in runs for segment in run.buy_hold_segments
        )
        momentum_segments = tuple(
            segment for run in runs for segment in run.momentum_segments
        )

        primary = paired_segment_bootstrap(
            baseline_segments,
            cost_segments,
            block_hours=PRIMARY_BLOCK_HOURS,
            arm_index=ARM_INDEX[arm],
        )
        diagnostics = {
            str(block): paired_segment_bootstrap(
                baseline_segments,
                cost_segments,
                block_hours=block,
                arm_index=ARM_INDEX[arm],
            )
            for block in ROBUSTNESS_BLOCK_HOURS
        }
        baseline_metrics = performance_metrics(_concat_segments(baseline_segments))
        cost_metrics = performance_metrics(_concat_segments(cost_segments))
        buy_metrics = performance_metrics(_concat_segments(buy_segments))
        momentum_metrics = performance_metrics(_concat_segments(momentum_segments))
        summary: dict[str, float | int | None] = {
            "all_record_mean": primary.all_record_mean,
            "inference_universe_mean": primary.inference_universe_mean,
            "eligible_primary_segments": primary.eligible_segments,
            "primary_p_value": primary.p_value,
            "cost_aware_turnover": float(sum(run.cost_aware_turnover for run in runs)),
            "baseline_turnover": float(sum(run.baseline_turnover for run in runs)),
            "cost_aware_completed_trades": int(
                sum(run.cost_aware_completed_trades for run in runs)
            ),
            "cost_aware_sharpe": cost_metrics["SHARPE"],
            "baseline_sharpe": baseline_metrics["SHARPE"],
        }
        summaries[arm] = summary
        arm_records[arm] = {
            "folds": [run.record() for run in runs],
            "baseline_metrics": baseline_metrics,
            "cost_aware_metrics": cost_metrics,
            "buy_and_hold_metrics": buy_metrics,
            "momentum_24h_metrics": momentum_metrics,
            "baseline_turnover": summary["baseline_turnover"],
            "cost_aware_turnover": summary["cost_aware_turnover"],
            "baseline_completed_trades": int(
                sum(run.baseline_completed_trades for run in runs)
            ),
            "cost_aware_completed_trades": summary["cost_aware_completed_trades"],
            "primary_168h": _bootstrap_record(primary),
            "diagnostic_24h": _bootstrap_record(diagnostics["24"]),
            "diagnostic_72h": _bootstrap_record(diagnostics["72"]),
        }

    parent_h2 = classify_success(summaries)
    practical_pass = True
    for arm in ARM_ORDER:
        cost_sharpe = arm_records[arm]["cost_aware_metrics"]["SHARPE"]
        buy_sharpe = arm_records[arm]["buy_and_hold_metrics"]["SHARPE"]
        if (
            cost_sharpe is None
            or buy_sharpe is None
            or not np.isfinite(float(cost_sharpe))
            or not np.isfinite(float(buy_sharpe))
            or not float(cost_sharpe) > float(buy_sharpe)
        ):
            practical_pass = False
    validation_token = VALIDATION_PASS if parent_h2 == "BOUNDED_H2_REPLICATION" else VALIDATION_FAIL
    practical_token = PRACTICAL_PASS if practical_pass else PRACTICAL_FAIL
    return {
        "registration_id": REGISTRATION_ID,
        "version": int(registration["version"]),
        "fold_index_base": 0,
        "trial_index_base": 0,
        "execution_order": {
            "arms": list(ARM_ORDER),
            "folds": [fold["fold"] for fold in folds],
            "fold_indices": [fold["fold_index"] for fold in folds],
            "bootstrap_hours": [168, 24, 72],
        },
        "arms": arm_records,
        "parent_h2_classification": parent_h2,
        "validation_result_token": validation_token,
        "practical_benchmark_token": practical_token,
    }


def write_json_exclusive(path: Path, record: Mapping[str, Any]) -> None:
    payload = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if path.exists() or temporary.exists():
        raise ValidationContractError(
            "Validation evidence path or staging path already exists",
            failure_code="EVIDENCE_NO_OVERWRITE_VIOLATION",
        )
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
        temporary.replace(path)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise


def build_runner_loss_incident(
    *,
    execution_sha: str,
    reviewed_candidate_sha: str,
    first_protected_request_occurred: bool,
    stage: str,
    evidence_gap_status: str,
) -> dict[str, Any]:
    if not first_protected_request_occurred:
        raise ValidationContractError(
            "runner-loss consumed-attempt state requires protected request",
            failure_code="RUNNER_LOSS_STATE_INVALID",
        )
    return {
        "execution_sha": execution_sha,
        "reviewed_candidate_sha": reviewed_candidate_sha,
        "stage": stage,
        "terminal_classification": TECHNICAL_INDETERMINATE,
        "validation_result_token": VALIDATION_TECHNICAL,
        "parent_h2_classification": None,
        "practical_benchmark_token": None,
        "first_protected_request_occurred": True,
        "protected_validation_interval_consumed": True,
        "evidence_gap_status": evidence_gap_status,
        "rerun_authorized": False,
        "oos_progression_authorized": False,
    }


def verify_bounded_static_contracts(root: Path = ROOT) -> dict[str, Any]:
    spec = load_validation_spec()
    folds = registered_validation_folds(spec)
    inventory = registered_archive_inventory(spec)
    pins = verify_pinned_module_identities(root, spec)
    if any(spec["authorization"].values()):
        raise ValidationContractError(
            "Validation authorization fields must remain false during bounded implementation",
            failure_code="BOUNDED_AUTHORIZATION_DRIFT",
        )
    return {
        "registration_id": REGISTRATION_ID,
        "approved_spec_head": APPROVED_SPEC_HEAD,
        "folds": [fold["fold"] for fold in folds],
        "fold_indices": [fold["fold_index"] for fold in folds],
        "archive_count": len(inventory),
        "pinned_module_count": len(pins),
        "protected_source_access_authorized": False,
        "oos_access_authorized": False,
    }
