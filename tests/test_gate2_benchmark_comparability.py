from datetime import datetime, timedelta, timezone
from decimal import Decimal

from tests.gate2_development_experiments import benchmark_parts


def test_benchmark_parts_use_exact_strategy_eligible_segments(monkeypatch):
    starts = [datetime(2020, 1, d, tzinfo=timezone.utc) for d in (1, 2, 3)]
    segments = [[type("Bar", (), {"timestamp": start + timedelta(hours=h)})() for h in range(3)] for start in starts]

    calls = []

    def fake_summarize(label, bars, target, segment_id):
        calls.append((label, segment_id, len(bars), target))
        return {"metrics": {"total_return": "0", "max_drawdown": "0", "trade_count": "0"}}

    monkeypatch.setattr("tests.gate2_development_experiments.summarize_segment", fake_summarize)
    result = benchmark_parts("buy_and_hold", segments, {0, 2})

    assert [part["metrics"]["total_return"] for part in result] == ["0", "0"]
    assert [call[1] for call in calls] == [0, 2]
    assert all(call[0] == "buy_and_hold" for call in calls)
    assert all(call[3] == [Decimal("1")] * 3 for call in calls)
