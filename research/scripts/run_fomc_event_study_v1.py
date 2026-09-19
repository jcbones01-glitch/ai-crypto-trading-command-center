from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import median
from zipfile import ZipFile

from research_core.data_ingestion import (
    archive_url,
    checksum_url,
    parse_timestamp,
    verify_sha256_bytes,
)
from research_core.data_interfaces import MarketBar
from research_core.data_quality import scan_archive
from research_core.data_quality_treatment_v2 import build_manifest


UTC = timezone.utc
START = datetime(2017, 8, 17, tzinfo=UTC)
END = datetime(2022, 1, 1, tzinfo=UTC)
HORIZONS_HOURS = (1, 6, 24)
CONTROL_LAGS_DAYS = (7, 14, 21, 28)
ASSETS = ("BTCUSDT", "ETHUSDT")

ROOT = Path(__file__).resolve().parents[2]
FOMC_MANIFEST = ROOT / "research/experiments/fomc_development_manifest_v1.json"
PREREGISTRATION = ROOT / "docs/GATE2_FOMC_EVENT_STUDY_PREREGISTRATION_V1.md"

EXPECTED_FOMC_DATASET_ID = "fd5021aa2ff2f01ceaa2f5e060d08db8e0825cc27e1bde147e8eb5948ee14e11"
EXPECTED_FOMC_EVENT_COUNT = 37
EXPECTED_MARKET_DATASET_IDS = {
    "BTCUSDT": "1590cf8e69ed757eeb6701a218d561448beb2eb6ea09dcd0ae31d15a8f5197cf",
    "ETHUSDT": "d35bf21e309820abc88090bad29601adc1d1ea6b31dcddf0b80d510af4cf542f",
}
USER_AGENT = "ai-crypto-trading-command-center research/1.0"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return parsed.astimezone(UTC)


def months(start: datetime, end: datetime):
    year, month = start.year, start.month
    while (year, month) < (end.year, end.month):
        yield year, month
        month += 1
        if month == 13:
            year += 1
            month = 1


def fetch(url: str, attempts: int = 3) -> bytes:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=90) as response:
                return response.read()
        except Exception as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"failed to fetch {url}: {last_error}") from last_error


def parse_valid_bars(
    path: Path,
    symbol: str,
    valid_timestamps: set[datetime],
) -> list[MarketBar]:
    bars: list[MarketBar] = []
    with ZipFile(path) as archive:
        members = [name for name in archive.namelist() if not name.endswith("/")]
        if len(members) != 1:
            raise RuntimeError(f"unexpected archive members: {path}")
        rows = archive.read(members[0]).decode("utf-8").splitlines()

    canonical_symbol = "BTC/USDT" if symbol == "BTCUSDT" else "ETH/USDT"
    for row in csv.reader(rows):
        if not row or row[0].strip().lower() in {"open time", "timestamp"} or len(row) < 6:
            continue
        try:
            timestamp, _ = parse_timestamp(row[0])
            if timestamp not in valid_timestamps or not (START <= timestamp < END):
                continue
            values = [Decimal(value) for value in row[1:6]]
            bars.append(MarketBar(timestamp, canonical_symbol, *values))
        except (ValueError, InvalidOperation):
            continue
    return bars


def _in_break(timestamp: datetime, breaks) -> bool:
    return any(
        datetime.fromisoformat(item.start) <= timestamp < datetime.fromisoformat(item.end)
        for item in breaks
    )


def continuous_segments(bars: list[MarketBar], breaks) -> list[list[MarketBar]]:
    segments: list[list[MarketBar]] = []
    current: list[MarketBar] = []
    for bar in bars:
        if _in_break(bar.timestamp, breaks):
            if current:
                segments.append(current)
                current = []
            continue
        if current and bar.timestamp != current[-1].timestamp + timedelta(hours=1):
            segments.append(current)
            current = []
        current.append(bar)
    if current:
        segments.append(current)
    return [segment for segment in segments if segment]


def load_frozen_events(path: Path = FOMC_MANIFEST) -> tuple[dict, list[dict]]:
    payload = json.loads(path.read_text(encoding="utf-8"))

    if payload.get("validation_or_oos_accessed") is not False:
        raise RuntimeError("frozen FOMC manifest must record validation_or_oos_accessed=false")
    dataset = payload.get("event_dataset", {})
    if dataset.get("dataset_id") != EXPECTED_FOMC_DATASET_ID:
        raise RuntimeError("frozen FOMC dataset identity mismatch")
    events = payload.get("events", [])
    if len(events) != EXPECTED_FOMC_EVENT_COUNT or dataset.get("record_count") != EXPECTED_FOMC_EVENT_COUNT:
        raise RuntimeError("frozen FOMC event count mismatch")

    ids = [event["event_id"] for event in events]
    if len(set(ids)) != len(ids):
        raise RuntimeError("frozen FOMC manifest contains duplicate event IDs")

    normalized: list[dict] = []
    for event in events:
        timestamp = parse_utc(event["first_market_available_at"])
        if not START <= timestamp < END:
            raise RuntimeError("FOMC event is outside Development")
        if timestamp.minute or timestamp.second or timestamp.microsecond:
            raise RuntimeError("FOMC event is not on an exact UTC hourly boundary")
        normalized.append({**event, "timestamp": timestamp})

    normalized.sort(key=lambda item: (item["timestamp"], item["event_id"]))
    return payload, normalized


