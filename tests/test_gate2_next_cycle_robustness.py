from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from decimal import Decimal

import tests.gate2_next_cycle_experiments as mod


def test_compound_return_is_multiplicative():
    assert mod.compound_return([Decimal("0.10"), Decimal("-0.10")]) == Decimal("-0.01")


def test_regime_uses_only_168_hour_trailing_return():
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    bars = []
    for i in range(169):
        close = Decimal("100") if i < 168 else Decimal("111")
        bars.append(SimpleNamespace(timestamp=start + timedelta(hours=i), close=close))
    assert mod.regime_for_signal(bars, 167) is None
    assert mod.regime_for_signal(bars, 168) == "bull"


def test_leave_one_out_excludes_exactly_one_segment(monkeypatch):
    calls = []

    def fake_sim(seg, hyp, params, fee, slip, delay, btc=None):
        calls.append(seg)
        return {"returns": [Decimal("0.10")], "events": [{"return": "0.10"}]}

    monkeypatch.setattr(mod, "simulate_events", fake_sim)
    result = mod.leave_one_out(["a", "b", "c"], "HYP-0005", {}, Decimal("0"), Decimal("0"), 1)
    assert len(result["variants"]) == 3
    assert all(v["events"] == 2 for v in result["variants"])
    assert all(v["above_cash"] for v in result["variants"])


def test_concentration_fails_when_top_positive_events_exceed_half(monkeypatch):
    def fake_sim(seg, hyp, params, fee, slip, delay, btc=None):
        value = {"a": "0.10", "b": "0.01"}[seg]
        return {"returns": [Decimal(value)], "events": [{"return": value}]}

    monkeypatch.setattr(mod, "simulate_events", fake_sim)
    result = mod.concentration_metrics(["a", "b"], "HYP-0005", {}, Decimal("0"), Decimal("0"), 1)
    assert Decimal(result["top_10_positive_event_pnl_fraction"]) > Decimal("0.50")
    assert result["pass"] is False
