from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class MarketBar:
    timestamp: datetime
    symbol: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        if not self.symbol.strip():
            raise ValueError("symbol cannot be empty")
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("OHLC prices must be positive")
        if not (self.low <= self.open <= self.high):
            raise ValueError("low <= open <= high is required")
        if not (self.low <= self.close <= self.high):
            raise ValueError("low <= close <= high is required")
        if self.volume < 0:
            raise ValueError("volume cannot be negative")


def validate_market_data(data: list[MarketBar]) -> None:
    """Require strictly increasing timestamps; duplicate timestamps are rejected."""
    for previous, current in zip(data, data[1:]):
        if current.timestamp <= previous.timestamp:
            raise ValueError("market data timestamps must be strictly increasing")


MarketData = list[MarketBar]
