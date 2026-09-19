from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

import tests.gate2_cycle7_experiments as mod


def bar(i, open_="100", high="101", low="99", close="100", volume="1"):
    return SimpleNamespace(
        timestamp=datetime(2020, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i),
        open=Decimal(open_),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume=Decimal(volume),
    )


def test_registered_cycle7_cell_count_is_exact():
    assert sum(len(mod.cartesian(g)) for g in mod.GRID.values()) == 28


def test_multi_hour_hold_uses_future_close_and_nonoverlap(monkeypatch):
    bars = [bar(i, close=str(100 + i)) for i in range(20)]
    monkeypatch.setattr(mod, "condition", lambda *args, **kwargs: True)
    params = {"hold_bars": 3}
    events = mod.simulate(bars, "HYP-X", params, Decimal("0"), Decimal("0"), 1)
    assert events[0]["entry_index"] == 2
    assert events[0]["exit_index"] == 4
    assert events[1]["signal_index"] == 5
    assert events[1]["entry_index"] == 6
    assert events[1]["exit_index"] == 8
    assert all(e["exit_index"] - e["entry_index"] + 1 == 3 for e in events)


def test_zero_delay_is_rejected():
    with pytest.raises(ValueError):
        mod.simulate([bar(i) for i in range(10)], "HYP-X", {"hold_bars": 2}, Decimal("0"), Decimal("0"), 0)


def test_bullish_harami_condition():
    bars = [
        bar(0, open_="110", high="112", low="98", close="100"),
        bar(1, open_="102", high="109", low="101", close="108"),
    ]
    params = {
        "parent_body_ratio": Decimal("0.50"),
        "close_location": Decimal("0.75"),
        "hold_bars": 12,
    }
    assert mod.condition("HYP-0025", 1, bars, params) is True


def test_compression_rank_is_causal_to_signal_time():
    bars = []
    for i in range(800):
        base = Decimal("100") + Decimal(i) / Decimal("100")
        bars.append(
            SimpleNamespace(
                timestamp=datetime(2020, 1, 1, tzinfo=timezone.utc) + timedelta(hours=i),
                open=base,
                high=base + Decimal("1"),
                low=base - Decimal("1"),
                close=base,
                volume=Decimal("1"),
            )
        )
    signal_i = 760
    before = mod.compression_rank(bars, signal_i)
    bars[799] = SimpleNamespace(
        timestamp=bars[799].timestamp,
        open=Decimal("1000"),
        high=Decimal("2000"),
        low=Decimal("1"),
        close=Decimal("1500"),
        volume=Decimal("999"),
    )
    after = mod.compression_rank(bars, signal_i)
    assert before == after
