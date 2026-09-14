from datetime import datetime, timedelta, timezone
from decimal import Decimal

from research_core.backtesting import BacktestConfig, run_backtest
from research_core.data_interfaces import MarketBar


def test_deterministic_costed_simulation() -> None:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    bars = [
        MarketBar(start + timedelta(hours=i), "BTC", Decimal(p), Decimal(p), Decimal(p), Decimal(p), Decimal("1"))
        for i, p in enumerate(["100", "110", "121"])
    ]
    result = run_backtest(
        bars,
        [Decimal("1"), Decimal("1"), Decimal("1")],
        BacktestConfig(Decimal("1000"), Decimal("0.001"), Decimal("0.001")),
    )
    assert result.equity == [Decimal("1000"), Decimal("1097.8000"), Decimal("1207.58000")]
