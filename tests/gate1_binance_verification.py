from __future__ import annotations

import tempfile
import urllib.request
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from research_core.data_ingestion import RESEARCH_END, RESEARCH_START, archive_url, checksum_url, verify_sha256_bytes
from research_core.data_quality import ArchiveQualityReport, DataQualityEvent, certify, scan_archive
from research_core.dataset import validate_partitions


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


def _checksum_event(symbol: str, archive: str, message: str) -> DataQualityEvent:
    return DataQualityEvent(symbol, "1h", archive, None, None, None, None,
                            "CHECKSUM_FAILURE", "archive SHA-256 must match Binance CHECKSUM",
                            "ERROR", "Binance Public Data archive", message)


def verify_symbol(symbol: str, root: Path) -> tuple[list[ArchiveQualityReport], int]:
    reports: list[ArchiveQualityReport] = []
    rows = 0
    for year, month in months(RESEARCH_START, RESEARCH_END):
        url = archive_url(symbol, year, month)
        archive_name = Path(url).name
        try:
            payload = fetch(url)
            checksum_text = fetch(checksum_url(url)).decode("utf-8")
            if not verify_sha256_bytes(payload, checksum_text):
                reports.append(ArchiveQualityReport(symbol, archive_name, 0, (_checksum_event(symbol, archive_name, "Binance archive SHA-256 checksum mismatch"),), False))
                continue
            path = root / archive_name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            report = scan_archive(path, symbol, checksum_verified=True)
            reports.append(report)
            rows += report.rows_processed
        except Exception as exc:
            reports.append(ArchiveQualityReport(symbol, archive_name, 0, (_checksum_event(symbol, archive_name, f"archive acquisition/verification failure: {exc}"),), False))
    return reports, rows


def _summary(reports: list[ArchiveQualityReport]) -> dict[str, int]:
    events = [event for report in reports for event in report.events]
    counts = Counter(event.anomaly_type for event in events)
    return {
        "archives": len(reports), "rows": sum(report.rows_processed for report in reports),
        "invalid_rows": len({(event.archive, event.row) for event in events if event.row is not None}),
        "missing_intervals": counts["MISSING_INTERVAL"], "timestamp_anomalies": counts["NON_ALIGNED_TIMESTAMP"],
        "duplicates": counts["DUPLICATE_TIMESTAMP"], "ordering_violations": counts["OUT_OF_ORDER_TIMESTAMP"],
        "ohlcv_anomalies": counts["INVALID_OHLC"] + counts["INVALID_VOLUME"],
        "checksum_failures": counts["CHECKSUM_FAILURE"],
        "other_issues": sum(value for key, value in counts.items() if key not in {
            "MISSING_INTERVAL", "NON_ALIGNED_TIMESTAMP", "DUPLICATE_TIMESTAMP",
            "OUT_OF_ORDER_TIMESTAMP", "INVALID_OHLC", "INVALID_VOLUME", "CHECKSUM_FAILURE",
        }),
    }


def _print_events(symbol: str, reports: list[ArchiveQualityReport]) -> None:
    for report in reports:
        for event in report.events:
            print("EVENT " + repr(asdict(event)))
    print(f"{symbol} SUMMARY {_summary(reports)}")
    print(f"{symbol} CERTIFICATION {certify(reports)}")


def verify_common(btc_reports: list[ArchiveQualityReport], eth_reports: list[ArchiveQualityReport]) -> str:
    all_events = [event for report in btc_reports + eth_reports for event in report.events]
    validate_partitions()
    if not all_events:
        state = "VALID"
    elif all(event.source_provenance.startswith("Binance Public Data issue #") for event in all_events):
        state = "VALID WITH DOCUMENTED SOURCE ANOMALIES"
    else:
        state = "UNUSABLE"
    validation_end = datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat()
    affected = [event.parsed_timestamp for event in all_events if event.parsed_timestamp]
    boundary_crossing = [ts for ts in affected if ts >= validation_end]
    print(f"COMMON CERTIFICATION {state}")
    print(f"COMMON AFFECTED_INTERVALS {len(affected)}")
    print(f"COMMON_VALIDATION_OOS_AFFECTED {bool(boundary_crossing)}")
    return state


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="gate1-binance-") as directory:
        root = Path(directory)
        btc_reports, btc_rows = verify_symbol("BTCUSDT", root / "BTCUSDT")
        eth_reports, eth_rows = verify_symbol("ETHUSDT", root / "ETHUSDT")
        _print_events("BTCUSDT", btc_reports)
        _print_events("ETHUSDT", eth_reports)
        common_state = verify_common(btc_reports, eth_reports)
        print(f"CERTIFICATION REPORT BTCUSDT={certify(btc_reports)} ETHUSDT={certify(eth_reports)} COMMON={common_state}")
        print(f"RUNTIME BTC_ARCHIVES={len(btc_reports)} BTC_ROWS={btc_rows} ETH_ARCHIVES={len(eth_reports)} ETH_ROWS={eth_rows}")
