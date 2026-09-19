from datetime import datetime, timezone

import pytest

from intelligence import hash_raw_payload
from intelligence.sources import discover_cpi_release_urls, parse_cpi_release


EST_FIXTURE = b"""
<html><body>
<h2>Consumer Price Index News Release</h2>
<p>Transmission of material in this release is embargoed until
8:30 a.m. (EST) February 13, 2020</p>
</body></html>
"""

EDT_FIXTURE = b"""
<html><body>
<h2>Consumer Price Index News Release</h2>
<p>Transmission of material in this release is embargoed until
8:30 a.m. (EDT) June 10, 2020</p>
</body></html>
"""

ET_WINTER_FIXTURE = b"""
<html><body>
<h2>Consumer Price Index News Release</h2>
<p>Transmission of material in this release is embargoed until
8:30 a.m. (ET) February 10, 2021</p>
</body></html>
"""

ET_SUMMER_FIXTURE = b"""
<html><body>
<h2>Consumer Price Index News Release</h2>
<p>Transmission of material in this release is embargoed until
8:30 a.m. (ET) August 11, 2021</p>
</body></html>
"""


def test_cpi_archive_discovery_selects_html_release_links_only():
    payload = b"""
    <html><body>
      <a href="/news.release/archives/cpi_02102021.htm">January 2021 Consumer Price Index</a>
      <a href="/news.release/archives/cpi_02102021.pdf">PDF</a>
      <a href="/news.release/archives/empsit_02052021.htm">Employment Situation</a>
      <a href="/news.release/archives/cpi_08112021.htm">July 2021 Consumer Price Index</a>
    </body></html>
    """
    assert discover_cpi_release_urls(payload) == (
        "https://www.bls.gov/news.release/archives/cpi_02102021.htm",
        "https://www.bls.gov/news.release/archives/cpi_08112021.htm",
    )


def test_cpi_est_release_converts_to_utc():
    event = parse_cpi_release(
        EST_FIXTURE,
        source_url="https://www.bls.gov/news.release/archives/cpi_02132020.htm",
        assets=("BTCUSDT", "ETHUSDT"),
    )
    assert event.published_at == datetime(2020, 2, 13, 13, 30, tzinfo=timezone.utc)
    assert event.first_market_available_at == event.published_at
    assert event.event_time == event.published_at
    assert event.raw_event_hash == hash_raw_payload(EST_FIXTURE)


def test_cpi_edt_release_converts_to_utc():
    event = parse_cpi_release(
        EDT_FIXTURE,
        source_url="https://www.bls.gov/news.release/archives/cpi_06102020.htm",
        assets=("BTCUSDT", "ETHUSDT"),
    )
    assert event.published_at == datetime(2020, 6, 10, 12, 30, tzinfo=timezone.utc)


def test_generic_et_uses_historical_eastern_dst_winter():
    event = parse_cpi_release(
        ET_WINTER_FIXTURE,
        source_url="https://www.bls.gov/news.release/archives/cpi_02102021.htm",
        assets=("BTCUSDT",),
    )
    assert event.published_at == datetime(2021, 2, 10, 13, 30, tzinfo=timezone.utc)


def test_generic_et_uses_historical_eastern_dst_summer():
    event = parse_cpi_release(
        ET_SUMMER_FIXTURE,
        source_url="https://www.bls.gov/news.release/archives/cpi_08112021.htm",
        assets=("BTCUSDT",),
    )
    assert event.published_at == datetime(2021, 8, 11, 12, 30, tzinfo=timezone.utc)


def test_cpi_event_id_is_stable_but_raw_hash_tracks_reissued_page_bytes():
    url = "https://www.bls.gov/news.release/archives/cpi_02102021.htm"
    first = parse_cpi_release(ET_WINTER_FIXTURE, source_url=url, assets=("BTCUSDT",))
    revised = parse_cpi_release(
        ET_WINTER_FIXTURE.replace(b"</body>", b"<p>reissued correction</p></body>"),
        source_url=url,
        assets=("BTCUSDT",),
    )
    assert first.event_id == revised.event_id
    assert first.raw_event_hash != revised.raw_event_hash


def test_cpi_adapter_rejects_missing_release_identity():
    payload = b"""
    <html><body>
    Producer Price Index News Release
    Transmission of material in this release is embargoed until
    8:30 a.m. (EST) February 13, 2020
    </body></html>
    """
    with pytest.raises(ValueError, match="not identified"):
        parse_cpi_release(
            payload,
            source_url="https://www.bls.gov/news.release/archives/cpi_02132020.htm",
            assets=("BTCUSDT",),
        )


def test_cpi_adapter_rejects_missing_explicit_embargo_timestamp():
    payload = b"<html><body>Consumer Price Index News Release</body></html>"
    with pytest.raises(ValueError, match="embargo"):
        parse_cpi_release(
            payload,
            source_url="https://www.bls.gov/news.release/archives/cpi_02132020.htm",
            assets=("BTCUSDT",),
        )


def test_cpi_adapter_rejects_non_bls_source():
    with pytest.raises(ValueError, match="Bureau of Labor Statistics"):
        parse_cpi_release(
            EST_FIXTURE,
            source_url="https://example.com/cpi-copy",
            assets=("BTCUSDT",),
        )
