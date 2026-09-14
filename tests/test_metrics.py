from decimal import Decimal

from research_core.metrics import calculate_metrics


def test_basic_metrics() -> None:
    result = calculate_metrics(
        [Decimal("100"), Decimal("110"), Decimal("99")],
        [Decimal("10"), Decimal("-5")],
    )
    assert result.total_return == Decimal("-0.01")
    assert result.trade_count == 2
    assert result.win_rate == Decimal("0.5")
    assert result.max_drawdown == Decimal("0.1")
    assert result.consecutive_losses == 1
