"""Gate 1A deterministic data-quality treatment implementation."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from .data_ingestion import NORMALIZATION_VERSION, PARTITIONS, RESEARCH_END, RESEARCH_START, TIMEFRAME
from .data_quality import ArchiveQualityReport, DataQualityEvent

TREATMENT_PROTOCOL_VERSION = "gate1a-v1"
SOURCE_VERSION = "binance-public-data-spot-1h"


def hour(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)


def event_id(event: DataQualityEvent) -> str:
    return hashlib.sha256(json.dumps(asdict(event), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class AffectedRegion:
    start: str
    end: str
    anomaly_ids: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class ContinuityBreak:
    start: str
    end: str
    anomaly_ids: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class Exclusion:
    start: str
    end: str
    anomaly_ids: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class CertifiedSegment:
    start: str
    end: str


@dataclass(frozen=True)
class PartitionCertification:
    partition: str
    start: str
    end: str
    certification: str
    certified_segments: tuple[CertifiedSegment, ...]
    exclusions: tuple[Exclusion, ...]


@dataclass(frozen=True)
class ResearchTreatmentManifest:
    source_version: str
    treatment_protocol_version: str
    normalization_version: str
    symbol: str
    timeframe: str
    research_start: str
    research_end: str
    anomaly_ids: tuple[str, ...]
    affected_regions: tuple[AffectedRegion, ...]
    continuity_breaks: tuple[ContinuityBreak, ...]
    exclusions: tuple[Exclusion, ...]
    certified_segments: tuple[CertifiedSegment, ...]
    partitions: tuple[PartitionCertification, ...]
    source_integrity: str
    research_certification: str
    dataset_identity: str

    def to_record_without_identity(self) -> dict:
        value = asdict(self)
        value.pop("dataset_identity", None)
        return value


def _regions(reports: list[ArchiveQualityReport], research_end: datetime = RESEARCH_END) -> tuple[AffectedRegion, ...]:
    """Build affected regions using the caller's research boundary.

    The boundary is an explicit input so a manifest for a historical partition
    cannot accidentally use the module-wide Gate 1 research end date while
    applying the two-clean-bar restoration rule.
    """
    research_end = research_end.astimezone(timezone.utc)
    by_hour: dict[datetime, set[str]] = {}
    for report in reports:
        for anomaly in report.events:
            if anomaly.parsed_timestamp:
                timestamp = hour(datetime.fromisoformat(anomaly.parsed_timestamp))
                if timestamp < research_end:
                    by_hour.setdefault(timestamp, set()).add(event_id(anomaly))
    if not by_hour:
        return ()
    ordered = sorted(by_hour)
    raw: list[AffectedRegion] = []
    start = previous = ordered[0]
    ids = set(by_hour[start])
    for current in ordered[1:]:
        if current == previous + timedelta(hours=1):
            previous = current
            ids.update(by_hour[current])
        else:
            raw.append(AffectedRegion(start.isoformat(), (previous + timedelta(hours=1)).isoformat(), tuple(sorted(ids)), "contiguous affected canonical hourly intervals"))
            start = previous = current
            ids = set(by_hour[current])
    raw.append(AffectedRegion(start.isoformat(), (previous + timedelta(hours=1)).isoformat(), tuple(sorted(ids)), "contiguous affected canonical hourly intervals"))

    clean = {
        hour(ts)
        for report in reports
        for ts in report.valid_timestamps
        if hour(ts) < research_end
    }
    event_hours = set(by_hour)
    restored: list[AffectedRegion] = []
    for region in raw:
        cursor = datetime.fromisoformat(region.end)
        while cursor < research_end:
            if cursor in clean and cursor not in event_hours and cursor + timedelta(hours=1) in clean and cursor + timedelta(hours=1) not in event_hours:
                restored.append(AffectedRegion(region.start, cursor.isoformat(), region.anomaly_ids, region.reason))
                break
            cursor += timedelta(hours=1)
        else:
            restored.append(region)
    return tuple(restored)


def _segments(start: datetime, end: datetime, regions: tuple[AffectedRegion, ...]) -> tuple[CertifiedSegment, ...]:
    cursor = start
    result: list[CertifiedSegment] = []
    for region in regions:
        rs, re = datetime.fromisoformat(region.start), datetime.fromisoformat(region.end)
        if re <= start or rs >= end:
            continue
        rs, re = max(rs, start), min(re, end)
        if cursor < rs:
            result.append(CertifiedSegment(cursor.isoformat(), rs.isoformat()))
        cursor = max(cursor, re)
    if cursor < end:
        result.append(CertifiedSegment(cursor.isoformat(), end.isoformat()))
    return tuple(result)


def _exclusions(regions: tuple[AffectedRegion, ...], start: datetime, end: datetime) -> tuple[Exclusion, ...]:
    return tuple(Exclusion(max(datetime.fromisoformat(r.start), start).isoformat(), min(datetime.fromisoformat(r.end), end).isoformat(), r.anomaly_ids, r.reason)
                 for r in regions if max(datetime.fromisoformat(r.start), start) < min(datetime.fromisoformat(r.end), end))


def build_manifest(symbol: str, reports: list[ArchiveQualityReport], research_start: datetime = RESEARCH_START, research_end: datetime = RESEARCH_END) -> ResearchTreatmentManifest:
    regions = _regions(reports, research_end)
    anomalies = tuple(sorted(event_id(e) for report in reports for e in report.events))
    source_integrity = "SOURCE VERIFIED" if reports and all(r.checksum_verified for r in reports) else "SOURCE UNVERIFIED"
    unlocalized = any(e.parsed_timestamp is None and e.anomaly_type != "CHECKSUM_FAILURE" for r in reports for e in r.events)
    checksum_failure = any(e.anomaly_type == "CHECKSUM_FAILURE" for r in reports for e in r.events) or source_integrity != "SOURCE VERIFIED"
    segments = _segments(research_start, research_end, regions)
    exclusions = _exclusions(regions, research_start, research_end)
    certification = "UNVERIFIED" if checksum_failure else ("UNUSABLE" if unlocalized else ("VALID" if not regions else "VALID WITH DOCUMENTED EXCLUSIONS"))
    partitions: list[PartitionCertification] = []
    for name, (start, end) in PARTITIONS.items():
        p_segments = _segments(start, end, regions)
        p_exclusions = _exclusions(regions, start, end)
        p_cert = "UNVERIFIED" if checksum_failure else ("UNUSABLE" if unlocalized else ("VALID" if not p_exclusions else "VALID WITH DOCUMENTED EXCLUSIONS"))
        partitions.append(PartitionCertification(name, start.isoformat(), end.isoformat(), p_cert, p_segments, p_exclusions))
    breaks = tuple(ContinuityBreak(r.start, r.end, r.anomaly_ids, "research continuity cannot cross affected region") for r in regions)
    base = {
        "source_version": SOURCE_VERSION, "treatment_protocol_version": TREATMENT_PROTOCOL_VERSION,
        "normalization_version": NORMALIZATION_VERSION, "symbol": symbol, "timeframe": TIMEFRAME,
        "research_start": research_start.isoformat(), "research_end": research_end.isoformat(),
        "anomaly_ids": anomalies, "affected_regions": [asdict(x) for x in regions],
        "continuity_breaks": [asdict(x) for x in breaks], "exclusions": [asdict(x) for x in exclusions],
        "certified_segments": [asdict(x) for x in segments], "partitions": [asdict(x) for x in partitions],
        "source_integrity": source_integrity, "research_certification": certification,
    }
    identity = hashlib.sha256(json.dumps(base, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return ResearchTreatmentManifest(SOURCE_VERSION, TREATMENT_PROTOCOL_VERSION, NORMALIZATION_VERSION, symbol, TIMEFRAME,
                                    research_start.isoformat(), research_end.isoformat(), anomalies, regions, breaks,
                                    exclusions, segments, tuple(partitions), source_integrity, certification, identity)


def lookback_eligible(timestamps: Iterable[datetime], target: datetime, bars_required: int, permitted_start: datetime, permitted_end: datetime, breaks: tuple[ContinuityBreak, ...]) -> bool:
    if bars_required <= 0:
        raise ValueError("bars_required must be positive")
    target, permitted_start, permitted_end = hour(target), permitted_start.astimezone(timezone.utc), permitted_end.astimezone(timezone.utc)
    available = {hour(ts) for ts in timestamps}
    first = target - timedelta(hours=bars_required - 1)
    if target < permitted_start or target >= permitted_end or first < permitted_start or target not in available:
        return False
    for i in range(bars_required):
        point = first + timedelta(hours=i)
        if point not in available or any(datetime.fromisoformat(b.start) <= point < datetime.fromisoformat(b.end) for b in breaks):
            return False
    return True


def return_eligible(previous: datetime, current: datetime, breaks: tuple[ContinuityBreak, ...]) -> bool:
    previous, current = hour(previous), hour(current)
    if current != previous + timedelta(hours=1):
        return False
    return not any(datetime.fromisoformat(b.start) <= previous < datetime.fromisoformat(b.end) or datetime.fromisoformat(b.start) <= current < datetime.fromisoformat(b.end) for b in breaks)


def common_certified_intervals(btc: ResearchTreatmentManifest, eth: ResearchTreatmentManifest) -> tuple[CertifiedSegment, ...]:
    values: list[CertifiedSegment] = []
    for a in btc.certified_segments:
        for b in eth.certified_segments:
            start = max(datetime.fromisoformat(a.start), datetime.fromisoformat(b.start))
            end = min(datetime.fromisoformat(a.end), datetime.fromisoformat(b.end))
            if start < end:
                values.append(CertifiedSegment(start.isoformat(), end.isoformat()))
    values.sort(key=lambda x: x.start)
    merged: list[CertifiedSegment] = []
    for value in values:
        if merged and merged[-1].end == value.start:
            merged[-1] = CertifiedSegment(merged[-1].start, value.end)
        else:
            merged.append(value)
    return tuple(merged)


def common_certification(btc: ResearchTreatmentManifest, eth: ResearchTreatmentManifest) -> str:
    if btc.source_integrity != "SOURCE VERIFIED" or eth.source_integrity != "SOURCE VERIFIED":
        return "UNVERIFIED"
    if not common_certified_intervals(btc, eth):
        return "UNUSABLE"
    return "VALID" if btc.research_certification == eth.research_certification == "VALID" else "VALID WITH DOCUMENTED EXCLUSIONS"
