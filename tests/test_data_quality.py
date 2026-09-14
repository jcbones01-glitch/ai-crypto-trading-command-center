from __future__ import annotations

import io
import zipfile

from research_core.data_quality import certify, scan_archive


def _archive(tmp_path, rows):
    path = tmp_path / "BTCUSDT-1h-2018-02.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("BTCUSDT-1h-2018-02.csv", "".join(",".join(row) + "\n" for row in rows))
    return path


def _row(timestamp, open_price="10", high="11", low="9", close="10", volume="1"):
    return [timestamp, open_price, high, low, close, volume]


def test_non_aligned_timestamp_is_explicit_and_not_repaired(tmp_path):
    report = scan_archive(_archive(tmp_path, [
        _row("1518048000000"), _row("1518168494789"), _row("1518319694789")
    ]), "BTCUSDT")
    events = [event for event in report.events if event.anomaly_type == "NON_ALIGNED_TIMESTAMP"]
    assert len(events) == 2
    assert events[0].raw_timestamp == "1518168494789"
    assert events[0].parsed_timestamp == "2018-02-09T09:28:14.789000+00:00"
    assert events[0].source_provenance == "Binance Public Data issue #77"
    assert report.rows_processed == 3
    assert certify([report]) == "VALID WITH DOCUMENTED SOURCE ANOMALIES"


def test_invalid_ohlc_is_visible_and_rows_are_not_deleted(tmp_path):
    report = scan_archive(_archive(tmp_path, [
        _row("1518048000000"), _row("1518051600000", open_price="12", high="11")
    ]), "BTCUSDT")
    assert report.rows_processed == 2
    assert any(event.anomaly_type == "INVALID_OHLC" for event in report.events)


def test_missing_interval_is_explicit(tmp_path):
    report = scan_archive(_archive(tmp_path, [
        _row("1518048000000"), _row("1518062400000")
    ]), "BTCUSDT")
    missing = [event for event in report.events if event.anomaly_type == "MISSING_INTERVAL"]
    assert [event.parsed_timestamp for event in missing] == [
        "2018-02-08T01:00:00+00:00", "2018-02-08T02:00:00+00:00", "2018-02-08T03:00:00+00:00"
    ]
    assert all(event.source_provenance == "Binance Public Data issue #77" for event in missing)
