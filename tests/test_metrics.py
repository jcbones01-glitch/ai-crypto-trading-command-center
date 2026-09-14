from decimal import Decimal

import pytest

from research_core.metrics import calculate_metrics


def test_trade_metrics_use_realized_pnls_and_calculate_exposure():
    metrics = calculate_metrics(
        [Decimal("100"), Decimal("110"), Decimal("99")],
        [Decimal("10"), Decimal("-5")],
        [Decimal("1"), Decimal("1"), Decimal("0")],
    )
    assert metrics.total_return == Decimal("-0.01")
    assert metrics.trade_count == 2
    assert metrics.win_rate == Decimal("0.5")
    assert metrics.average_win == Decimal("10")
    assert metrics.average_loss == Decimal("-5")
    assert metrics.expectancy == Decimal("2.5")
    assert metrics.profit_factor == Decimal("2")
    assert metrics.max_drawdown == Decimal("0.1")
    assert metrics.exposure == Decimal(2) / Decimal(3)
    assert metrics.recovery_periods is None


def test_all_wins_and_all_losses():
    all_wins = calculate_metrics([Decimal("100"), Decimal("101")], [Decimal("1"), Decimal("2")])
    all_losses = calculate_metrics([Decimal("100"), Decimal("99")], [Decimal("-1"), Decimal("-2")])
    assert all_wins.profit_factor is None
    assert all_losses.profit_factor == Decimal("0")


def test_zero_volatility_and_no_downside():
    flat = calculate_metrics([Decimal("100"), Decimal("100"), Decimal("100")], [])
    rising = calculate_metrics([Decimal("100"), Decimal("101"), Decimal("102")], [])
    assert flat.sharpe is None and flat.sortino is None
    assert rising.sharpe is not None and rising.sortino is None


def test_recovery_period_is_calculated():
    recovered = calculate_metrics([Decimal("100"), Decimal("90"), Decimal("100")], [])
    unrecovered = calculate_metrics([Decimal("100"), Decimal("90"), Decimal("95")], [])
    assert recovered.recovery_periods == 1
    assert unrecovered.recovery_periods is None


def test_invalid_metric_inputs_are_rejected():
    with pytest.raises(ValueError): calculate_metrics([], [])
    with pytest.raises(ValueError): calculate_metrics([Decimal("100")], [], periods_per_year=0)
    with pytest.raises(ValueError): calculate_metrics([Decimal("100"), Decimal("101")], [], [Decimal("1")])
    with pytest.raises(ValueError): calculate_metrics([Decimal("100"), Decimal("101")], [], [Decimal("1.1"), Decimal("0")])


def test_extreme_decimal_values_remain_decimal():
    metrics = calculate_metrics([Decimal("1E+20"), Decimal("1.0000000001E+20")], [Decimal("1E+10")])
    # There is exactly one return observation. Its variance is zero, so
    # Sharpe is mathematically undefined. There are no negative returns,
    # so Sortino is also undefined. Defined numeric metrics remain Decimal.
    assert isinstance(metrics.total_return, Decimal)
    assert metrics.sharpe is None
    assert metrics.sortino is None
    assert isinstance(metrics.win_rate, Decimal)
    assert isinstance(metrics.average_win, Decimal)
    assert isinstance(metrics.average_loss, Decimal)
    assert isinstance(metrics.expectancy, Decimal)
    assert isinstance(metrics.max_drawdown, Decimal)
    assert isinstance(metrics.exposure, Decimal)
