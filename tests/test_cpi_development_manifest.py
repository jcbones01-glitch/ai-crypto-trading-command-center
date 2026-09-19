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
