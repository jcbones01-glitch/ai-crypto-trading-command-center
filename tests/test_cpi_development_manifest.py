from datetime import datetime, timezone

import pytest

import research.scripts.build_cpi_development_manifest as mod


def test_cpi_manifest_scope_is_development_only():
    assert mod.DEVELOPMENT_START == datetime(2017, 8, 17, tzinfo=timezone.utc)
    assert mod.DEVELOPMENT_END == datetime(2022, 1, 1, tzinfo=timezone.utc)


def test_cpi_manifest_expected_counts_are_frozen():
    assert mod.EXPECTED_CALENDAR_CANDIDATE_COUNT == 60
    assert mod.EXPECTED_DEVELOPMENT_RELEASE_COUNT == 52


def test_cpi_manifest_assets_are_frozen():
    assert mod.ASSETS == ("BTCUSDT", "ETHUSDT")


def test_archive_calendar_year_parses_only_expected_filename_shape():
    assert mod.archive_calendar_year(
        "https://www.bls.gov/news.release/archives/cpi_02102021.htm"
    ) == 2021
    with pytest.raises(ValueError, match="unexpected CPI archive filename"):
        mod.archive_calendar_year(
            "https://www.bls.gov/news.release/archives/cpi_02102021.pdf"
        )


def make_snapshot(tmp_path):
    import json
    from intelligence import hash_raw_payload
    from tests.test_bls_cpi_source import ET_WINTER_FIXTURE
    url = "https://www.bls.gov/news.release/archives/cpi_02102021.htm"
    (tmp_path / "release.htm").write_bytes(ET_WINTER_FIXTURE)
    inventory = {"snapshot_version": "bls-cpi-raw-snapshot-v1", "responses": [{
        "url": url, "path": "release.htm",
        "sha256": hash_raw_payload(ET_WINTER_FIXTURE),
        "retrieved_at": "2026-09-19T00:00:00Z",
        "acquisition_method": "synthetic test fixture; not historical evidence",
    }]}
    (tmp_path / "inventory.json").write_text(json.dumps(inventory))
    return url, inventory


def test_snapshot_replays_exact_bytes_without_network(tmp_path, monkeypatch):
    from tests.test_bls_cpi_source import ET_WINTER_FIXTURE
    def forbidden(*args, **kwargs):
        raise AssertionError("network forbidden")
    monkeypatch.setattr(mod, "urlopen", forbidden)
    url, _ = make_snapshot(tmp_path)
    read, digest = mod.snapshot_fetcher(tmp_path)
    assert read(url) == ET_WINTER_FIXTURE
    assert len(digest) == 64
    with pytest.raises(RuntimeError, match="missing official source"):
        read(mod.ARCHIVE_INDEX_URL)


def test_snapshot_rejects_tampered_bytes(tmp_path):
    make_snapshot(tmp_path)
    (tmp_path / "release.htm").write_bytes(b"changed")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        mod.snapshot_fetcher(tmp_path)


@pytest.mark.parametrize("change, message", [
    ({"url": "https://example.com/cpi.htm"}, "official BLS"),
    ({"path": "../outside.htm"}, "escapes root"),
    ({"url": "https://www.bls.gov/news.release/archives/cpi_02102022.htm"}, "outside allowed"),
    ({"retrieved_at": "2026-09-19T00:00:00"}, "provenance missing"),
])
def test_snapshot_rejects_invalid_provenance(tmp_path, change, message):
    import json
    _, inventory = make_snapshot(tmp_path)
    inventory["responses"][0].update(change)
    (tmp_path / "inventory.json").write_text(json.dumps(inventory))
    with pytest.raises(ValueError, match=message):
        mod.snapshot_fetcher(tmp_path)


def test_snapshot_rejects_duplicate_urls(tmp_path):
    import json
    _, inventory = make_snapshot(tmp_path)
    inventory["responses"] *= 2
    (tmp_path / "inventory.json").write_text(json.dumps(inventory))
    with pytest.raises(ValueError, match="duplicate"):
        mod.snapshot_fetcher(tmp_path)


def test_missing_snapshot_does_not_fall_back_to_live(tmp_path):
    with pytest.raises(RuntimeError, match="certification remains blocked"):
        mod.snapshot_fetcher(tmp_path)


def test_complete_synthetic_snapshot_builds_52_events_offline(tmp_path, monkeypatch):
    import json
    import sys
    from intelligence import hash_raw_payload
    root = tmp_path / 'sources'
    root.mkdir()
    entries, links = [], []
    for year in range(2017, 2022):
        for month in range(1, 13):
            name = f'cpi_{month:02d}10{year}.htm'
            url = f'https://www.bls.gov/news.release/archives/{name}'
            links.append(f'<a href="{url}">Consumer Price Index</a>')
            date = datetime(year, month, 10).strftime('%B %d, %Y')
            payload = (f'Consumer Price Index News Release\n'
                       f'Transmission of material in this release is embargoed until '
                       f'8:30 a.m. (ET) {date}').encode()
            (root / name).write_bytes(payload)
            entries.append({'url': url, 'path': name, 'sha256': hash_raw_payload(payload),
                            'retrieved_at': '2026-09-19T00:00:00Z',
                            'acquisition_method': 'SYNTHETIC TEST ONLY'})
    index = ''.join(links).encode()
    (root / 'index.htm').write_bytes(index)
    entries.append({'url': mod.ARCHIVE_INDEX_URL, 'path': 'index.htm',
                    'sha256': hash_raw_payload(index), 'retrieved_at': '2026-09-19T00:00:00Z',
                    'acquisition_method': 'SYNTHETIC TEST ONLY'})
    (root / 'inventory.json').write_text(json.dumps({
        'snapshot_version': 'bls-cpi-raw-snapshot-v1', 'responses': entries}))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, 'argv', ['builder', '--snapshot-dir', str(root)])
    def forbidden(*args, **kwargs):
        raise AssertionError('network forbidden')
    monkeypatch.setattr(mod, 'urlopen', forbidden)
    mod.main()
    output_path = tmp_path / 'event_intelligence_results/cpi_development_manifest.json'
    first = output_path.read_bytes()
    output = json.loads(first)
    assert output['event_dataset']['record_count'] == 52
    assert output['validation_or_oos_accessed'] is False
    assert output['source_mode'] == 'raw-snapshot'
    assert len({event['event_id'] for event in output['events']}) == 52
    mod.main()
    assert output_path.read_bytes() == first
