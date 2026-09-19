from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Iterable

from .event_schema import EventRecord


DEFAULT_PROTOCOL_VERSION = "event-dataset-v1"


def _utc_text(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_event(event: EventRecord) -> dict[str, object]:
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "region": event.region,
        "assets": list(event.assets),
        "event_time": _utc_text(event.event_time),
        "published_at": _utc_text(event.published_at),
        "first_market_available_at": _utc_text(event.first_market_available_at),
        "source_id": event.source_id,
        "source_version": event.source_version,
        "raw_event_hash": event.raw_event_hash,
        "classification_model": event.classification_model,
        "classification_prompt_version": event.classification_prompt_version,
        "classification_timestamp": _utc_text(event.classification_timestamp),
        "information_cutoff": _utc_text(event.information_cutoff),
    }


@dataclass(frozen=True)
class EventDatasetManifest:
    protocol_version: str
    dataset_id: str
    record_count: int
    first_market_available_at: datetime
    last_market_available_at: datetime
    source_ids: tuple[str, ...]


def build_event_dataset_manifest(
    events: Iterable[EventRecord],
    protocol_version: str = DEFAULT_PROTOCOL_VERSION,
) -> EventDatasetManifest:
    """Build a deterministic identity over canonical point-in-time records."""
    if not protocol_version or not protocol_version.strip():
        raise ValueError("protocol_version must be non-empty")

    records = tuple(events)
    if not records:
        raise ValueError("event dataset must contain at least one record")

    ids = [event.event_id for event in records]
    if len(set(ids)) != len(ids):
        raise ValueError("event dataset contains duplicate event_id values")

    ordered = tuple(sorted(records, key=lambda event: (event.first_market_available_at, event.event_id)))
    payload = {
        "protocol_version": protocol_version,
        "events": [_canonical_event(event) for event in ordered],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    dataset_id = sha256(canonical).hexdigest()

    return EventDatasetManifest(
        protocol_version=protocol_version,
        dataset_id=dataset_id,
        record_count=len(ordered),
        first_market_available_at=ordered[0].first_market_available_at,
        last_market_available_at=ordered[-1].first_market_available_at,
        source_ids=tuple(sorted({event.source_id for event in ordered})),
    )
