from __future__ import annotations

import html
import re
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from intelligence.event_schema import EventRecord, hash_raw_payload


SOURCE_ID = "federal-reserve-board/fomc-statement"
SOURCE_VERSION = "federal-reserve-fomc-html-v1"
_REQUIRED_TITLE = "Federal Reserve issues FOMC statement"

_DATE_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
    r"(\d{1,2}),\s+(\d{4})\b"
)
_RELEASE_RE = re.compile(
    r"For\s+release\s+at\s+(\d{1,2}):(\d{2})\s*([ap])\.m\.\s*(EST|EDT)\b",
    re.IGNORECASE,
)

_FIXED_EASTERN = {
    "EST": timezone(timedelta(hours=-5), name="EST"),
    "EDT": timezone(timedelta(hours=-4), name="EDT"),
}


class _StatementLinkParser(HTMLParser):
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
        label = re.sub(r"\s+", " ", " ".join(self._parts)).strip()
        if label.lower() == _REQUIRED_TITLE.lower():
            self.matches.append(self._href)
        self._href = None
        self._parts = []


def _plain_text(raw_payload: bytes) -> str:
    if not isinstance(raw_payload, bytes):
        raise TypeError("raw_payload must be bytes")
    decoded = raw_payload.decode("utf-8", errors="strict")
    no_tags = re.sub(r"<[^>]+>", " ", decoded)
    return re.sub(r"\s+", " ", html.unescape(no_tags)).strip()


def _validate_source_url(source_url: str) -> None:
    parsed = urlparse(source_url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or hostname not in {"federalreserve.gov", "www.federalreserve.gov"}:
        raise ValueError("source_url must be an HTTPS Federal Reserve Board URL")


def discover_fomc_statement_urls(raw_index_payload: bytes, *, index_url: str) -> tuple[str, ...]:
    """Discover only links explicitly titled as Federal Reserve FOMC statements."""
    _validate_source_url(index_url)
    if not isinstance(raw_index_payload, bytes):
        raise TypeError("raw_index_payload must be bytes")
    parser = _StatementLinkParser()
    parser.feed(raw_index_payload.decode("utf-8", errors="strict"))

    urls: set[str] = set()
    for href in parser.matches:
        url = urljoin(index_url, href)
        _validate_source_url(url)
        urls.add(url)
    return tuple(sorted(urls))


def _validate_statement_identity(text: str) -> None:
    if _REQUIRED_TITLE.lower() not in text.lower():
        raise ValueError("page is not identified as 'Federal Reserve issues FOMC statement'")


def _parse_release_timestamp(text: str) -> datetime:
    date_match = _DATE_RE.search(text)
    if not date_match:
        raise ValueError("FOMC statement date not found")

    release_match = _RELEASE_RE.search(text)
    if not release_match:
        raise ValueError("explicit FOMC 'For release at' timestamp with EST/EDT not found")

    month_name, day_text, year_text = date_match.groups()
    hour_text, minute_text, meridiem, zone_name = release_match.groups()

    hour = int(hour_text)
    minute = int(minute_text)
    if not 1 <= hour <= 12 or not 0 <= minute <= 59:
        raise ValueError("invalid FOMC release time")

    if meridiem.lower() == "p" and hour != 12:
        hour += 12
    elif meridiem.lower() == "a" and hour == 12:
        hour = 0

    local_date = datetime.strptime(
        f"{month_name} {day_text}, {year_text}",
        "%B %d, %Y",
    )
    local = local_date.replace(
        hour=hour,
        minute=minute,
        tzinfo=_FIXED_EASTERN[zone_name.upper()],
    )
    return local.astimezone(timezone.utc)


def parse_fomc_statement(
    raw_payload: bytes,
    *,
    source_url: str,
    assets: tuple[str, ...],
) -> EventRecord:
    """Parse one official Federal Reserve FOMC statement page.

    Accepted pages must explicitly identify themselves as an FOMC statement and
    expose an EST/EDT "For release at" timestamp. The official release timestamp
    controls publication and first market availability. Ambiguous pages fail
    closed instead of being inferred from URL dates or crawl metadata.
    """
    _validate_source_url(source_url)
    text = _plain_text(raw_payload)
    _validate_statement_identity(text)
    released_at = _parse_release_timestamp(text)

    stable_key = f"{SOURCE_ID}|{source_url}|{released_at.isoformat()}".encode("utf-8")
    event_id = sha256(stable_key).hexdigest()

    return EventRecord(
        event_id=event_id,
        event_type="central_bank_policy_statement",
        region="US",
        assets=assets,
        event_time=released_at,
        published_at=released_at,
        first_market_available_at=released_at,
        source_id=SOURCE_ID,
        source_version=SOURCE_VERSION,
        raw_event_hash=hash_raw_payload(raw_payload),
    )
