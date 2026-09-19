from __future__ import annotations

from datetime import datetime
from typing import Iterable

from .event_schema import EventRecord


def _require_aware(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")


def events_available_as_of(
    events: Iterable[EventRecord],
    as_of: datetime,
) -> tuple[EventRecord, ...]:
    """Return only events that were market-available by `as_of`.

    Output ordering is deterministic by availability time then event id.
    """
    _require_aware(as_of)
    available = [event for event in events if event.first_market_available_at <= as_of]
    return tuple(sorted(available, key=lambda event: (event.first_market_available_at, event.event_id)))
