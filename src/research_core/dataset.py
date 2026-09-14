"""Dataset-level Gate 1 helpers and pre-registered research partitions."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .data_ingestion import PARTITIONS, RESEARCH_END, RESEARCH_START


@dataclass(frozen=True)
class ResearchPartition:
    name: str
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        if self.start.tzinfo is None or self.end.tzinfo is None:
            raise ValueError("partition timestamps must be timezone-aware")
        if self.start.utcoffset() != timezone.utc.utcoffset(self.start) or self.end.utcoffset() != timezone.utc.utcoffset(self.end):
            raise ValueError("partition timestamps must be UTC")
        if self.start >= self.end:
            raise ValueError("partition start must precede end")


RESEARCH_PARTITIONS = tuple(ResearchPartition(name, start, end) for name, (start, end) in PARTITIONS.items())


def validate_partitions(partitions: tuple[ResearchPartition, ...] = RESEARCH_PARTITIONS) -> None:
    ordered = sorted(partitions, key=lambda item: item.start)
    if not ordered or ordered[0].start != RESEARCH_START or ordered[-1].end != RESEARCH_END:
        raise ValueError("partitions must cover the registered research window")
    for previous, current in zip(ordered, ordered[1:]):
        if previous.end != current.start:
            raise ValueError("partitions must be continuous and non-overlapping")


def first_common_valid_timestamp(btc_start: datetime | None, eth_start: datetime | None) -> datetime:
    """Return the common start without making asset-specific period choices."""
    if btc_start is None or eth_start is None:
        raise ValueError("both asset starts must be objectively verified")
    start = max(btc_start, eth_start)
    if start < RESEARCH_START:
        start = RESEARCH_START
    if start >= RESEARCH_END:
        raise ValueError("no common timestamp exists inside the registered research window")
    return start
