from datetime import datetime, timezone

import pytest

from intelligence import hash_raw_payload
from intelligence.sources import (
    discover_employment_situation_urls,
    parse_employment_situation_release,
)


EDT_FIXTURE = b"""
<html><body>
<h2>Employment Situation News Release</h2>
<p>Transmission of material in this release is embargoed until USDL-17-1347
8:30 a.m. (EDT) Friday, October 6, 2017</p>
</body></html>
"""

EST_FIXTURE = b"""
<html><body>
<h2>Employment Situation News Release</h2>
<p>Transmission of material in this news release is embargoed until USDL-20-0010
8:30 a.m. (EST) Friday, January 10, 2020</p>
</body></html>
"""

ET_FIXTURE = b"""
Employment Situation News Release
Transmission of material in this news release is embargoed until USDL-21-0002
8:30 a.m. (ET) Friday, January 8, 2021
"""


def test_employment_archive_discovery_selects_html_release_links_only():
    payload = b"""
    <html><body>
      <a href="/news.release/archives/empsit_01082021.htm">December 2020 Employment Situation</a>
      <a href="/news.release/archives/empsit_01082021.pdf">PDF</a>
      <a href="/news.release/archives/cpi_01132021.htm">Consumer Price Index</a>
      <a href="/news.release/archives/empsit_02052021.htm">January 2021 Employment Situation</a>
    </body></html>
    """
    assert discover_employment_situation_urls(payload) == (
        "https://www.bls.gov/news.release/archives/empsit_01082021.htm",
        "https://www.bls.gov/news.release/archives/empsit_02052021.htm",
    )


def test_employment_edt_release_converts_to_utc():
    event = parse_employment_situation_release(
        EDT_FIXTURE,
        source_url="https://www.bls.gov/news.release/archives/empsit_10062017.htm",
        assets=("BTCUSDT", "ETHUSDT"),
    )
    assert event.published_at == datetime(2017, 10, 6, 12, 30, tzinfo=timezone.utc)
    assert event.first_market_available_at == event.published_at
    assert event.event_time == event.published_at
    assert event.raw_event_hash == hash_raw_payload(EDT_FIXTURE)


def test_employment_est_release_converts_to_utc():
    event = parse_employment_situation_release(
        EST_FIXTURE,
        source_url="https://www.bls.gov/news.release/archives/empsit_01102020.htm",
        assets=("BTCUSDT",),
    )
    assert event.published_at == datetime(2020, 1, 10, 13, 30, tzinfo=timezone.utc)


def test_employment_generic_et_uses_historical_eastern_offset():
    event = parse_employment_situation_release(
        ET_FIXTURE,
        source_url="https://www.bls.gov/news.release/archives/empsit_01082021.htm",
        assets=("BTCUSDT",),
        payload_format="rendered-text",
    )
    assert event.published_at == datetime(2021, 1, 8, 13, 30, tzinfo=timezone.utc)
    assert event.source_version == "bls-employment-situation-rendered-text-v1"


def test_employment_event_id_stable_but_payload_hash_tracks_reissue():
    url = "https://www.bls.gov/news.release/archives/empsit_01102020.htm"
    first = parse_employment_situation_release(EST_FIXTURE, source_url=url, assets=("BTCUSDT",))
    revised = parse_employment_situation_release(
        EST_FIXTURE.replace(b"</body>", b"<p>reissued correction</p></body>"),
        source_url=url,
        assets=("BTCUSDT",),
    )
    assert first.event_id == revised.event_id
    assert first.raw_event_hash != revised.raw_event_hash


def test_employment_rejects_wrong_release_identity():
    payload = b"""
    <html><body>
    Consumer Price Index News Release
    Transmission of material in this release is embargoed until
    8:30 a.m. (EST) Friday, January 10, 2020
    </body></html>
    """
    with pytest.raises(ValueError, match="not identified"):
        parse_employment_situation_release(
            payload,
            source_url="https://www.bls.gov/news.release/archives/empsit_01102020.htm",
            assets=("BTCUSDT",),
        )


def test_employment_rejects_missing_explicit_embargo_time():
    payload = b"<html><body>Employment Situation News Release</body></html>"
    with pytest.raises(ValueError, match="embargo"):
        parse_employment_situation_release(
            payload,
            source_url="https://www.bls.gov/news.release/archives/empsit_01102020.htm",
            assets=("BTCUSDT",),
        )


def test_employment_rejects_non_bls_source():
    with pytest.raises(ValueError, match="Bureau of Labor Statistics"):
        parse_employment_situation_release(
            EDT_FIXTURE,
            source_url="https://example.com/empsit-copy",
            assets=("BTCUSDT",),
        )
