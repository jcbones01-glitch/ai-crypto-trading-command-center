"""Fixed settings for the paper-trading learning system.

Changing anything here is a strategy change and needs owner approval
(record it in knowledge/06_decisions_log.md).
"""
from __future__ import annotations

# Faber (2007) five-asset basket: US stocks, foreign stocks, US bonds,
# real estate, commodities.  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=962461
UNIVERSE: tuple[str, ...] = ("SPY", "EFA", "IEF", "VNQ", "DBC")
BENCHMARK = "SPY"
LOOKBACK_MONTHS = 10
MIN_TRADE_DOLLARS = 50.0

# First day of paper trading (first orders placed 2026-09-28).  The monthly
# report measures the account and buy-and-hold SPY from this date's close.
TRACKING_START = "2026-09-28"

# Safety locks.  Only the Alpaca PAPER trading endpoint is allowed.
PAPER_TRADING_BASE_URL = "https://paper-api.alpaca.markets"
MARKET_DATA_BASE_URL = "https://data.alpaca.markets"
KEY_ENV = "ALPACA_PAPER_KEY_ID"
SECRET_ENV = "ALPACA_PAPER_SECRET_KEY"
