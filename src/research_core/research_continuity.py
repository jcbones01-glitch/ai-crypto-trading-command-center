"""Generic research-continuity guards used by Gate 1A."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence, TypeVar

from .data_quality_treatment import CertifiedSegment, ContinuityBreak

DATA_BOUNDARY_TERMINATION = "DATA_BOUNDARY_TERMINATION"
T = TypeVar("T")


@dataclass(frozen=True)
class AlternativeSourceCandidate:
    """Documentation-only interface; never performs source replacement."""
    source_id: str
    independence_verified: bool
    provenance_verified: bool
    completeness_verified: bool
    accuracy_verified: bool
    comparability_verified: bool
    historical_integrity_verified: bool
    reproducibility_verified: bool
    approval_status: str = "REQUIRES SEPARATE APPROVAL"

    @property
    def eligible_for_replacement(self) -> bool:
        return False


def segment_series(timestamps: Sequence[datetime], values: Sequence[T], breaks: tuple[ContinuityBreak, ...]) -> tuple[tuple[tuple[datetime, T], ...], ...]:
    """Split a series at continuity breaks without filling or bridging gaps."""
    if len(timestamps) != len(values):
        raise ValueError("timestamps and values must have equal length")
    segments: list[list[tuple[datetime, T]]] = []
    current: list[tuple[datetime, T]] = []
    for timestamp, value in zip(timestamps, values):
        blocked = any(datetime.fromisoformat(br.start) <= timestamp < datetime.fromisoformat(br.end) for br in breaks)
        if blocked:
            if current:
                segments.append(current)
                current = []
            continue
        current.append((timestamp, value))
    if current:
        segments.append(current)
    return tuple(tuple(segment) for segment in segments)


def trade_boundary_termination(timestamp: datetime, breaks: tuple[ContinuityBreak, ...]) -> str | None:
    """Return the mandatory research termination reason at a continuity break."""
    if any(datetime.fromisoformat(br.start) <= timestamp < datetime.fromisoformat(br.end) for br in breaks):
        return DATA_BOUNDARY_TERMINATION
    return None


def certified_segment_contains(segment: CertifiedSegment, timestamp: datetime) -> bool:
    start = datetime.fromisoformat(segment.start)
    end = datetime.fromisoformat(segment.end)
    return start <= timestamp < end
