from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

import research.scripts.run_fomc_event_study_v1 as mod


UTC = timezone.utc
T0 = datetime(2020, 1, 1, 12, 0, tzinfo=UTC)


def bar(timestamp, open_price):
    return SimpleNamespace(timestamp=timestamp, open=Decimal(str(open_price)))


def test_frozen_study_dimensions_are_exact():
    assert mod.HORIZONS_HOURS == (1, 6, 24)
    assert mod.CONTROL_LAGS_DAYS == (7, 14, 21, 28)
    assert mod.ASSETS == ("BTCUSDT", "ETHUSDT")
    assert mod.EXPECTED_FOMC_EVENT_COUNT == 37
    assert mod.EXPECTED_FOMC_DATASET_ID == "fd5021aa2ff2f01ceaa2f5e060d08db8e0825cc27e1bde147e8eb5948ee14e11"


def test_forward_open_return_uses_exact_open_to_open_horizon():
    segment = [bar(T0 + timedelta(hours=i), 100 + i) for i in range(25)]
    lookup = mod.build_segment_lookup([segment])
    eligible, reason, value = mod.forward_open_return(lookup, T0, 6)
    assert eligible is True
    assert reason is None
    assert value == Decimal("106") / Decimal("100") - Decimal("1")


def test_forward_open_return_rejects_continuity_break():
    first = [bar(T0 + timedelta(hours=i), 100 + i) for i in range(3)]
    second = [bar(T0 + timedelta(hours=i), 100 + i) for i in range(3, 8)]
    lookup = mod.build_segment_lookup([first, second])
    eligible, reason, value = mod.forward_open_return(lookup, T0, 6)
    assert eligible is False
    assert "continuity break" in reason
    assert value is None


def test_control_timestamps_are_prior_same_weekday_and_hour():
    for lag in mod.CONTROL_LAGS_DAYS:
        control = mod.control_timestamp(T0, lag)
        assert control < T0
        assert control.hour == T0.hour
        assert control.weekday() == T0.weekday()


def test_control_near_event_rule_is_inclusive_at_24_hours():
    events = (T0,)
    assert mod.is_near_fomc_event(T0 - timedelta(hours=24), events) is True
    assert mod.is_near_fomc_event(T0 + timedelta(hours=24), events) is True
    assert mod.is_near_fomc_event(T0 - timedelta(hours=25), events) is False


def test_summary_metrics_are_deterministic():
    values = [Decimal("-0.02"), Decimal("0.01"), Decimal("0.03")]
    summary = mod.summarize_returns(values)
    assert summary["eligible_observations"] == 3
    assert Decimal(summary["mean_signed_return"]) == Decimal("0.02") / Decimal("3")
    assert Decimal(summary["median_signed_return"]) == Decimal("0.01")
    assert Decimal(summary["positive_return_fraction"]) == Decimal("2") / Decimal("3")
    assert Decimal(summary["mean_absolute_return"]) == Decimal("0.06") / Decimal("3")
    assert Decimal(summary["median_absolute_return"]) == Decimal("0.02")


def test_unregistered_horizon_and_control_lag_are_rejected():
    with pytest.raises(ValueError, match="unregistered horizon"):
        mod.forward_open_return({}, T0, 12)
    with pytest.raises(ValueError, match="unregistered control lag"):
        mod.control_timestamp(T0, 35)


def test_frozen_manifest_is_development_only_and_complete():
    payload, events = mod.load_frozen_events()
    assert payload["validation_or_oos_accessed"] is False
    assert len(events) == 37
    assert len({event["event_id"] for event in events}) == 37
    assert all(mod.START <= event["timestamp"] < mod.END for event in events)
    assert all(
        event["timestamp"].minute == event["timestamp"].second == event["timestamp"].microsecond == 0
        for event in events
    )
