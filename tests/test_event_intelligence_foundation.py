from datetime import datetime, timedelta, timezone

import pytest

from intelligence import EventRecord, events_available_as_of, hash_raw_payload


UTC = timezone.utc
T0 = datetime(2020, 1, 1, 12, 0, tzinfo=UTC)


def make_event(
    event_id: str = "evt-1",
    *,
    published_at: datetime = T0,
    available_at: datetime = T0,
    event_time: datetime = T0,
) -> EventRecord:
    return EventRecord(
        event_id=event_id,
        event_type="macro_release",
        region="US",
        assets=("BTCUSDT", "ETHUSDT"),
        event_time=event_time,
        published_at=published_at,
        first_market_available_at=available_at,
        source_id="fixture-source",
        source_version="v1",
        raw_event_hash=hash_raw_payload(event_id.encode("utf-8")),
    )


def test_raw_payload_hash_is_deterministic_and_content_sensitive():
    assert hash_raw_payload(b"abc") == hash_raw_payload(b"abc")
    assert hash_raw_payload(b"abc") != hash_raw_payload(b"abd")
    assert len(hash_raw_payload(b"abc")) == 64


def test_event_rejects_naive_timestamps():
    with pytest.raises(ValueError, match="event_time must be timezone-aware"):
        make_event(event_time=datetime(2020, 1, 1, 12, 0))


def test_market_availability_cannot_precede_publication():
    with pytest.raises(ValueError, match="cannot precede published_at"):
        make_event(
            published_at=T0,
            available_at=T0 - timedelta(seconds=1),
        )


def test_point_in_time_filter_excludes_future_information():
    early = make_event("early", published_at=T0, available_at=T0)
    future = make_event(
        "future",
        published_at=T0 + timedelta(hours=2),
        available_at=T0 + timedelta(hours=2),
        event_time=T0 + timedelta(hours=2),
    )

    visible = events_available_as_of((future, early), T0 + timedelta(hours=1))
    assert visible == (early,)


def test_point_in_time_output_order_is_deterministic():
    later_id = make_event("z-event")
    earlier_id = make_event("a-event")
    assert events_available_as_of((later_id, earlier_id), T0) == (earlier_id, later_id)


def test_classification_metadata_is_all_or_none():
    with pytest.raises(ValueError, match="all-or-none"):
        EventRecord(
            event_id="evt",
            event_type="regulatory",
            region="US",
            assets=("BTCUSDT",),
            event_time=T0,
            published_at=T0,
            first_market_available_at=T0,
            source_id="fixture-source",
            source_version="v1",
            raw_event_hash=hash_raw_payload(b"evt"),
            classification_model="model-v1",
        )


def test_classification_information_cutoff_cannot_precede_availability():
    with pytest.raises(ValueError, match="information_cutoff cannot precede"):
        EventRecord(
            event_id="evt",
            event_type="regulatory",
            region="US",
            assets=("BTCUSDT",),
            event_time=T0,
            published_at=T0,
            first_market_available_at=T0,
            source_id="fixture-source",
            source_version="v1",
            raw_event_hash=hash_raw_payload(b"evt"),
            classification_model="model-v1",
            classification_prompt_version="prompt-v1",
            classification_timestamp=T0 + timedelta(days=1),
            information_cutoff=T0 - timedelta(seconds=1),
        )
