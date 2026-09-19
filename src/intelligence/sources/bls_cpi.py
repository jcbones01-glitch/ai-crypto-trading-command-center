from __future__ import annotations

import html
import re
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

from intelligence.event_schema import EventRecord, hash_raw_payload


SOURCE_ID = "bls/cpi-news-release"
SOURCE_VERSION = "bls-cpi-html-v1"
ARCHIVE_INDEX_URL = "https://www.bls.gov/bls/news-release/cpi.htm"
_REQUIRED_TITLE = "Consumer Price Index News Release"

_ARCHIVE_PATH_RE = re.compile(r"^/news\.release/archives/cpi_\d{8}\.htm$", re.IGNORECASE)
_EMBARGO_RE = re.compile(
    r"embargoed\s+until\s+"
    r"(\d{1,2}):(\d{2})\s*([ap])\.m\.\s*"
    r"\((EST|EDT|ET)\)\s+"
    r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
    r"(\d{1,2}),\s+(\d{4})",
    re.IGNORECASE,
)

_FIXED_EASTERN = {
    "EST": timezone(timedelta(hours=-5), name="EST"),
    "EDT": timezone(timedelta(hours=-4), name="EDT"),
}
_EASTERN = ZoneInfo("America/New_York")


class _ArchiveLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._href: str | None = None
        self._parts: list[str] = []
        self.matches: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        self._href = dict(attrs).get("href")
        self._parts = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._href is None:
            return
        parsed = urlparse(self._href)
        label = re.sub(r"\s+", " ", " ".join(self._parts)).strip()
        if _ARCHIVE_PATH_RE.match(parsed.path) and "consumer price index" in label.lower():
            self.matches.append(self._href)
        self._href = None
        self._parts = []


def _plain_text(raw_payload: bytes) -> str:
    if not isinstance(raw_payload, bytes):
        raise TypeError("raw_payload must be bytes")
    decoded = raw_payload.decode("utf-8", errors="strict")
    no_tags = re.sub(r"<[^>]+>", " ", decoded)
    return re.sub(r"\s+", " ", html.unescape(no_tags)).strip()


def _validate_bls_url(source_url: str) -> None:
    parsed = urlparse(source_url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or hostname not in {"bls.gov", "www.bls.gov"}:
        raise ValueError("source_url must be an HTTPS U.S. Bureau of Labor Statistics URL")


def discover_cpi_release_urls(raw_index_payload: bytes, *, index_url: str = ARCHIVE_INDEX_URL) -> tuple[str, ...]:
    """Discover archived HTML CPI release pages from the official BLS index."""
    _validate_bls_url(index_url)
    if not isinstance(raw_index_payload, bytes):
        raise TypeError("raw_index_payload must be bytes")
    parser = _ArchiveLinkParser()
    parser.feed(raw_index_payload.decode("utf-8", errors="strict"))

    urls: set[str] = set()
    for href in parser.matches:
        url = urljoin(index_url, href)
        _validate_bls_url(url)
        urls.add(url)
    return tuple(sorted(urls))


def _validate_release_identity(text: str) -> None:
    if _REQUIRED_TITLE.lower() not in text.lower():
        raise ValueError("page is not identified as a Consumer Price Index News Release")
    if "Transmission of material in this release is embargoed until".lower() not in text.lower():
        raise ValueError("CPI embargo statement not found")


def _parse_embargo_timestamp(text: str) -> datetime:
    match = _EMBARGO_RE.search(text)
    if not match:
        raise ValueError("explicit CPI embargo timestamp with EST/EDT/ET not found")

    hour_text, minute_text, meridiem, zone_name, month_name, day_text, year_text = match.groups()
    hour = int(hour_text)
    minute = int(minute_text)
    if not 1 <= hour <= 12 or not 0 <= minute <= 59:
        raise ValueError("invalid CPI embargo time")

    if meridiem.lower() == "p" and hour != 12:
        hour += 12
    elif meridiem.lower() == "a" and hour == 12:
        hour = 0

    naive = datetime.strptime(
        f"{month_name} {day_text}, {year_text} {hour:02d}:{minute:02d}",
        "%B %d, %Y %H:%M",
    )
    zone_key = zone_name.upper()
    if zone_key == "ET":
        local = naive.replace(tzinfo=_EASTERN)
    else:
        local = naive.replace(tzinfo=_FIXED_EASTERN[zone_key])
    return local.astimezone(timezone.utc)


def parse_cpi_release(
    raw_payload: bytes,
    *,
    source_url: str,
    assets: tuple[str, ...],
) -> EventRecord:
    """Parse one official BLS CPI release page into a point-in-time event.

    V1 certifies release identity and embargo timestamp only. It intentionally
    does not interpret CPI values, revisions, surprise, or archived prose.
    """
    _validate_bls_url(source_url)
    text = _plain_text(raw_payload)
    _validate_release_identity(text)
    released_at = _parse_embargo_timestamp(text)

    stable_key = f"{SOURCE_ID}|{source_url}|{released_at.isoformat()}".encode("utf-8")
    event_id = sha256(stable_key).hexdigest()

    return EventRecord(
        event_id=event_id,
        event_type="us_cpi_release",
        region="US",
        assets=assets,
        event_time=released_at,
        published_at=released_at,
        first_market_available_at=released_at,
        source_id=SOURCE_ID,
        source_version=SOURCE_VERSION,
        raw_event_hash=hash_raw_payload(raw_payload),
    )
