from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from intelligence import build_event_dataset_manifest
from intelligence.sources import discover_fomc_statement_urls, parse_fomc_statement


DEVELOPMENT_START = datetime(2017, 8, 17, tzinfo=timezone.utc)
DEVELOPMENT_END = datetime(2022, 1, 1, tzinfo=timezone.utc)
EXPECTED_DEVELOPMENT_STATEMENT_COUNT = 37
INDEX_URLS = tuple(
    f"https://www.federalreserve.gov/newsevents/pressreleases/{year}-press.htm"
    for year in range(2017, 2022)
)
ASSETS = ("BTCUSDT", "ETHUSDT")
USER_AGENT = "ai-crypto-trading-command-center research/1.0 (public GitHub research project)"


def fetch(url: str, attempts: int = 3) -> bytes:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=30) as response:
                if getattr(response, "status", 200) != 200:
                    raise RuntimeError(f"HTTP {response.status}: {url}")
                return response.read()
        except Exception as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"failed to fetch {url}: {last_error}") from last_error


def main() -> None:
    discovered: set[str] = set()
    index_hashes: list[dict[str, str]] = []

    for index_url in INDEX_URLS:
        payload = fetch(index_url)
        from intelligence import hash_raw_payload
        index_hashes.append({"url": index_url, "raw_sha256": hash_raw_payload(payload)})
        discovered.update(discover_fomc_statement_urls(payload, index_url=index_url))

    records: list[tuple[str, object]] = []
    for url in sorted(discovered):
        payload = fetch(url)
        event = parse_fomc_statement(payload, source_url=url, assets=ASSETS)
        if DEVELOPMENT_START <= event.first_market_available_at < DEVELOPMENT_END:
            records.append((url, event))

    if len(records) != EXPECTED_DEVELOPMENT_STATEMENT_COUNT:
        raise RuntimeError(
            "Development FOMC statement count mismatch: "
            f"expected {EXPECTED_DEVELOPMENT_STATEMENT_COUNT}, got {len(records)}"
        )

    events = tuple(event for _, event in records)
    manifest = build_event_dataset_manifest(events)

    output = {
        "manifest_version": "fomc-development-manifest-v1",
        "github_sha": os.environ.get("GITHUB_SHA", "UNKNOWN"),
        "development_window": [
            DEVELOPMENT_START.isoformat().replace("+00:00", "Z"),
            DEVELOPMENT_END.isoformat().replace("+00:00", "Z"),
        ],
        "validation_or_oos_accessed": False,
        "discovery": {
            "index_urls": list(INDEX_URLS),
            "index_payload_hashes": index_hashes,
            "discovered_statement_url_count_2017_2021": len(discovered),
            "development_statement_count": len(records),
            "expected_development_statement_count": EXPECTED_DEVELOPMENT_STATEMENT_COUNT,
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
    path = outdir / "fomc_development_manifest.json"
    path.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")
    print(f"FOMC Development manifest generated: {manifest.dataset_id} ({manifest.record_count} events)")


if __name__ == "__main__":
    main()
