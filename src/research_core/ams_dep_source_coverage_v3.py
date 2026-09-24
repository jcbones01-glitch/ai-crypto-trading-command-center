"""Prospective AMS-DEP Development V3 source-coverage certification overlay.

This module is offline and deterministic. It does not acquire market data,
modify MarketBar values, or change V2 row-treatment semantics. It audits the
accepted normalized timestamp vector against the hours already certified by
the frozen base Development treatment and removes only unsupported hours from
certification.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from typing import Iterable, Sequence

from .ams_dep_pipeline import (
    DEVELOPMENT_END,
    DEVELOPMENT_START,
    recompute_treatment_manifest_identity,
)
from .data_quality_treatment_v2 import (
    AffectedRegion,
    CertifiedSegment,
    ContinuityBreak,
    Exclusion,
    PartitionCertification,
    ResearchTreatmentManifest,
)

COVERAGE_AUDIT_VERSION = "AMS_DEP_DEVELOPMENT_SOURCE_COVERAGE_V3"
COVERAGE_GAP_DOMAIN = "AMS_DEP_DEVELOPMENT_V3_SOURCE_COVERAGE_GAP"
COVERAGE_GAP_VERSION = 3
COVERAGE_GAP_REASON = (
    "BASE_CERTIFIED_HOUR_ABSENT_FROM_ACCEPTED_NORMALIZED_SOURCE"
)
EMPTY_CERTIFICATION_CODE = "EMPTY_FINAL_DEVELOPMENT_CERTIFICATION"
BOUNDARY_UNACCOUNTED_CODE = "ARCHIVE_BOUNDARY_COVERAGE_UNACCOUNTED"

_ARCHIVE_RE = re.compile(
    r"^(?P<symbol>[A-Z0-9]+)-1h-(?P<year>\d{4})-(?P<month>\d{2})\.zip$"
)


class SourceCoverageV3Error(RuntimeError):
    """Coverage/certification integrity failure with durable evidence."""

    def __init__(
        self,
        message: str,
        *,
        failure_code: str,
        coverage_evidence: dict | None = None,
    ):
        super().__init__(message)
        self.failure_code = failure_code
        self.coverage_evidence = (
            None if coverage_evidence is None else dict(coverage_evidence)
        )


@dataclass(frozen=True)
class CoverageGapV3:
    start: str
    end: str
    coverage_gap_id: str
    reason: str = COVERAGE_GAP_REASON

    def to_record(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class CoverageAuditV3:
    symbol: str
    final_manifest: ResearchTreatmentManifest
    evidence: dict


def _dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SourceCoverageV3Error(
            "coverage timestamp must be timezone-aware",
            failure_code="COVERAGE_TIMESTAMP_NOT_AWARE",
        )
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _hour_aligned(value: datetime) -> bool:
    return (
        value.tzinfo is not None
        and value.utcoffset() is not None
        and value.minute == 0
        and value.second == 0
        and value.microsecond == 0
    )


def _json_ascii(value, *, sort_keys: bool = False) -> bytes:
    return json.dumps(
        value,
        sort_keys=sort_keys,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def timestamp_vector_sha256(values: Sequence[str]) -> str:
    return _sha256_bytes(_json_ascii(list(values)))


def record_sequence_sha256(values: Sequence[dict]) -> str:
    return _sha256_bytes(_json_ascii(list(values), sort_keys=True))


def coverage_gap_id(symbol: str, start: str, end: str) -> str:
    record = {
        "domain": COVERAGE_GAP_DOMAIN,
        "version": COVERAGE_GAP_VERSION,
        "symbol": symbol,
        "start": start,
        "end": end,
        "reason": COVERAGE_GAP_REASON,
    }
    return _sha256_bytes(_json_ascii(record, sort_keys=True))


def _development_partition(
    manifest: ResearchTreatmentManifest,
) -> PartitionCertification:
    matches = [
        item for item in manifest.partitions
        if item.partition == "development"
    ]
    if len(matches) != 1:
        raise SourceCoverageV3Error(
            "exactly one base Development partition required",
            failure_code="BASE_DEVELOPMENT_PARTITION_CARDINALITY_FAIL",
        )
    partition = matches[0]
    if (
        _dt(partition.start) != DEVELOPMENT_START
        or _dt(partition.end) != DEVELOPMENT_END
    ):
        raise SourceCoverageV3Error(
            "base Development partition boundary mismatch",
            failure_code="BASE_DEVELOPMENT_BOUNDARY_MISMATCH",
        )
    return partition


def _segment_hours(
    segments: Sequence[CertifiedSegment],
) -> tuple[datetime, ...]:
    ordered = tuple(
        sorted(segments, key=lambda item: (_dt(item.start), _dt(item.end)))
    )
    out: list[datetime] = []
    previous_end: datetime | None = None
    for segment in ordered:
        start, end = _dt(segment.start), _dt(segment.end)
        if not _hour_aligned(start) or not _hour_aligned(end):
            raise SourceCoverageV3Error(
                "base certified segment boundary is not hour-aligned",
                failure_code="BASE_CERTIFIED_SEGMENT_NOT_HOUR_ALIGNED",
            )
        if end <= start:
            raise SourceCoverageV3Error(
                "base certified segment must be nonempty",
                failure_code="BASE_CERTIFIED_SEGMENT_EMPTY",
            )
        if previous_end is not None and start < previous_end:
            raise SourceCoverageV3Error(
                "base certified segments overlap",
                failure_code="BASE_CERTIFIED_SEGMENT_OVERLAP",
            )
        cursor = start
        while cursor < end:
            out.append(cursor)
            cursor += timedelta(hours=1)
        previous_end = end
    if len(set(out)) != len(out):
        raise SourceCoverageV3Error(
            "base certified-hour vector contains duplicates",
            failure_code="BASE_CERTIFIED_HOUR_DUPLICATE",
        )
    return tuple(out)


def _accepted_hours(values: Iterable[datetime]) -> tuple[datetime, ...]:
    accepted = tuple(
        value.astimezone(timezone.utc)
        if value.tzinfo is not None and value.utcoffset() is not None
        else value
        for value in values
    )
    previous: datetime | None = None
    seen: set[datetime] = set()
    for value in accepted:
        if value.tzinfo is None or value.utcoffset() is None:
            raise SourceCoverageV3Error(
                "accepted timestamp must be timezone-aware",
                failure_code="ACCEPTED_TIMESTAMP_NOT_AWARE",
            )
        if not _hour_aligned(value):
            raise SourceCoverageV3Error(
                "accepted timestamp is not on an exact UTC hour",
                failure_code="ACCEPTED_TIMESTAMP_NOT_HOUR_ALIGNED",
            )
        if not (DEVELOPMENT_START <= value < DEVELOPMENT_END):
            raise SourceCoverageV3Error(
                "accepted timestamp lies outside Development",
                failure_code="ACCEPTED_TIMESTAMP_OUTSIDE_DEVELOPMENT",
            )
        if value in seen:
            raise SourceCoverageV3Error(
                "accepted timestamp vector contains duplicates",
                failure_code="ACCEPTED_TIMESTAMP_DUPLICATE",
            )
        if previous is not None and value <= previous:
            raise SourceCoverageV3Error(
                "accepted timestamp vector is not strictly increasing",
                failure_code="ACCEPTED_TIMESTAMP_ORDER_FAIL",
            )
        seen.add(value)
        previous = value
    return accepted


def _inside(timestamp: datetime, start: str, end: str) -> bool:
    return _dt(start) <= timestamp < _dt(end)


def _inside_any(timestamp: datetime, intervals: Sequence) -> bool:
    return any(_inside(timestamp, item.start, item.end) for item in intervals)


def _coalesce_missing(
    symbol: str,
    missing: Sequence[datetime],
) -> tuple[CoverageGapV3, ...]:
    if not missing:
        return ()
    gaps: list[CoverageGapV3] = []
    start = previous = missing[0]
    for current in missing[1:]:
        if current == previous + timedelta(hours=1):
            previous = current
            continue
        end = previous + timedelta(hours=1)
        start_iso, end_iso = _iso(start), _iso(end)
        gaps.append(
            CoverageGapV3(
                start=start_iso,
                end=end_iso,
                coverage_gap_id=coverage_gap_id(
                    symbol, start_iso, end_iso
                ),
            )
        )
        start = previous = current
    end = previous + timedelta(hours=1)
    start_iso, end_iso = _iso(start), _iso(end)
    gaps.append(
        CoverageGapV3(
            start=start_iso,
            end=end_iso,
            coverage_gap_id=coverage_gap_id(symbol, start_iso, end_iso),
        )
    )
    return tuple(gaps)


def _segments_from_hours(
    values: Sequence[datetime],
) -> tuple[CertifiedSegment, ...]:
    if not values:
        return ()
    result: list[CertifiedSegment] = []
    start = previous = values[0]
    for current in values[1:]:
        if current == previous + timedelta(hours=1):
            previous = current
            continue
        result.append(
            CertifiedSegment(_iso(start), _iso(previous + timedelta(hours=1)))
        )
        start = previous = current
    result.append(
        CertifiedSegment(_iso(start), _iso(previous + timedelta(hours=1)))
    )
    return tuple(result)


def _interval_records(values: Sequence) -> list[dict]:
    return [asdict(item) for item in values]


def _sort_interval_records(values: Sequence) -> tuple:
    return tuple(
        sorted(
            values,
            key=lambda item: (
                item.start,
                item.end,
                item.reason,
                tuple(item.anomaly_ids),
            ),
        )
    )


def _build_coverage_manifest(
    base: ResearchTreatmentManifest,
    gaps: Sequence[CoverageGapV3],
    final_segments: Sequence[CertifiedSegment],
) -> ResearchTreatmentManifest:
    base_development = _development_partition(base)

    coverage_regions = tuple(
        AffectedRegion(
            item.start,
            item.end,
            (item.coverage_gap_id,),
            COVERAGE_GAP_REASON,
        )
        for item in gaps
    )
    coverage_exclusions = tuple(
        Exclusion(
            item.start,
            item.end,
            (item.coverage_gap_id,),
            COVERAGE_GAP_REASON,
        )
        for item in gaps
    )
    coverage_breaks = tuple(
        ContinuityBreak(
            item.start,
            item.end,
            (item.coverage_gap_id,),
            COVERAGE_GAP_REASON,
        )
        for item in gaps
    )

    affected_regions = _sort_interval_records(
        tuple(base.affected_regions) + coverage_regions
    )
    exclusions = _sort_interval_records(
        tuple(base.exclusions) + coverage_exclusions
    )
    continuity_breaks = _sort_interval_records(
        tuple(base.continuity_breaks) + coverage_breaks
    )
    development_exclusions = _sort_interval_records(
        tuple(base_development.exclusions) + coverage_exclusions
    )
    final_segments_tuple = tuple(
        sorted(final_segments, key=lambda item: (item.start, item.end))
    )
    certification = (
        "VALID WITH DOCUMENTED EXCLUSIONS"
        if development_exclusions
        else "VALID"
    )

    partitions = []
    for partition in base.partitions:
        if partition.partition == "development":
            partitions.append(
                PartitionCertification(
                    partition="development",
                    start=partition.start,
                    end=partition.end,
                    certification=certification,
                    certified_segments=final_segments_tuple,
                    exclusions=development_exclusions,
                )
            )
        else:
            partitions.append(partition)

    provisional = ResearchTreatmentManifest(
        source_version=base.source_version,
        treatment_protocol_version=base.treatment_protocol_version,
        normalization_version=base.normalization_version,
        symbol=base.symbol,
        timeframe=base.timeframe,
        research_start=base.research_start,
        research_end=base.research_end,
        anomaly_ids=tuple(base.anomaly_ids),
        affected_regions=affected_regions,
        continuity_breaks=continuity_breaks,
        exclusions=exclusions,
        certified_segments=final_segments_tuple,
        partitions=tuple(partitions),
        source_integrity=base.source_integrity,
        research_certification=certification,
        dataset_identity="",
    )
    identity = recompute_treatment_manifest_identity(provisional)
    return replace(provisional, dataset_identity=identity)


def _month_boundary(right_archive: str) -> datetime:
    match = _ARCHIVE_RE.fullmatch(right_archive)
    if not match:
        raise SourceCoverageV3Error(
            f"invalid registered archive filename: {right_archive}",
            failure_code="REGISTERED_ARCHIVE_FILENAME_INVALID",
        )
    year, month = int(match.group("year")), int(match.group("month"))
    return datetime(year, month, 1, tzinfo=timezone.utc)


def _boundary_status(
    timestamp: datetime,
    *,
    observed: set[datetime],
    base_hours: set[datetime],
    base_exclusions: Sequence[Exclusion],
    missing: set[datetime],
    final_hours: set[datetime],
) -> dict:
    inside_development = (
        DEVELOPMENT_START <= timestamp < DEVELOPMENT_END
    )
    base_excluded = (
        inside_development and _inside_any(timestamp, base_exclusions)
    )
    base_certified = timestamp in base_hours
    observed_accepted = timestamp in observed
    v3_coverage_excluded = timestamp in missing
    final_certified = timestamp in final_hours
    fully_accounted = (
        not inside_development
        or base_excluded
        or (
            base_certified
            and (observed_accepted or v3_coverage_excluded)
        )
    )
    return {
        "inside_development": inside_development,
        "observed_accepted": observed_accepted,
        "base_certified": base_certified,
        "base_excluded": base_excluded,
        "v3_coverage_excluded": v3_coverage_excluded,
        "final_certified": final_certified,
        "fully_accounted": fully_accounted,
    }


def _boundary_records(
    archive_filenames: Sequence[str],
    *,
    observed: set[datetime],
    base_hours: set[datetime],
    base_exclusions: Sequence[Exclusion],
    missing: set[datetime],
    final_hours: set[datetime],
) -> tuple[dict, ...]:
    values = tuple(archive_filenames)
    if len(set(values)) != len(values):
        raise SourceCoverageV3Error(
            "registered archive filenames must be unique",
            failure_code="REGISTERED_ARCHIVE_FILENAME_DUPLICATE",
        )
    records: list[dict] = []
    for left, right in zip(values, values[1:]):
        boundary = _month_boundary(right)
        left_hour = boundary - timedelta(hours=1)
        right_hour = boundary
        left_status = _boundary_status(
            left_hour,
            observed=observed,
            base_hours=base_hours,
            base_exclusions=base_exclusions,
            missing=missing,
            final_hours=final_hours,
        )
        right_status = _boundary_status(
            right_hour,
            observed=observed,
            base_hours=base_hours,
            base_exclusions=base_exclusions,
            missing=missing,
            final_hours=final_hours,
        )
        record = {
            "left_archive": left,
            "right_archive": right,
            "boundary_timestamp": _iso(boundary),
            "left_expected_hour": _iso(left_hour),
            "right_expected_hour": _iso(right_hour),
            "left": left_status,
            "right": right_status,
            "boundary_fully_accounted": bool(
                left_status["fully_accounted"]
                and right_status["fully_accounted"]
            ),
        }
        records.append(record)
        if not record["boundary_fully_accounted"]:
            evidence = {
                "evidence_status": "PARTIAL_COVERAGE_AUDIT",
                "failure_code": BOUNDARY_UNACCOUNTED_CODE,
                "adjacent_archive_boundary_records_exact": records,
            }
            raise SourceCoverageV3Error(
                "adjacent archive boundary is not fully accounted",
                failure_code=BOUNDARY_UNACCOUNTED_CODE,
                coverage_evidence=evidence,
            )
    return tuple(records)


def audit_development_source_coverage_v3(
    symbol: str,
    base_manifest: ResearchTreatmentManifest,
    accepted_timestamps: Iterable[datetime],
    archive_filenames: Sequence[str],
) -> CoverageAuditV3:
    """Build the V3 monotone coverage-certification overlay and evidence."""
    if base_manifest.symbol != symbol:
        raise SourceCoverageV3Error(
            "coverage/base-manifest symbol mismatch",
            failure_code="COVERAGE_MANIFEST_SYMBOL_MISMATCH",
        )
    base_development = _development_partition(base_manifest)
    base_segments = tuple(base_development.certified_segments)
    base_segment_records = _interval_records(base_segments)
    base_hours = _segment_hours(base_segments)
    if not base_hours:
        raise SourceCoverageV3Error(
            "base Development certification contains no certified hours",
            failure_code=EMPTY_CERTIFICATION_CODE,
            coverage_evidence={
                "evidence_status": "PARTIAL_COVERAGE_AUDIT",
                "base_certified_segment_records_exact":
                    base_segment_records,
            },
        )

    accepted = _accepted_hours(accepted_timestamps)
    accepted_strings = tuple(_iso(value) for value in accepted)
    base_set = set(base_hours)
    accepted_set = set(accepted)

    for timestamp in accepted:
        if (
            timestamp not in base_set
            and not _inside_any(timestamp, base_development.exclusions)
        ):
            raise SourceCoverageV3Error(
                "accepted timestamp is neither base-certified nor base-excluded",
                failure_code="ACCEPTED_TIMESTAMP_NOT_BASE_ACCOUNTED",
                coverage_evidence={
                    "evidence_status": "PARTIAL_COVERAGE_AUDIT",
                    "accepted_normalized_timestamp_vector_exact":
                        list(accepted_strings),
                    "accepted_timestamp_vector_sha256":
                        timestamp_vector_sha256(accepted_strings),
                    "base_certified_segment_records_exact":
                        base_segment_records,
                },
            )

    missing = tuple(value for value in base_hours if value not in accepted_set)
    final = tuple(value for value in base_hours if value in accepted_set)
    missing_strings = tuple(_iso(value) for value in missing)
    final_strings = tuple(_iso(value) for value in final)

    if not final:
        raise SourceCoverageV3Error(
            "V3 final Development certification is empty",
            failure_code=EMPTY_CERTIFICATION_CODE,
            coverage_evidence={
                "evidence_status": "COMPLETE_COVERAGE_SET_EMPTY",
                "accepted_normalized_timestamp_vector_exact":
                    list(accepted_strings),
                "accepted_timestamp_vector_sha256":
                    timestamp_vector_sha256(accepted_strings),
                "base_certified_segment_records_exact":
                    base_segment_records,
                "missing_coverage_hour_vector_exact":
                    list(missing_strings),
                "missing_coverage_hour_vector_sha256":
                    timestamp_vector_sha256(missing_strings),
            },
        )

    gaps = _coalesce_missing(symbol, missing)
    final_segments = _segments_from_hours(final)
    if not final_segments:
        raise SourceCoverageV3Error(
            "V3 final certified segment collection is empty",
            failure_code=EMPTY_CERTIFICATION_CODE,
        )

    # Independent V3 exact-grid self-check before the canonical verifier.
    for segment in final_segments:
        start, end = _dt(segment.start), _dt(segment.end)
        expected: list[datetime] = []
        cursor = start
        while cursor < end:
            expected.append(cursor)
            cursor += timedelta(hours=1)
        actual = [
            value for value in accepted
            if start <= value < end
        ]
        if tuple(actual) != tuple(expected):
            raise SourceCoverageV3Error(
                "V3 final certified segment hourly grid mismatch",
                failure_code="V3_FINAL_CERTIFIED_GRID_MISMATCH",
            )

    coverage_manifest = _build_coverage_manifest(
        base_manifest, gaps, final_segments
    )
    if tuple(coverage_manifest.anomaly_ids) != tuple(base_manifest.anomaly_ids):
        raise SourceCoverageV3Error(
            "coverage-aware top-level anomaly_ids changed",
            failure_code="COVERAGE_TOP_LEVEL_ANOMALY_IDS_CHANGED",
        )

    boundary_records = _boundary_records(
        archive_filenames,
        observed=accepted_set,
        base_hours=base_set,
        base_exclusions=base_development.exclusions,
        missing=set(missing),
        final_hours=set(final),
    )

    if len(archive_filenames) == 53 and len(boundary_records) != 52:
        raise SourceCoverageV3Error(
            "complete asset must contain exactly 52 boundary records",
            failure_code="ARCHIVE_BOUNDARY_RECORD_COUNT_MISMATCH",
        )

    gap_records = [item.to_record() for item in gaps]
    final_segment_records = _interval_records(final_segments)
    base_exclusion_records = _interval_records(base_development.exclusions)
    added_exclusion_records = [
        {
            "start": item.start,
            "end": item.end,
            "anomaly_ids": (item.coverage_gap_id,),
            "reason": COVERAGE_GAP_REASON,
        }
        for item in gaps
    ]
    final_partition = _development_partition(coverage_manifest)
    final_exclusion_records = _interval_records(final_partition.exclusions)

    evidence = {
        "evidence_status": "COMPLETE_SOURCE_COVERAGE_AUDIT",
        "coverage_audit_version": COVERAGE_AUDIT_VERSION,
        "registered_development_start": DEVELOPMENT_START.isoformat(),
        "registered_development_end": DEVELOPMENT_END.isoformat(),
        "accepted_normalized_row_count": len(accepted_strings),
        "accepted_first_timestamp":
            accepted_strings[0] if accepted_strings else None,
        "accepted_last_timestamp":
            accepted_strings[-1] if accepted_strings else None,
        "accepted_normalized_timestamp_vector_exact":
            list(accepted_strings),
        "accepted_timestamp_vector_sha256":
            timestamp_vector_sha256(accepted_strings),
        "base_certified_segment_records_exact": base_segment_records,
        "base_certified_hour_count": len(base_hours),
        "base_certified_hour_vector_sha256":
            timestamp_vector_sha256(tuple(_iso(x) for x in base_hours)),
        "missing_coverage_hour_count": len(missing_strings),
        "missing_coverage_hour_vector_exact": list(missing_strings),
        "missing_coverage_hour_vector_sha256":
            timestamp_vector_sha256(missing_strings),
        "coverage_gap_intervals_exact": gap_records,
        "coverage_gap_ids_exact":
            [item.coverage_gap_id for item in gaps],
        "final_certified_hour_count": len(final_strings),
        "final_certified_hour_vector_sha256":
            timestamp_vector_sha256(final_strings),
        "final_certified_segments_exact": final_segment_records,
        "final_certified_segments_sha256":
            record_sequence_sha256(final_segment_records),
        "base_exclusion_count_and_hash": {
            "count": len(base_exclusion_records),
            "sha256": record_sequence_sha256(base_exclusion_records),
        },
        "added_coverage_exclusion_count_and_hash": {
            "count": len(added_exclusion_records),
            "sha256": record_sequence_sha256(added_exclusion_records),
        },
        "final_exclusion_count_and_hash": {
            "count": len(final_exclusion_records),
            "sha256": record_sequence_sha256(final_exclusion_records),
        },
        "adjacent_archive_boundary_records_exact":
            list(boundary_records),
        "adjacent_archive_boundary_records_sha256":
            record_sequence_sha256(boundary_records),
        "base_treatment_manifest_identity": base_manifest.dataset_identity,
        "final_coverage_aware_manifest_identity":
            coverage_manifest.dataset_identity,
        "coverage_overlay_only_removes_base_certification": True,
        "no_market_bar_created_or_modified": True,
    }
    return CoverageAuditV3(
        symbol=symbol,
        final_manifest=coverage_manifest,
        evidence=evidence,
    )
