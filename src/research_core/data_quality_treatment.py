"""Deterministic Gate 1A data-quality treatment and certification layer."""
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


def _hour(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)


def _event_id(event: DataQualityEvent) -> str:
    payload = json.dumps(asdict(event), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


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
        record = asdict(self)
        record.pop("dataset_identity", None)
        return record


def _identity(record: dict) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(payload).hexdigest()


def _merge_hours(hours: Iterable[datetime], event_ids_by_hour: dict[datetime, set[str]]) -> list[AffectedRegion]:
    ordered = sorted(set(hours))
    if not ordered:
        return []
    regions: list[AffectedRegion] = []
    start = previous = ordered[0]
    ids = set(event_ids_by_hour.get(start, set()))
    for current in ordered[1:]:
        if current == previous + timedelta(hours=1):
            previous = current
            ids.update(event_ids_by_hour.get(current, set()))
            continue
        regions.append(AffectedRegion(start.isoformat(), (previous + timedelta(hours=1)).isoformat(), tuple(sorted(ids)), "contiguous affected canonical hourly intervals"))
        start = previous = current
        ids = set(event_ids_by_hour.get(current, set()))
    regions.append(AffectedRegion(start.isoformat(), (previous + timedelta(hours=1)).isoformat(), tuple(sorted(ids)), "contiguous affected canonical hourly intervals"))
    return regions


def _restored_end(region: AffectedRegion, reports: list[ArchiveQualityReport]) -> AffectedRegion:
    """Require two consecutive clean canonical bars after the last affected hour."""
    end = datetime.fromisoformat(region.end)
    event_times = {
        _hour(datetime.fromisoformat(event.parsed_timestamp))
        for report in reports
        for event in report.events
        if event.parsed_timestamp
    }
    clean = set()
    for report in reports:
        for timestamp in report.valid_timestamps:
            timestamp = _hour(timestamp)
            if timestamp not in event_times:
                clean.add(timestamp)
    cursor = end
    while cursor < RESEARCH_END:
        if cursor in clean and cursor + timedelta(hours=1) in clean:
            return AffectedRegion(region.start, cursor.isoformat(), region.anomaly_ids, region.reason)
        cursor += timedelta(hours=1)
    return region


def build_affected_regions(reports: list[ArchiveQualityReport]) -> tuple[AffectedRegion, ...]:
    """Build deterministic regions from anomaly events and canonical timestamps.

    Start: the UTC hour containing the earliest timestamp implicated by an anomaly.
    Continuation: adjacent affected canonical hours are merged.
    Termination: the first clean canonical hour after the region, provided that
    hour and the immediately following hour are both clean source-valid bars.
    Those restoration bars are not excluded.
    """
    event_ids_by_hour: dict[datetime, set[str]] = {}
    for report in reports:
        for event in report.events:
            if event.parsed_timestamp:
                timestamp = _hour(datetime.fromisoformat(event.parsed_timestamp))
                event_ids_by_hour.setdefault(timestamp, set()).add(_event_id(event))
    regions = _merge_hours(event_ids_by_hour.keys(), event_ids_by_hour)
    return tuple(_restored_end(region, reports) for region in regions)


def _segments(start: datetime, end: datetime, regions: tuple[AffectedRegion, ...]) -> tuple[CertifiedSegment, ...]:
    cursor = start
    result: list[CertifiedSegment] = []
    for region in regions:
        rs = datetime.fromisoformat(region.start)
        re = datetime.fromisoformat(region.end)
        if re <= start or rs >= end:
            continue
        rs = max(rs, start)
        re = min(re, end)
        if cursor < rs:
            result.append(CertifiedSegment(cursor.isoformat(), rs.isoformat()))
        cursor = max(cursor, re)
    if cursor < end:
        result.append(CertifiedSegment(cursor.isoformat(), end.isoformat()))
    return tuple(result)


def _exclusions(regions: tuple[AffectedRegion, ...], start: datetime, end: datetime) -> tuple[Exclusion, ...]:
    result: list[Exclusion] = []
    for region in regions:
        rs = max(datetime.fromisoformat(region.start), start)
        re = min(datetime.fromisoformat(region.end), end)
        if rs < re:
            result.append(Exclusion(rs.isoformat(), re.isoformat(), region.anomaly_ids, region.reason))
    return tuple(result)


def _partition_certification(segments: tuple[CertifiedSegment, ...], exclusions: tuple[Exclusion, ...], source_integrity: str) -> str:
    if source_integrity != "SOURCE VERIFIED":
        return "UNVERIFIED"
    if not exclusions:
        return "VALID"
    return "VALID WITH DOCUMENTED EXCLUSIONS" if segments else "UNUSABLE"


def _research_certification(source_integrity: str, regions: tuple[AffectedRegion, ...], segments: tuple[CertifiedSegment, ...]) -> str:
    if source_integrity != "SOURCE VERIFIED":
        return "UNVERIFIED"
    if not regions:
        return "VALID"
    return "VALID WITH DOCUMENTED EXCLUSIONS" if segments else "UNUSABLE"


def build_manifest(symbol: str, reports: list[ArchiveQualityReport], research_start: datetime = RESEARCH_START, research_end: datetime = RESEARCH_END) -> ResearchTreatmentManifest:
    """Create a fully deterministic, strategy-blind treatment manifest."""
    regions = build_affected_regions(reports)
    anomaly_ids = tuple(sorted(_event_id(event) for report in reports for event in report.events))
    source_integrity = "SOURCE VERIFIED" if reports and all(report.checksum_verified for report in reports) else "SOURCE UNVERIFIED"
    segments = _segments(research_start, research_end, regions)
    exclusions = _exclusions(regions, research_start, research_end)
    partitions: list[PartitionCertification] = []
    for name, (start, end) in PARTITIONS.items():
        p_exclusions = _exclusions(regions, start, end)
        p_segments = _segments(start, end, regions)
        partitions.append(PartitionCertification(name, start.isoformat(), end.isoformat(), _partition_certification(p_segments, p_exclusions, source_integrity), p_segments, p_exclusions))
    certification = _research_certification(source_integrity, regions, segments)
    breaks = tuple(ContinuityBreak(x.start, x.end, x.anomaly_ids, "research continuity cannot cross affected region") for x in regions)
    base = {
        "source_version": SOURCE_VERSION,
        "treatment_protocol_version": TREATMENT_PROTOCOL_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
        "symbol": symbol,
        "timeframe": TIMEFRAME,
        "research_start": research_start.isoformat(),
        "research_end": research_end.isoformat(),
        "anomaly_ids": anomaly_ids,
        "affected_regions": [asdict(x) for x in regions],
        "continuity_breaks": [asdict(x) for x in breaks],
        "exclusions": [asdict(x) for x in exclusions],
        "certified_segments": [asdict(x) for x in segments],
        "partitions": [asdict(x) for x in partitions],
        "source_integrity": source_integrity,
        "research_certification": certification,
    }
    identity = _identity(base)
    return ResearchTreatmentManifest(SOURCE_VERSION, TREATMENT_PROTOCOL_VERSION, NORMALIZATION_VERSION, symbol, TIMEFRAME, research_start.isoformat(), research_end.isoformat(), anomaly_ids, regions, breaks, exclusions, segments, tuple(partitions), source_integrity, certification, identity)


def lookback_eligible(timestamps: Iterable[datetime], target: datetime, bars_required: int, permitted_start: datetime, permitted_end: datetime, breaks: tuple[ContinuityBreak, ...]) -> bool:
    """Return true only when N canonical consecutive bars are certified."""
    if bars_required <= 0:
        raise ValueError("bars_required must be positive")
    target = _hour(target)
    permitted_start = permitted_start.astimezone(timezone.utc)
    permitted_end = permitted_end.astimezone(timezone.utc)
    available = {_hour(ts) for ts in timestamps}
    if target < permitted_start or target >= permitted_end or target not in available:
        return False
    first = target - timedelta(hours=bars_required - 1)
    if first < permitted_start:
        return False
    for index in range(bars_required):
        ts = first + timedelta(hours=index)
        if ts not in available:
            return False
        if any(datetime.fromisoformat(br.start) <= ts < datetime.fromisoformat(br.end) for br in breaks):
            return False
    return True


def return_eligible(previous: datetime, current: datetime, breaks: tuple[ContinuityBreak, ...]) -> bool:
    """A return is eligible only for adjacent canonical hourly observations."""
    previous = _hour(previous)
    current = _hour(current)
    if current != previous + timedelta(hours=1):
        return False
    return not any(datetime.fromisoformat(br.start) <= previous < datetime.fromisoformat(br.end) or datetime.fromisoformat(br.start) <= current < datetime.fromisoformat(br.end) for br in breaks)


def common_certified_intervals(btc: ResearchTreatmentManifest, eth: ResearchTreatmentManifest) -> tuple[CertifiedSegment, ...]:
    """Intersect certified continuous segments using deterministic half-open intervals."""
    result: list[CertifiedSegment] = []
    for left in btc.certified_segments:
        ls, le = datetime.fromisoformat(left.start), datetime.fromisoformat(left.end)
        for right in eth.certified_segments:
            rs, re = datetime.fromisoformat(right.start), datetime.fromisoformat(right.end)
            start, end = max(ls, rs), min(le, re)
            if start < end:
                result.append(CertifiedSegment(start.isoformat(), end.isoformat()))
    result.sort(key=lambda segment: segment.start)
    merged: list[CertifiedSegment] = []
    for segment in result:
        if merged and merged[-1].end == segment.start:
            merged[-1] = CertifiedSegment(merged[-1].start, segment.end)
        else:
            merged.append(segment)
    return tuple(merged)


def common_certification(btc: ResearchTreatmentManifest, eth: ResearchTreatmentManifest) -> str:
    if btc.source_integrity != "SOURCE VERIFIED" or eth.source_integrity != "SOURCE VERIFIED":
        return "UNVERIFIED"
    common = common_certified_intervals(btc, eth)
    if not common:
        return "UNUSABLE"
    if btc.research_certification == "VALID" and eth.research_certification == "VALID":
        return "VALID"
    return "VALID WITH DOCUMENTED EXCLUSIONS"
