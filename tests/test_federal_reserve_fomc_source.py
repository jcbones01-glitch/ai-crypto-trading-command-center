from datetime import datetime, timezone

import pytest

from intelligence import hash_raw_payload
from intelligence.sources import parse_fomc_statement


EST_FIXTURE = b"""
<html><body>
<div>December 13, 2017</div>
<h3>Federal Reserve issues FOMC statement</h3>
<p>For release at 2:00 p.m. EST</p>
</body></html>
"""

EDT_FIXTURE = b"""
<html><body>
<div>July 28, 2021</div>
<h3>Federal Reserve issues FOMC statement</h3>
<p>For release at 2:00 p.m. EDT</p>
</body></html>
"""

EMERGENCY_FIXTURE = b"""
<html><body>
<div>March 3, 2020</div>
<h3>Federal Reserve issues FOMC statement</h3>
<p>For release at 10:00 a.m. EST</p>
</body></html>
"""


def test_fomc_est_release_converts_to_utc():
    event = parse_fomc_statement(
        EST_FIXTURE,
        source_url="https://www.federalreserve.gov/newsevents/pressreleases/monetary20171213a.htm",
        assets=("BTCUSDT", "ETHUSDT"),
    )
    assert event.published_at == datetime(2017, 12, 13, 19, 0, tzinfo=timezone.utc)
    assert event.first_market_available_at == event.published_at
    assert event.event_time == event.published_at
    assert event.raw_event_hash == hash_raw_payload(EST_FIXTURE)
    assert event.source_id == "federal-reserve-board/fomc-statement"
    assert event.source_version == "federal-reserve-fomc-html-v1"


def test_fomc_edt_release_converts_to_utc():
    event = parse_fomc_statement(
        EDT_FIXTURE,
        source_url="https://www.federalreserve.gov/newsevents/pressreleases/monetary20210728a.htm",
        assets=("BTCUSDT", "ETHUSDT"),
    )
    assert event.published_at == datetime(2021, 7, 28, 18, 0, tzinfo=timezone.utc)


def test_fomc_emergency_statement_uses_its_actual_release_hour():
    event = parse_fomc_statement(
        EMERGENCY_FIXTURE,
        source_url="https://www.federalreserve.gov/newsevents/pressreleases/monetary20200303a.htm",
        assets=("BTCUSDT", "ETHUSDT"),
    )
    assert event.published_at == datetime(2020, 3, 3, 15, 0, tzinfo=timezone.utc)


def test_fomc_event_id_is_stable_but_raw_hash_tracks_payload_changes():
    url = "https://www.federalreserve.gov/newsevents/pressreleases/monetary20171213a.htm"
    first = parse_fomc_statement(EST_FIXTURE, source_url=url, assets=("BTCUSDT",))
    changed = parse_fomc_statement(
        EST_FIXTURE.replace(b"</body>", b"<div>metadata change</div></body>"),
        source_url=url,
        assets=("BTCUSDT",),
    )
    assert first.event_id == changed.event_id
    assert first.raw_event_hash != changed.raw_event_hash


def test_fomc_adapter_rejects_missing_statement_identity():
    payload = b"""
    <html><body>
    December 13, 2017
    Federal Reserve announces a monetary-policy action
    For release at 2:00 p.m. EST
    </body></html>
    """
    with pytest.raises(ValueError, match="not identified"):
        parse_fomc_statement(
            payload,
            source_url="https://www.federalreserve.gov/newsevents/pressreleases/monetary20171213b.htm",
            assets=("BTCUSDT",),
        )


def test_fomc_adapter_rejects_missing_explicit_release_timestamp():
    payload = b"<html><body>December 13, 2017 Federal Reserve issues FOMC statement</body></html>"
    with pytest.raises(ValueError, match="For release at"):
        parse_fomc_statement(
            payload,
            source_url="https://www.federalreserve.gov/newsevents/pressreleases/example.htm",
            assets=("BTCUSDT",),
        )


def test_fomc_adapter_rejects_ambiguous_timezone():
    payload = b"<html><body>December 13, 2017 Federal Reserve issues FOMC statement For release at 2:00 p.m. ET</body></html>"
    with pytest.raises(ValueError, match="For release at"):
        parse_fomc_statement(
            payload,
            source_url="https://www.federalreserve.gov/newsevents/pressreleases/example.htm",
            assets=("BTCUSDT",),
        )


def test_fomc_adapter_rejects_non_federal_reserve_source():
    with pytest.raises(ValueError, match="Federal Reserve Board URL"):
        parse_fomc_statement(
            EST_FIXTURE,
            source_url="https://example.com/fomc-copy",
            assets=("BTCUSDT",),
        )
