from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from research_core.backtesting import BacktestConfig, run_backtest
from research_core.data_interfaces import MarketBar


def bars(count: int) -> list[MarketBar]:
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return [
        MarketBar(
            start + timedelta(hours=i),
            "BTC/USDT",
            Decimal("100"),
            Decimal("101"),
            Decimal("99"),
            Decimal("100"),
            Decimal("1"),
        )
        for i in range(count)
    ]


def config(delay: int) -> BacktestConfig:
    return BacktestConfig(
        initial_capital=Decimal("1000"),
        commission_rate=Decimal("0"),
        slippage_rate=Decimal("0"),
        execution_delay_bars=delay,
    )


def test_one_and_two_bar_delays_are_supported():
    assert config(1).execution_delay_bars == 1
    assert config(2).execution_delay_bars == 2


@pytest.mark.parametrize("delay", [0, -1, 3, 10])
def test_unsupported_delays_are_rejected(delay: int):
    with pytest.raises(ValueError, match="must be 1 or 2"):
        config(delay)


def test_two_bar_delay_does_not_execute_on_first_or_second_bar():
    market = bars(4)
    targets = [Decimal("1"), Decimal("0"), Decimal("0"), Decimal("0")]
    result = run_backtest(market, targets, config(2))

    # Signal on bar 0 executes on bar 2 OPEN. With flat prices and zero costs,
    # equity is unchanged, but exposure proves when the position appeared.
    assert result.positions[0] == Decimal("0")
    assert result.positions[1] == Decimal("0")
    assert result.positions[2] == Decimal("1")
    assert result.positions[3] == Decimal("0")


def test_one_bar_delay_executes_on_next_bar_open():
    market = bars(3)
    targets = [Decimal("1"), Decimal("0"), Decimal("0")]
    result = run_backtest(market, targets, config(1))

    assert result.positions[0] == Decimal("0")
    assert result.positions[1] == Decimal("1")
    assert result.positions[2] == Decimal("0")