def build_segment_lookup(segments: list[list[MarketBar]]) -> dict[datetime, tuple[int, int, MarketBar]]:
    lookup: dict[datetime, tuple[int, int, MarketBar]] = {}
    for segment_index, segment in enumerate(segments):
        for position, bar in enumerate(segment):
            if bar.timestamp in lookup:
                raise RuntimeError(f"duplicate certified market timestamp: {bar.timestamp.isoformat()}")
            lookup[bar.timestamp] = (segment_index, position, bar)
    return lookup


def forward_open_return(
    lookup: dict[datetime, tuple[int, int, MarketBar]],
    timestamp: datetime,
    horizon_hours: int,
) -> tuple[bool, str | None, Decimal | None]:
    if horizon_hours not in HORIZONS_HOURS:
        raise ValueError("unregistered horizon")
    start = lookup.get(timestamp)
    if start is None:
        return False, "event/control start timestamp unavailable in certified market data", None

    end_timestamp = timestamp + timedelta(hours=horizon_hours)
    end = lookup.get(end_timestamp)
    if end is None:
        return False, "forward endpoint unavailable in certified market data", None

    start_segment, start_position, start_bar = start
    end_segment, end_position, end_bar = end
    if start_segment != end_segment or end_position - start_position != horizon_hours:
        return False, "forward interval crosses a certified continuity break", None
    if start_bar.open <= 0 or end_bar.open <= 0:
        return False, "non-positive open price", None

    return True, None, end_bar.open / start_bar.open - Decimal("1")


def is_near_fomc_event(timestamp: datetime, event_times: tuple[datetime, ...]) -> bool:
    return any(abs(timestamp - event_time) <= timedelta(hours=24) for event_time in event_times)


def control_timestamp(event_timestamp: datetime, lag_days: int) -> datetime:
    if lag_days not in CONTROL_LAGS_DAYS:
        raise ValueError("unregistered control lag")
    return event_timestamp - timedelta(days=lag_days)


def summarize_returns(values: list[Decimal]) -> dict:
    if not values:
        return {
            "eligible_observations": 0,
            "mean_signed_return": None,
            "median_signed_return": None,
            "positive_return_fraction": None,
            "mean_absolute_return": None,
            "median_absolute_return": None,
        }

    absolute = [abs(value) for value in values]
    count = Decimal(len(values))
    return {
        "eligible_observations": len(values),
        "mean_signed_return": str(sum(values, Decimal("0")) / count),
        "median_signed_return": str(median(values)),
        "positive_return_fraction": str(Decimal(sum(value > 0 for value in values)) / count),
        "mean_absolute_return": str(sum(absolute, Decimal("0")) / count),
        "median_absolute_return": str(median(absolute)),
    }


def compare_summaries(event_summary: dict, control_summary: dict) -> dict:
    if not event_summary["eligible_observations"] or not control_summary["eligible_observations"]:
        return {
            "mean_signed_return_difference": None,
            "mean_absolute_return_difference": None,
            "mean_absolute_return_ratio": None,
        }

    event_mean = Decimal(event_summary["mean_signed_return"])
    control_mean = Decimal(control_summary["mean_signed_return"])
    event_abs = Decimal(event_summary["mean_absolute_return"])
    control_abs = Decimal(control_summary["mean_absolute_return"])
    return {
        "mean_signed_return_difference": str(event_mean - control_mean),
        "mean_absolute_return_difference": str(event_abs - control_abs),
        "mean_absolute_return_ratio": str(event_abs / control_abs) if control_abs != 0 else None,
    }


def load_market_data(symbol: str, root: Path) -> tuple[object, list[list[MarketBar]]]:
    scans = []
    paths: list[Path] = []

    for year, month in months(START, END):
        url = archive_url(symbol, year, month)
        payload = fetch(url)
        checksum = fetch(checksum_url(url)).decode("utf-8")
        if not verify_sha256_bytes(payload, checksum):
            raise RuntimeError(f"checksum mismatch: {url}")

        path = root / symbol / Path(url).name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
        scans.append(scan_archive(path, symbol, True))
        paths.append(path)

    manifest = build_manifest(symbol, scans, START, END)
    if manifest.dataset_identity != EXPECTED_MARKET_DATASET_IDS[symbol]:
        raise RuntimeError(
            f"{symbol} Development dataset identity mismatch: "
            f"{manifest.dataset_identity} != {EXPECTED_MARKET_DATASET_IDS[symbol]}"
        )
    if manifest.source_integrity != "SOURCE VERIFIED":
        raise RuntimeError(f"{symbol} source integrity is not verified")

    bars: list[MarketBar] = []
    for path, scan in zip(paths, scans):
        bars.extend(parse_valid_bars(path, symbol, set(scan.valid_timestamps)))
    bars.sort(key=lambda bar: bar.timestamp)
    return manifest, continuous_segments(bars, manifest.continuity_breaks)


