from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from intelligence import build_event_dataset_manifest, hash_raw_payload
from intelligence.sources import discover_cpi_release_urls, parse_cpi_release
from intelligence.sources.bls_cpi import ARCHIVE_INDEX_URL


DEVELOPMENT_START = datetime(2017, 8, 17, tzinfo=timezone.utc)
DEVELOPMENT_END = datetime(2022, 1, 1, tzinfo=timezone.utc)
EXPECTED_DEVELOPMENT_RELEASE_COUNT = 52
EXPECTED_CALENDAR_CANDIDATE_COUNT = 60
ASSETS = ("BTCUSDT", "ETHUSDT")
USER_AGENT = "ai-crypto-trading-command-center research/1.0 (public GitHub research project)"

_ARCHIVE_FILENAME_RE = re.compile(r"^cpi_(\d{2})(\d{2})(\d{4})\.htm$", re.IGNORECASE)


def fetch(url: str, attempts: int = 3) -> bytes:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=45) as response:
                if getattr(response, "status", 200) != 200:
                    raise RuntimeError(f"HTTP {response.status}: {url}")
                return response.read()
        except Exception as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"failed to fetch {url}: {last_error}") from last_error


def archive_calendar_year(url: str) -> int:
    name = Path(urlparse(url).path).name
    match = _ARCHIVE_FILENAME_RE.match(name)
    if not match:
        raise ValueError(f"unexpected CPI archive filename: {name}")
    return int(match.group(3))


def main() -> None:
    index_payload = fetch(ARCHIVE_INDEX_URL)
    discovered = discover_cpi_release_urls(index_payload, index_url=ARCHIVE_INDEX_URL)

    calendar_candidates = tuple(
        url for url in discovered
        if 2017 <= archive_calendar_year(url) <= 2021
    )
    if len(calendar_candidates) != EXPECTED_CALENDAR_CANDIDATE_COUNT:
        raise RuntimeError(
            "CPI 2017-2021 archive candidate count mismatch: "
            f"expected {EXPECTED_CALENDAR_CANDIDATE_COUNT}, got {len(calendar_candidates)}"
        )

    records: list[tuple[str, object]] = []
    for url in calendar_candidates:
        payload = fetch(url)
        event = parse_cpi_release(payload, source_url=url, assets=ASSETS)
        if DEVELOPMENT_START <= event.first_market_available_at < DEVELOPMENT_END:
            records.append((url, event))

    if len(records) != EXPECTED_DEVELOPMENT_RELEASE_COUNT:
        raise RuntimeError(
            "Development CPI release count mismatch: "
            f"expected {EXPECTED_DEVELOPMENT_RELEASE_COUNT}, got {len(records)}"
        )

    events = tuple(event for _, event in records)
    manifest = build_event_dataset_manifest(events)

    output = {
        "manifest_version": "cpi-development-manifest-v1",
        "github_sha": os.environ.get("GITHUB_SHA", "UNKNOWN"),
        "development_window": [
            DEVELOPMENT_START.isoformat().replace("+00:00", "Z"),
            DEVELOPMENT_END.isoformat().replace("+00:00", "Z"),
        ],
        "validation_or_oos_accessed": False,
        "discovery": {
            "archive_index_url": ARCHIVE_INDEX_URL,
            "archive_index_raw_sha256": hash_raw_payload(index_payload),
            "all_discovered_html_cpi_release_count": len(discovered),
            "calendar_2017_2021_candidate_count": len(calendar_candidates),
            "expected_calendar_2017_2021_candidate_count": EXPECTED_CALENDAR_CANDIDATE_COUNT,
            "development_release_count": len(records),
            "expected_development_release_count": EXPECTED_DEVELOPMENT_RELEASE_COUNT,
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
            for url, event in sorted(records, key=lambda item: item[1].first_market_available_at)
        ],
    }

    outdir = Path("event_intelligence_results")
    outdir.mkdir(exist_ok=True)
    path = outdir / "cpi_development_manifest.json"
    path.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print(f"CPI Development manifest generated: {manifest.dataset_id} ({manifest.record_count} events)")


if __name__ == "__main__":
    main()
