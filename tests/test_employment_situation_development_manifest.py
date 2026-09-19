import hashlib
import json
from datetime import datetime, timezone

import pytest

import research.scripts.build_employment_situation_development_manifest as mod


def test_employment_manifest_scope_and_counts_are_frozen():
    assert mod.DEVELOPMENT_START == datetime(2017, 8, 17, tzinfo=timezone.utc)
    assert mod.DEVELOPMENT_END == datetime(2022, 1, 1, tzinfo=timezone.utc)
    assert mod.EXPECTED_CALENDAR_CANDIDATE_COUNT == 60
    assert mod.EXPECTED_DEVELOPMENT_RELEASE_COUNT == 52
    assert mod.ASSETS == ("BTCUSDT", "ETHUSDT")


def test_archive_calendar_year_parses_expected_shape_only():
    assert mod.archive_calendar_year(
        "https://www.bls.gov/news.release/archives/empsit_01082021.htm"
    ) == 2021
    with pytest.raises(ValueError, match="unexpected Employment Situation"):
        mod.archive_calendar_year(
            "https://www.bls.gov/news.release/archives/empsit_01082021.pdf"
        )


def write_snapshot(tmp_path, payload=b"index", *, bad_hash=False):
    rel = "index.htm"
    (tmp_path / rel).write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    if bad_hash:
        digest = "0" * 64
    inventory = {
        "snapshot_version": "bls-employment-situation-dom-snapshot-v1",
        "responses": [
            {
                "url": mod.ARCHIVE_INDEX_URL,
                "path": rel,
                "sha256": digest,
                "retrieved_at": "2026-09-19T06:30:00Z",
                "acquisition_method": "test-fixture",
            }
        ],
    }
    (tmp_path / "inventory.json").write_text(json.dumps(inventory))
    return payload


def test_snapshot_fetcher_replays_exact_bytes_without_network_fallback(tmp_path):
    payload = write_snapshot(tmp_path)
    read, inventory_hash = mod.snapshot_fetcher(tmp_path)
    assert read(mod.ARCHIVE_INDEX_URL) == payload
    assert read.snapshot_version == "bls-employment-situation-dom-snapshot-v1"
    assert len(inventory_hash) == 64
    with pytest.raises(RuntimeError, match="missing official source snapshot"):
        read("https://www.bls.gov/news.release/archives/empsit_01082021.htm")


def test_snapshot_fetcher_rejects_tampered_representation(tmp_path):
    write_snapshot(tmp_path, bad_hash=True)
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        mod.snapshot_fetcher(tmp_path)


def test_snapshot_fetcher_blocks_when_inventory_missing(tmp_path):
    with pytest.raises(RuntimeError, match="certification remains blocked"):
        mod.snapshot_fetcher(tmp_path)
