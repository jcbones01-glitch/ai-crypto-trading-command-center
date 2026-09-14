from __future__ import annotations

import json
import tempfile
import urllib.request
from dataclasses import asdict
from pathlib import Path

from research_core.data_ingestion import RESEARCH_END, RESEARCH_START, archive_url, checksum_url, verify_sha256_bytes
from research_core.data_quality import ArchiveQualityReport, DataQualityEvent, scan_archive
from research_core.data_quality_treatment_v2 import build_manifest, common_certification, common_certified_intervals
from research_core.source_identity import bind_source_identity


def months(start, end):
    year, month = start.year, start.month
    while (year, month) < (end.year, end.month):
        yield year, month
        month += 1
        if month == 13:
            year, month = year + 1, 1


def fetch(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def checksum_event(symbol: str, archive: str, message: str) -> DataQualityEvent:
    return DataQualityEvent(symbol, "1h", archive, None, None, None, None, "CHECKSUM_FAILURE",
                            "archive SHA-256 must match Binance CHECKSUM", "ERROR",
                            "Binance Public Data archive", message)


def scan_symbol(symbol: str, root: Path):
    reports: list[ArchiveQualityReport] = []
    paths: list[Path] = []
    for year, month in months(RESEARCH_START, RESEARCH_END):
        url = archive_url(symbol, year, month)
        name = Path(url).name
        try:
            payload = fetch(url)
            checksum = fetch(checksum_url(url)).decode("utf-8")
            if not verify_sha256_bytes(payload, checksum):
                reports.append(ArchiveQualityReport(symbol, name, 0, (checksum_event(symbol, name, "checksum mismatch"),), False))
                continue
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            paths.append(path)
            reports.append(scan_archive(path, symbol, True))
        except Exception as exc:
            reports.append(ArchiveQualityReport(symbol, name, 0, (checksum_event(symbol, name, f"acquisition/verification failure: {exc}"),), False))
    manifest = build_manifest(symbol, reports)
    if paths:
        manifest = bind_source_identity(manifest, paths)
    return reports, paths, manifest


def summary(reports):
    events = [event for report in reports for event in report.events]
    return {
        "archives": len(reports),
        "rows": sum(report.rows_processed for report in reports),
        "anomaly_events": len(events),
        "invalid_rows": len({(event.archive, event.row) for event in events if event.row is not None}),
        "affected_regions": None,
        "continuity_breaks": None,
        "excluded_intervals": None,
    }


def write_report(directory: Path, symbol: str, reports: list[ArchiveQualityReport], manifest) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "symbol": symbol,
        "summary": summary(reports),
        "source_integrity": manifest.source_integrity,
        "research_certification": manifest.research_certification,
        "treatment_protocol_version": manifest.treatment_protocol_version,
        "source_version": manifest.source_version,
        "dataset_identity": manifest.dataset_identity,
        "affected_regions": [asdict(x) for x in manifest.affected_regions],
        "continuity_breaks": [asdict(x) for x in manifest.continuity_breaks],
        "exclusions": [asdict(x) for x in manifest.exclusions],
        "certified_segments": [asdict(x) for x in manifest.certified_segments],
        "partitions": [asdict(x) for x in manifest.partitions],
        "anomaly_ids": list(manifest.anomaly_ids),
        "anomalies": [asdict(event) for report in reports for event in report.events],
    }
    payload["summary"]["affected_regions"] = len(manifest.affected_regions)
    payload["summary"]["continuity_breaks"] = len(manifest.continuity_breaks)
    payload["summary"]["excluded_intervals"] = len(manifest.exclusions)
    (directory / f"{symbol}-gate1a.json").write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="gate1a-binance-") as directory:
        root = Path(directory)
        btc_reports, btc_paths, btc = scan_symbol("BTCUSDT", root / "BTCUSDT")
        eth_reports, eth_paths, eth = scan_symbol("ETHUSDT", root / "ETHUSDT")
        common = common_certified_intervals(btc, eth)
        state = common_certification(btc, eth)
        output = Path("gate1a_reports")
        write_report(output, "BTCUSDT", btc_reports, btc)
        write_report(output, "ETHUSDT", eth_reports, eth)
        common_payload = {
            "treatment_protocol_version": btc.treatment_protocol_version,
            "btc_dataset_identity": btc.dataset_identity,
            "eth_dataset_identity": eth.dataset_identity,
            "common_certification": state,
            "common_certified_intervals": [asdict(x) for x in common],
            "common_continuity_breaks": [
                {"start": max(b.start, e.start), "end": min(b.end, e.end)}
                for b in btc.continuity_breaks for e in eth.continuity_breaks
                if max(b.start, e.start) < min(b.end, e.end)
            ],
        }
        (output / "COMMON-gate1a.json").write_text(json.dumps(common_payload, sort_keys=True, indent=2), encoding="utf-8")
        print(f"GATE1A BTC SOURCE={btc.source_integrity} RESEARCH={btc.research_certification} REGIONS={len(btc.affected_regions)} BREAKS={len(btc.continuity_breaks)} EXCLUSIONS={len(btc.exclusions)}")
        print(f"GATE1A ETH SOURCE={eth.source_integrity} RESEARCH={eth.research_certification} REGIONS={len(eth.affected_regions)} BREAKS={len(eth.continuity_breaks)} EXCLUSIONS={len(eth.exclusions)}")
        print(f"GATE1A COMMON CERTIFICATION={state} COMMON_SEGMENTS={len(common)}")
        print(f"GATE1A BTC_IDENTITY={btc.dataset_identity}")
        print(f"GATE1A ETH_IDENTITY={eth.dataset_identity}")
