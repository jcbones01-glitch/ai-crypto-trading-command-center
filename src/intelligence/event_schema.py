from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from typing import Iterable


def _require_aware(value: datetime, field_name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _require_text(value: str, field_name: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must be non-empty")


def hash_raw_payload(payload: bytes) -> str:
    """Return the deterministic SHA-256 hash of an exact raw source payload."""
    if not isinstance(payload, bytes):
        raise TypeError("payload must be bytes")
    return sha256(payload).hexdigest()


@dataclass(frozen=True)
class EventRecord:
    """Immutable point-in-time event record.

    `first_market_available_at` controls historical research availability.
    Classification metadata describes a reproducible later transformation; it
    never changes the event's historical availability.
    """

    event_id: str
    event_type: str
    region: str
    assets: tuple[str, ...]
    event_time: datetime
    published_at: datetime
    first_market_available_at: datetime
    source_id: str
    source_version: str
    raw_event_hash: str
    classification_model: str | None = None
    classification_prompt_version: str | None = None
    classification_timestamp: datetime | None = None
    information_cutoff: datetime | None = None

    def __post_init__(self) -> None:
        for value, field_name in (
            (self.event_id, "event_id"),
            (self.event_type, "event_type"),
            (self.region, "region"),
            (self.source_id, "source_id"),
            (self.source_version, "source_version"),
        ):
            _require_text(value, field_name)

        if not self.assets:
            raise ValueError("assets must contain at least one asset")
        if any(not asset or not asset.strip() for asset in self.assets):
            raise ValueError("assets must contain only non-empty values")
        if len(set(self.assets)) != len(self.assets):
            raise ValueError("assets must not contain duplicates")

        for value, field_name in (
            (self.event_time, "event_time"),
            (self.published_at, "published_at"),
            (self.first_market_available_at, "first_market_available_at"),
        ):
            _require_aware(value, field_name)

        if self.first_market_available_at < self.published_at:
            raise ValueError("first_market_available_at cannot precede published_at")

        if len(self.raw_event_hash) != 64:
            raise ValueError("raw_event_hash must be a 64-character SHA-256 hex digest")
        try:
            int(self.raw_event_hash, 16)
        except ValueError as exc:
            raise ValueError("raw_event_hash must be hexadecimal") from exc

        classification_values: Iterable[object | None] = (
            self.classification_model,
            self.classification_prompt_version,
            self.classification_timestamp,
            self.information_cutoff,
        )
        present = [value is not None for value in classification_values]
        if any(present) and not all(present):
            raise ValueError("classification metadata must be provided all-or-none")

        if all(present):
            assert self.classification_model is not None
            assert self.classification_prompt_version is not None
            assert self.classification_timestamp is not None
            assert self.information_cutoff is not None
            _require_text(self.classification_model, "classification_model")
            _require_text(self.classification_prompt_version, "classification_prompt_version")
            _require_aware(self.classification_timestamp, "classification_timestamp")
            _require_aware(self.information_cutoff, "information_cutoff")
            if self.information_cutoff < self.first_market_available_at:
                raise ValueError("information_cutoff cannot precede first_market_available_at")
