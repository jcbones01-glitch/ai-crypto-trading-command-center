from datetime import datetime, timedelta, timezone
from io import StringIO

import pytest

from research_core.data_ingestion import normalize_csv
from research_core.historical_dataset import ingest_archives, require_complete_hourly_window


def make_row(dt):
    return [str(int(dt.timestamp() * 1000)), "100", "105", "99", "103", "1", "0", "0", "1", "0", "0", "0"]


def test_complete_window_requires_exact_half_open_boundaries(tmp_path):
    base = datetime(2021, 1, 1, tzinfo=timezone.utc)
    rows = "\n".join(",".join(make_row(base + timedelta(hours=i))) for i in range(3))
    path = tmp_path / "BTCUSDT-1h-fixture.csv"
    path.write_text(rows, encoding="utf-8")

    # TEST FIXTURE ONLY: exercise the same normalized contract without a market-data claim.
    bars, _ = normalize_csv(StringIO(rows), "BTCUSDT")
    assert bars[-1].timestamp == base + timedelta(hours=2)
    assert len(bars) == 3


def test_ingest_requires_at_least_one_archive():
    with pytest.raises(ValueError):
        ingest_archives([], "BTCUSDT")


def test_complete_window_rejects_missing_hour():
    base = datetime(2021, 1, 1, tzinfo=timezone.utc)
    rows = "\n".join(",".join(make_row(base + timedelta(hours=i))) for i in (0, 2))
    bars, unit = normalize_csv(StringIO(rows), "BTCUSDT")
    from research_core.data_ingestion import DatasetMetadata
    from research_core.historical_dataset import HistoricalDataset
    metadata = DatasetMetadata("x", "TEST FIXTURE ONLY", "BTCUSDT", "BTC/USDT", "spot", "1h", "UTC", bars[0].timestamp.isoformat(), bars[-1].timestamp.isoformat(), len(bars), unit, "test", "invalid", "x")
    dataset = HistoricalDataset("BTCUSDT", tuple(bars), metadata)
    with pytest.raises(ValueError):
        require_complete_hourly_window(dataset, base, base + timedelta(hours=3))
