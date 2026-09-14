from pathlib import Path

from .data_ingestion import SUPPORTED_SYMBOLS, TIMEFRAME


def archive_member_symbol(name: str) -> str:
    filename = Path(name).name
    for symbol in SUPPORTED_SYMBOLS:
        if filename.startswith(f"{symbol}-{TIMEFRAME}-") and filename.endswith(".csv"):
            return symbol
    raise ValueError("unable to establish supported Binance symbol from archive member filename")
