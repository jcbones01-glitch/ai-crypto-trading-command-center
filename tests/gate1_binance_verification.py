from __future__ import annotations

import hashlib
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from research_core.data_ingestion import RESEARCH_END, RESEARCH_START, archive_url, checksum_url, verify_sha256_bytes
from research_core.historical_dataset import ingest_archives


def months(start: datetime, end: datetime):
    year, month = start.year, start.month
    while (year, month) < (end.year, end.month):
        yield year, month
        month += 1
        if month == 13:
            year, month = year + 1, 1


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def verify_symbol(symbol: str, root: Path) -> None:
    paths: list[Path] = []
    checksum_records: list[str] = []
    for year, month in months(RESEARCH_START, RESEARCH_END):
        url = archive_url(symbol, year, month)
        payload = fetch(url)
        checksum_text = fetch(checksum_url(url)).decode("utf-8")
        if not verify_sha256_bytes(payload, checksum_text):
            raise AssertionError(f"checksum mismatch: {symbol} {year:04d}-{month:02d}")
        digest = hashlib.sha256(payload).hexdigest()
        path = root / Path(url).name
        path.write_bytes(payload)
        paths.append(path)
        checksum_records.append(f"{path.name}:{digest}")
    dataset = ingest_archives(paths, symbol, expected_start=RESEARCH_START, expected_end=RESEARCH_END)
    expected_identity = hashlib.sha256(("\n".join(checksum_records) + "\n").encode()).hexdigest()
    assert dataset.metadata.source_identity == expected_identity
    assert dataset.metadata.row_count == len(dataset.bars)
    assert dataset.metadata.validation_status == "validated"
    print(f"{symbol}: start={dataset.metadata.start_timestamp} end={dataset.metadata.end_timestamp} rows={dataset.metadata.row_count} precision={dataset.metadata.timestamp_unit} content_hash={dataset.metadata.content_hash} dataset_id={dataset.metadata.dataset_id}")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="gate1-binance-") as directory:
        root = Path(directory)
        verify_symbol("BTCUSDT", root / "BTCUSDT")
        verify_symbol("ETHUSDT", root / "ETHUSDT")
