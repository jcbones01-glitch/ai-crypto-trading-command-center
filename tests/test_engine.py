from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from research_core.backtesting import BacktestConfig, run_backtest
from research_core.data_interfaces import MarketBar


def bars(prices: list[str]) -> list[MarketBar]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        MarketBar(start + timedelta(hours=i), "BTC", Decimal(p), Decimal(p), Decimal(p), Decimal(p), Decimal("1"))
        for i, p in enumerate(prices)
    ]


def free_config() -> BacktestConfig:
    return BacktestConfig(Decimal("1000"), Decimal("0"), Decimal("0"))


def test_enter_hold_exit_realized_profit():
    result = run_backtest(bars(["100", "110", "120"]), [Decimal("1"), Decimal("1"), Decimal("0")], free_config())
    assert result.trade_pnls == [Decimal("200")]
    assert result.realized_pnl == Decimal("200")
    assert result.unrealized_pnl == Decimal("0")


def test_realized_loss():
    result = run_backtest(bars(["100", "90", "80"]), [Decimal("1"), Decimal("1"), Decimal("0")], free_config())
    assert result.trade_pnls == [Decimal("-200")]


def test_partial_position_change_realizes_only_closed_quantity():
    result = run_backtest(bars(["100", "120", "140"]), [Decimal("1"), Decimal("0.5"), Decimal("0")], free_config())
    assert result.trade_pnls == [Decimal("100"), Decimal("200")]
    assert result.realized_pnl == Decimal("300")


def test_multiple_trades_are_separate_realized_outcomes():
    result = run_backtest(bars(["100", "110", "100", "90", "100"]), [Decimal("1"), Decimal("0"), Decimal("1"), Decimal("0"), Decimal("0")], free_config())
    assert result.trade_pnls == [Decimal("100"), Decimal("-110")]


def test_cost_only_round_trip_is_a_loss_from_fees():
    result = run_backtest(bars(["100", "100", "100"]), [Decimal("1"), Decimal("1"), Decimal("0")], BacktestConfig(Decimal("1000"), Decimal("0.001"), Decimal("0")))
    assert result.trade_pnls[0] < 0
    assert result.transaction_costs > 0
    assert result.realized_pnl == result.trade_pnls[0]


def test_zero_return_zero_cost_trade_is_zero():
    result = run_backtest(bars(["100", "100", "100"]), [Decimal("1"), Decimal("1"), Decimal("0")], free_config())
    assert result.trade_pnls == [Decimal("0")]


def test_transaction_costs_reduce_equity():
    free = run_backtest(bars(["100", "110", "110"]), [Decimal("1"), Decimal("1"), Decimal("0")], free_config())
    costly = run_backtest(bars(["100", "110", "110"]), [Decimal("1"), Decimal("1"), Decimal("0")], BacktestConfig(Decimal("1000"), Decimal("0.001"), Decimal("0")))
    assert costly.equity[-1] < free.equity[-1]


def test_slippage_reduces_round_trip_profit():
    no_slip = run_backtest(bars(["100", "110", "110"]), [Decimal("1"), Decimal("1"), Decimal("0")], free_config())
    slip = run_backtest(bars(["100", "110", "110"]), [Decimal("1"), Decimal("1"), Decimal("0")], BacktestConfig(Decimal("1000"), Decimal("0"), Decimal("0.001")))
    assert slip.equity[-1] < no_slip.equity[-1]


def test_empty_and_mismatched_inputs():
    assert run_backtest([], [], free_config()).equity == []
    with pytest.raises(ValueError):
        run_backtest(bars(["100"]), [], free_config())


def test_spot_position_bounds():
    with pytest.raises(ValueError):
        run_backtest(bars(["100"]), [Decimal("1.1")], free_config())
