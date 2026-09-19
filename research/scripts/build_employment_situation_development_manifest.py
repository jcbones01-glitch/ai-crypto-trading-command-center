from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from intelligence import build_event_dataset_manifest, hash_raw_payload
from intelligence.sources import (
    discover_employment_situation_urls,
    parse_employment_situation_release,
)
from intelligence.sources.bls_employment_situation import ARCHIVE_INDEX_URL


DEVELOPMENT_START = datetime(2017, 8, 17, tzinfo=timezone.utc)
DEVELOPMENT_END = datetime(2022, 1, 1, tzinfo=timezone.utc)
EXPECTED_CALENDAR_CANDIDATE_COUNT = 60
EXPECTED_DEVELOPMENT_RELEASE_COUNT = 52
ASSETS = ("BTCUSDT", "ETHUSDT")

_ARCHIVE_FILENAME_RE = re.compile(
    r"^empsit_(\d{2})(\d{2})(\d{4})\.htm$",
    re.IGNORECASE,
)


def archive_calendar_year(url: str) -> int:
    name = Path(urlparse(url).path).name
    match = _ARCHIVE_FILENAME_RE.match(name)
    if not match:
        raise ValueError(f"unexpected Employment Situation archive filename: {name}")
    return int(match.group(3))


def snapshot_fetcher(snapshot_dir: Path):
    """Replay reviewed first-party BLS representations with no network fallback."""
    root = snapshot_dir.resolve()
    inventory_path = root / "inventory.json"
    if not inventory_path.is_file():
        raise RuntimeError(
            "Employment Situation source snapshot unavailable; certification remains blocked"
        )

    inventory_bytes = inventory_path.read_bytes()
    inventory = json.loads(inventory_bytes)
    if inventory.get("snapshot_version") not in {
        "bls-employment-situation-dom-snapshot-v1",
        "bls-employment-situation-raw-snapshot-v1",
    }:
        raise ValueError("unsupported Employment Situation snapshot version")

    entries: dict[str, bytes] = {}
    for entry in inventory["responses"]:
        url = entry["url"]
        parsed = urlparse(url)
        if (
            parsed.scheme != "https"
            or parsed.netloc != "www.bls.gov"
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("snapshot requires canonical official BLS URLs")

        if url != ARCHIVE_INDEX_URL:
            expected_path = "/news.release/archives/" + Path(parsed.path).name
            if parsed.path != expected_path:
                raise ValueError("unexpected Employment Situation snapshot path")
            if not 2017 <= archive_calendar_year(url) <= 2021:
                raise ValueError("snapshot release outside allowed calendar years")

        if url in entries:
            raise ValueError("duplicate snapshot URL")

        retrieved_at = datetime.fromisoformat(
            entry["retrieved_at"].replace("Z", "+00:00")
        )
        if retrieved_at.tzinfo is None or not entry.get("acquisition_method"):
            raise ValueError("snapshot acquisition provenance missing")

        relative = Path(entry["path"])
        path = (root / relative).resolve()
        if relative.is_absolute() or not path.is_relative_to(root):
            raise ValueError("snapshot path escapes root")
        if not path.is_file():
            raise RuntimeError(f"missing snapshot representation: {relative}")

        payload = path.read_bytes()
        if hash_raw_payload(payload) != entry["sha256"]:
            raise ValueError("snapshot representation SHA-256 mismatch")
        entries[url] = payload

    def read(url: str) -> bytes:
        if url not in entries:
            raise RuntimeError(f"missing official source snapshot: {url}")
        return entries[url]

    read.snapshot_version = inventory["snapshot_version"]
    return read, hash_raw_payload(inventory_bytes)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=Path("research/sources/bls_employment_situation_v1"),
    )
    args = parser.parse_args()

    read_source, inventory_hash = snapshot_fetcher(args.snapshot_dir)
    index_payload = read_source(ARCHIVE_INDEX_URL)
    discovered = discover_employment_situation_urls(
        index_payload,
        index_url=ARCHIVE_INDEX_URL,
    )

    calendar_candidates = tuple(
        url for url in discovered if 2017 <= archive_calendar_year(url) <= 2021
    )
    if len(calendar_candidates) != EXPECTED_CALENDAR_CANDIDATE_COUNT:
        raise RuntimeError(
            "Employment Situation 2017-2021 archive candidate count mismatch: "
            f"expected {EXPECTED_CALENDAR_CANDIDATE_COUNT}, got {len(calendar_candidates)}"
        )

    payload_format = (
        "rendered-text"
        if read_source.snapshot_version == "bls-employment-situation-dom-snapshot-v1"
        else "html"
    )
    records: list[tuple[str, object]] = []
    for url in calendar_candidates:
        payload = read_source(url)
        event = parse_employment_situation_release(
            payload,
            source_url=url,
            assets=ASSETS,
            payload_format=payload_format,
        )
        if DEVELOPMENT_START <= event.first_market_available_at < DEVELOPMENT_END:
            records.append((url, event))

    if len(records) != EXPECTED_DEVELOPMENT_RELEASE_COUNT:
        raise RuntimeError(
            "Development Employment Situation release count mismatch: "
            f"expected {EXPECTED_DEVELOPMENT_RELEASE_COUNT}, got {len(records)}"
        )

    by_year: dict[str, int] = {}
    for _, event in records:
        key = str(event.first_market_available_at.year)
        by_year[key] = by_year.get(key, 0) + 1
    expected_years = {"2017": 4, "2018": 12, "2019": 12, "2020": 12, "2021": 12}
    if by_year != expected_years:
        raise RuntimeError(
            f"Development Employment Situation yearly counts mismatch: {by_year}"
        )

    events = tuple(event for _, event in records)
    manifest = build_event_dataset_manifest(events)

    output = {
        "manifest_version": "employment-situation-development-manifest-v1",
        "source_mode": (
            "dom-snapshot"
            if read_source.snapshot_version == "bls-employment-situation-dom-snapshot-v1"
            else "raw-snapshot"
        ),
        "snapshot_version": read_source.snapshot_version,
        "snapshot_inventory_sha256": inventory_hash,
        "github_sha": os.environ.get("GITHUB_SHA", "UNKNOWN"),
        "development_window": [
            DEVELOPMENT_START.isoformat().replace("+00:00", "Z"),
            DEVELOPMENT_END.isoformat().replace("+00:00", "Z"),
        ],
        "validation_or_oos_accessed": False,
        "discovery": {
            "archive_index_url": ARCHIVE_INDEX_URL,
            "calendar_2017_2021_candidate_count": len(calendar_candidates),
            "expected_calendar_2017_2021_candidate_count": EXPECTED_CALENDAR_CANDIDATE_COUNT,
            "development_release_count": len(records),
            "expected_development_release_count": EXPECTED_DEVELOPMENT_RELEASE_COUNT,
            "development_yearly_counts": by_year,
        },
        "event_dataset": {
            "protocol_version": manifest.protocol_version,
            "dataset_id": manifest.dataset_id,
            "record_count": manifest.record_count,
            "first_market_available_at": manifest.first_market_available_at.isoformat().replace("+00:00", "Z"),
            "last_market_available_at": manifest.last_market_available_at.isoformat().replace("+00:00", "Z"),
            "source_ids": list(manifest.source_ids),
        },
        "events": [
            {
                "source_url": url,
                "event_id": event.event_id,
                "event_type": event.event_type,
                "region": event.region,
                "assets": list(event.assets),
                "event_time": event.event_time.isoformat().replace("+00:00", "Z"),
                "published_at": event.published_at.isoformat().replace("+00:00", "Z"),
                "first_market_available_at": event.first_market_available_at.isoformat().replace("+00:00", "Z"),
                "source_id": event.source_id,
                "source_version": event.source_version,
                "raw_event_hash": event.raw_event_hash,
            }
            for url, event in sorted(
                records,
                key=lambda item: item[1].first_market_available_at,
            )
        ],
    }

    outdir = Path("event_intelligence_results")
    outdir.mkdir(exist_ok=True)
    path = outdir / "employment_situation_development_manifest.json"
    path.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print(
        "Employment Situation Development manifest generated: "
        f"{manifest.dataset_id} ({manifest.record_count} events)"
    )


if __name__ == "__main__":
    main()