def run_study() -> dict:
    frozen_manifest, events = load_frozen_events()
    event_times = tuple(event["timestamp"] for event in events)

    report = {
        "study_version": "fomc-descriptive-event-study-v1",
        "github_sha": os.environ.get("GITHUB_SHA", "UNKNOWN"),
        "preregistration": {
            "path": str(PREREGISTRATION.relative_to(ROOT)),
            "sha256": sha256_file(PREREGISTRATION),
        },
        "fomc_event_manifest": {
            "path": str(FOMC_MANIFEST.relative_to(ROOT)),
            "sha256": sha256_file(FOMC_MANIFEST),
            "dataset_id": EXPECTED_FOMC_DATASET_ID,
            "record_count": EXPECTED_FOMC_EVENT_COUNT,
        },
        "development_window": [
            START.isoformat().replace("+00:00", "Z"),
            END.isoformat().replace("+00:00", "Z"),
        ],
        "validation_or_oos_accessed": False,
        "horizons_hours": list(HORIZONS_HOURS),
        "control_lags_days": list(CONTROL_LAGS_DAYS),
        "market_datasets": {},
        "results": {},
        "interpretation_boundary": "DESCRIPTIVE_ONLY_NO_STRATEGY_PROMOTION",
    }

    with tempfile.TemporaryDirectory(prefix="fomc-event-study-") as temp_dir:
        root = Path(temp_dir)

        for symbol in ASSETS:
            market_manifest, segments = load_market_data(symbol, root)
            lookup = build_segment_lookup(segments)
            report["market_datasets"][symbol] = {
                "dataset_identity": market_manifest.dataset_identity,
                "source_integrity": market_manifest.source_integrity,
                "research_certification": market_manifest.research_certification,
            }
            asset_results = {}

            for horizon in HORIZONS_HOURS:
                event_observations = []
                control_observations = []
                event_returns: list[Decimal] = []
                control_returns: list[Decimal] = []

                for event in events:
                    event_time = event["timestamp"]
                    eligible, reason, value = forward_open_return(lookup, event_time, horizon)
                    event_record = {
                        "event_id": event["event_id"],
                        "event_timestamp": event_time.isoformat().replace("+00:00", "Z"),
                        "eligible": eligible,
                        "exclusion_reason": reason,
                        "return": str(value) if value is not None else None,
                    }
                    event_observations.append(event_record)
                    if value is not None:
                        event_returns.append(value)

                    for lag_days in CONTROL_LAGS_DAYS:
                        timestamp = control_timestamp(event_time, lag_days)
                        control_reason = None
                        control_value = None
                        control_eligible = True

                        if not START <= timestamp < END:
                            control_eligible = False
                            control_reason = "control timestamp outside Development"
                        elif is_near_fomc_event(timestamp, event_times):
                            control_eligible = False
                            control_reason = "control timestamp is within 24 hours of a certified FOMC event"
                        else:
                            control_eligible, control_reason, control_value = forward_open_return(
                                lookup,
                                timestamp,
                                horizon,
                            )

                        control_record = {
                            "associated_event_id": event["event_id"],
                            "event_timestamp": event_time.isoformat().replace("+00:00", "Z"),
                            "lag_days": lag_days,
                            "control_timestamp": timestamp.isoformat().replace("+00:00", "Z"),
                            "eligible": control_eligible,
                            "exclusion_reason": control_reason,
                            "return": str(control_value) if control_value is not None else None,
                        }
                        control_observations.append(control_record)
                        if control_value is not None:
                            control_returns.append(control_value)

                event_summary = summarize_returns(event_returns)
                control_summary = summarize_returns(control_returns)
                asset_results[str(horizon)] = {
                    "event_summary": event_summary,
                    "control_summary": control_summary,
                    "comparison": compare_summaries(event_summary, control_summary),
                    "event_observations": event_observations,
                    "control_observations": control_observations,
                }

            report["results"][symbol] = asset_results

    # Preserve an explicit proof that the frozen manifest, rather than live Fed pages,
    # drove the event timestamps used by the study.
    report["fomc_event_manifest"]["source_artifact_run_id"] = frozen_manifest.get(
        "source_manifest_artifact_run_id"
    )
    report["fomc_event_manifest"]["source_artifact_id"] = frozen_manifest.get(
        "source_manifest_artifact_id"
    )
    return report


def main() -> None:
    report = run_study()
    output_dir = Path("event_intelligence_results")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "fomc_event_study_v1.json"
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print("FOMC descriptive event study evidence generated")


if __name__ == "__main__":
    main()
