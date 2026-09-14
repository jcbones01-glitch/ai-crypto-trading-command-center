from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile


def binance_kline_row(timestamp: int, open_price: str = "100.0") -> str:
    return f"{timestamp},{open_price},105.0,99.0,103.0,12.5,0,1287.5,10,6.0,618.0,0\n"


def make_archive(symbol: str, timestamp: int, *, member_symbol: str | None = None) -> BytesIO:
    actual = member_symbol or symbol
    member = f"{actual}-1h-2021-01.csv"
    payload = binance_kline_row(timestamp).encode("utf-8")
    stream = BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
        archive.writestr(member, payload)
    stream.seek(0)
    return stream
