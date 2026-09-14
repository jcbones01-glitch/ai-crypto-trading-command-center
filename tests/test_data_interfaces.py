from datetime import datetime, timezone
from decimal import Decimal

import pytest

from research_core.data_interfaces import MarketBar


def test_market_bar_contract() -> None:
    bar = MarketBar(datetime(2026, 1, 1, tzinfo=timezone.utc), "BTC", Decimal("100"), Decimal("110"), Decimal("90"), Decimal("105"), Decimal("1000"))
    assert bar.close == Decimal("105")


def test_invalid_bar_rejected() -> None:
    with pytest.raises(ValueError):
        MarketBar(datetime(2026, 1, 1, tzinfo=timezone.utc), "BTC", Decimal("100"), Decimal("99"), Decimal("80"), Decimal("85"), Decimal("100"))
