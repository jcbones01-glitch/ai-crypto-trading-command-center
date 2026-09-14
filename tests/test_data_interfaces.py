from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from research_core.data_interfaces import MarketBar, validate_market_data


def valid_bar(timestamp: datetime) -> MarketBar:
    return MarketBar(timestamp, "BTC", Decimal("10"), Decimal("12"), Decimal("9"), Decimal("11"), Decimal("1"))


def test_market_bar_contract():
    bar = valid_bar(datetime(2026, 1, 1, tzinfo=timezone.utc))
    assert bar.close == Decimal("11")


def test_invalid_bars_rejected():
    ts = datetime(2026, 1, 1, tzinfo=timezone.utc)
    cases = [
        (ts.replace(tzinfo=None), "BTC", "10", "12", "9", "11", "1"),
        (ts, "", "10", "12", "9", "11", "1"),
        (ts, "BTC", "0", "12", "9", "11", "1"),
        (ts, "BTC", "13", "12", "9", "11", "1"),
        (ts, "BTC", "10", "12", "9", "13", "1"),
        (ts, "BTC", "10", "12", "9", "11", "-1"),
    ]
    for timestamp, symbol, op, hp, lp, cp, volume in cases:
        with pytest.raises(ValueError):
            MarketBar(timestamp, symbol, Decimal(op), Decimal(hp), Decimal(lp), Decimal(cp), Decimal(volume))


def test_market_data_requires_strictly_increasing_timestamps():
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        validate_market_data([valid_bar(t), valid_bar(t)])
    with pytest.raises(ValueError):
        validate_market_data([valid_bar(t + timedelta(hours=1)), valid_bar(t)])
