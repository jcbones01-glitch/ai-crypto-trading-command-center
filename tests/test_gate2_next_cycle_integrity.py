from datetime import datetime, timedelta, timezone
from decimal import Decimal

from research_core.data_interfaces import MarketBar
from tests.gate2_next_cycle_experiments import (
    BASE,
    concentration_and_dd,
    event_condition,
    median_previous,
    parameter_cells,
    simulate_events,
)


def bar(ts, close, volume=100):
    value = Decimal(str(close))
    return MarketBar(ts, "ETH/USDT", value, value, value, value, Decimal(str(volume)))


def test_registered_parameter_cells_total_45():
    assert len(parameter_cells("HYP-0005")) == 18
    assert len(parameter_cells("HYP-0006")) == 9
    assert len(parameter_cells("HYP-0007")) == 18


def test_worst_segment_return_is_actual_minimum_for_all_positive_segments():
    details = [
        {"segment": 0, "aggregate": {"events": 1, "compound_return": "0.10"}, "events": [{"return": "0.10"}], "error": None},
        {"segment": 1, "aggregate": {"events": 1, "compound_return": "0.20"}, "events": [{"return": "0.20"}], "error": None},
    ]
    result = concentration_and_dd(details)
    assert Decimal(result["worst_segment_return"]) == Decimal("0.10")


def test_volume_baseline_uses_only_previous_completed_bars():
    values = [Decimal("100"), Decimal("100"), Decimal("100"), Decimal("1000")]
    assert median_previous(values, 3, 3) == Decimal("100")


def test_hyp0006_requires_exact_timestamp_alignment_at_signal_bar():
    ts = datetime(2021, 1, 1, tzinfo=timezone.utc)
    eth = [bar(ts, 100), bar(ts + timedelta(hours=1), 101)]
    btc = [bar(ts, 100), bar(ts + timedelta(hours=1, minutes=1), 103)]
    params = BASE["HYP-0006"]
    try:
        event_condition("HYP-0006", 1, eth, params, btc)
    except ValueError as exc:
        assert "timestamp synchronization" in str(exc)
    else:
        raise AssertionError("HYP-0006 accepted non-synchronized timestamps")


def test_delay_one_and_two_use_future_bar_opens_without_overlap():
    ts = datetime(2021, 1, 1, tzinfo=timezone.utc)
    bars = [
        bar(ts + timedelta(hours=0), 100, 100),
        bar(ts + timedelta(hours=1), 101, 100),
        bar(ts + timedelta(hours=2), 102, 100),
        bar(ts + timedelta(hours=3), 103, 100),
        bar(ts + timedelta(hours=4), 104, 100),
    ]
    params = {"volume_lookback": 1, "shock": Decimal("1"), "return_threshold": Decimal("0.005")}
    result_1 = simulate_events(bars, "HYP-0005", params, Decimal("0"), Decimal("0"), 1)
    result_2 = simulate_events(bars, "HYP-0005", params, Decimal("0"), Decimal("0"), 2)
    assert result_1["events"][0]["signal_index"] == 1
    assert result_1["events"][0]["entry_index"] == 2
    assert result_1["events"][0]["exit_index"] == 2
    assert result_2["events"][0]["signal_index"] == 1
    assert result_2["events"][0]["entry_index"] == 3
    assert result_2["events"][0]["exit_index"] == 3
