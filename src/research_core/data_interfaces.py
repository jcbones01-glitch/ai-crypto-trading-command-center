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
        if self.high < max(self.open, self.close):
            raise ValueError("high must contain open and close")
        if self.low > min(self.open, self.close):
            raise ValueError("low must contain open and close")
        if self.high < self.low:
            raise ValueError("high cannot be below low")
        if self.volume < 0:
            raise ValueError("volume cannot be negative")


MarketData = list[MarketBar]
