from datetime import datetime, timezone

import research.scripts.build_fomc_development_manifest as mod


def test_fomc_manifest_scope_is_development_only():
    assert mod.DEVELOPMENT_START == datetime(2017, 8, 17, tzinfo=timezone.utc)
    assert mod.DEVELOPMENT_END == datetime(2022, 1, 1, tzinfo=timezone.utc)
    assert all("2017-press.htm" not in url or url.startswith("https://www.federalreserve.gov/") for url in mod.INDEX_URLS)
    assert len(mod.INDEX_URLS) == 5
    assert mod.INDEX_URLS[0].endswith("/2017-press.htm")
    assert mod.INDEX_URLS[-1].endswith("/2021-press.htm")


def test_fomc_manifest_expected_count_is_frozen():
    assert mod.EXPECTED_DEVELOPMENT_STATEMENT_COUNT == 37


def test_fomc_manifest_assets_are_frozen():
    assert mod.ASSETS == ("BTCUSDT", "ETHUSDT")
