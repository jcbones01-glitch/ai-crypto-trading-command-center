"""Canonical AMS-DEP full-pipeline sample construction.

This module implements the approved V1 synthetic-integrity specification.
It does not authorize empirical reads and contains no network/data acquisition.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np

from .data_ingestion import (
    NORMALIZATION_VERSION,
    PARTITIONS,
    SUPPORTED_SYMBOLS,
    TIMEFRAME,
    DatasetMetadata,
    content_hash,
    dataset_identity,
    validate_dataset,
)
from .data_interfaces import MarketBar
from .data_quality_treatment_v2 import (
    TREATMENT_PROTOCOL_VERSION,
    PartitionCertification,
    ResearchTreatmentManifest,
)
from .dependence_statistics import RESTRICTIONS, SLOTS, holm_six, primary_design
from .market_state import build_market_states
from .source_identity import source_identity

REGISTERED_TREATMENT_IDENTITIES = {
    "BTCUSDT": "1590cf8e69ed757eeb6701a218d561448beb2eb6ea09dcd0ae31d15a8f5197cf",
    "ETHUSDT": "d35bf21e309820abc88090bad29601adc1d1ea6b31dcddf0b80d510af4cf542f",
}
DEVELOPMENT_START, DEVELOPMENT_END = PARTITIONS["development"]
SOURCE_VERSION_PREFIX = "binance-public-data-spot-1h:"
ALLOWED_CERTIFICATIONS = {"VALID", "VALID WITH DOCUMENTED EXCLUSIONS"}
VOLATILITY_LABEL_MAP = {
    "VOL_LOW": "LOW",
    "VOL_NORMAL": "NORMAL",
    "VOL_HIGH": "HIGH",
}
SUPPORT_YEARS = (2017, 2018, 2019, 2020, 2021)
SUPPORT_VOLATILITY_STATES = ("VOL_LOW", "VOL_NORMAL", "VOL_HIGH")
MIN_ROWS_PER_ASSET = 5000
MIN_ROWS_PER_CELL = 200
MIN_DATES_PER_CELL = 10
REJECTION_CODES = (
    "PREVIOUS_ENDPOINT_UNAVAILABLE",
    "FORWARD_ENDPOINT_UNAVAILABLE",
    "CROSSES_CONTINUITY_BOUNDARY",
    "PREDICTOR_NOT_CERTIFIED",
    "INCOMPLETE_AMS_V1_STATE",
    "PROTECTED_PARTITION_ENDPOINT",
    "NONFINITE_RETURN",
)
_SOURCE_VERSION_RE = re.compile(r"^binance-public-data-spot-1h:([0-9a-f]{64})$")


class PipelineIntegrityError(RuntimeError):
    """Fail-closed source/sample integrity error."""


@dataclass(frozen=True)
class CertifiedDataBundle:
    """One canonical verified Development source bundle."""

    symbol: str
    bars: tuple[MarketBar, ...]
    metadata: DatasetMetadata
    manifest: ResearchTreatmentManifest
    raw_archive_paths: tuple[Path, ...]


@dataclass(frozen=True)
class PrimaryRow:
    predictor_timestamp: datetime
    availability_timestamp: datetime
    x: float
    y: float
    year: int
    volatility_state: str
    activity_state: str
    trend_state: str
    hour: int
    segment_id: int


@dataclass(frozen=True)
class RejectedRow:
    predictor_timestamp: datetime
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class PrimarySample:
    symbol: str
    rows: tuple[PrimaryRow, ...]
    rejected: tuple[RejectedRow, ...]
    loaded_timestamps: tuple[datetime, ...]
    candidate_timestamps: tuple[datetime, ...]
    accepted_timestamps: tuple[datetime, ...]
    rejected_timestamps: tuple[datetime, ...]
    segment_assignments: tuple[tuple[datetime, int], ...]
    inventory_sha256: Mapping[str, str]

    @property
    def candidate_count(self) -> int:
        return len(self.candidate_timestamps)

    @property
    def accepted_count(self) -> int:
        return len(self.accepted_timestamps)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected_timestamps)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _digest_lines(values: Iterable[str]) -> str:
    lines = list(values)
    payload = ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _timestamp_digest(values: Iterable[datetime]) -> str:
    return _digest_lines(_iso(value) for value in values)


def recompute_treatment_manifest_identity(manifest: ResearchTreatmentManifest) -> str:
    payload = json.dumps(
        manifest.to_record_without_identity(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def _development_partition(manifest: ResearchTreatmentManifest) -> PartitionCertification:
    matches = [item for item in manifest.partitions if item.partition == "development"]
    if len(matches) != 1:
        raise PipelineIntegrityError("exactly one Development partition certification required")
    return matches[0]


def _dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise PipelineIntegrityError("manifest timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _inside(timestamp: datetime, start: str, end: str) -> bool:
    return _dt(start) <= timestamp < _dt(end)


def _inside_any(timestamp: datetime, intervals) -> bool:
    return any(_inside(timestamp, value.start, value.end) for value in intervals)


def _expected_hour_grid(start: datetime, end: datetime) -> tuple[datetime, ...]:
    if end <= start:
        raise PipelineIntegrityError("certified segment must be nonempty")
    out = []
    cursor = start
    while cursor < end:
        out.append(cursor)
        cursor += timedelta(hours=1)
    return tuple(out)


def verify_certified_bundle(
    bundle: CertifiedDataBundle,
    *,
    registered_identity: str | None = None,
) -> dict:
    """Verify source, manifest, normalized bars, exclusions, and segment grids."""

    if bundle.symbol not in REGISTERED_TREATMENT_IDENTITIES:
        raise PipelineIntegrityError("unsupported AMS-DEP symbol")
    expected_manifest_identity = (
        REGISTERED_TREATMENT_IDENTITIES[bundle.symbol]
        if registered_identity is None
        else registered_identity
    )
    if registered_identity is not None and registered_identity != REGISTERED_TREATMENT_IDENTITIES[bundle.symbol]:
        # Test-only synthetic fixtures may supply a synthetic identity explicitly.
        expected_manifest_identity = registered_identity

    if not bundle.raw_archive_paths:
        raise PipelineIntegrityError("raw archive paths are required")
    actual_source_identity = source_identity(list(bundle.raw_archive_paths))

    manifest = bundle.manifest
    recomputed_manifest_identity = recompute_treatment_manifest_identity(manifest)
    if not (
        recomputed_manifest_identity
        == manifest.dataset_identity
        == expected_manifest_identity
    ):
        raise PipelineIntegrityError("treatment manifest identity mismatch")

    match = _SOURCE_VERSION_RE.fullmatch(manifest.source_version)
    if not match:
        raise PipelineIntegrityError("invalid bound source_version")
    manifest_raw_identity = match.group(1)
    if manifest_raw_identity != actual_source_identity:
        raise PipelineIntegrityError("raw archive set does not match treatment manifest")
    if bundle.metadata.source_identity != actual_source_identity:
        raise PipelineIntegrityError("metadata source identity mismatch")

    if manifest.symbol != bundle.symbol:
        raise PipelineIntegrityError("manifest symbol mismatch")
    if manifest.timeframe != TIMEFRAME:
        raise PipelineIntegrityError("manifest timeframe mismatch")
    if manifest.normalization_version != NORMALIZATION_VERSION:
        raise PipelineIntegrityError("manifest normalization version mismatch")
    if manifest.treatment_protocol_version != TREATMENT_PROTOCOL_VERSION:
        raise PipelineIntegrityError("manifest treatment version mismatch")
    if manifest.source_integrity != "SOURCE VERIFIED":
        raise PipelineIntegrityError("unverified source")
    if manifest.research_certification not in ALLOWED_CERTIFICATIONS:
        raise PipelineIntegrityError("unusable research certification")

    partition = _development_partition(manifest)
    if _dt(partition.start) != DEVELOPMENT_START or _dt(partition.end) != DEVELOPMENT_END:
        raise PipelineIntegrityError("Development boundaries mismatch")
    if partition.certification not in ALLOWED_CERTIFICATIONS:
        raise PipelineIntegrityError("unusable Development certification")

    bars = list(bundle.bars)
    if not bars:
        raise PipelineIntegrityError("empty returned bar bundle")
    if any(not (DEVELOPMENT_START <= bar.timestamp < DEVELOPMENT_END) for bar in bars):
        raise PipelineIntegrityError("bar outside frozen Development partition")

    metadata = bundle.metadata
    expected_canonical = SUPPORTED_SYMBOLS[bundle.symbol]
    expected_fields = {
        "source": "Binance Public Data",
        "source_symbol": bundle.symbol,
        "canonical_symbol": expected_canonical,
        "market": "spot",
        "timeframe": TIMEFRAME,
        "timezone": "UTC",
        "normalization_version": NORMALIZATION_VERSION,
    }
    for field, expected in expected_fields.items():
        if getattr(metadata, field) != expected:
            raise PipelineIntegrityError(f"metadata {field} mismatch")
    if metadata.row_count != len(bars):
        raise PipelineIntegrityError("metadata row_count mismatch")
    if metadata.start_timestamp != _iso(bars[0].timestamp):
        raise PipelineIntegrityError("metadata start_timestamp mismatch")
    if metadata.end_timestamp != _iso(bars[-1].timestamp):
        raise PipelineIntegrityError("metadata end_timestamp mismatch")
    if dataset_identity(bars) != metadata.dataset_id:
        raise PipelineIntegrityError("normalized dataset identity mismatch")
    if content_hash(bars) != metadata.content_hash:
        raise PipelineIntegrityError("normalized content hash mismatch")

    whole = validate_dataset(bars, bundle.symbol, metadata.timestamp_unit)
    disallowed = [issue for issue in whole.issues if issue.code != "missing_interval"]
    if disallowed:
        raise PipelineIntegrityError(
            "whole-bundle validation failed: " + ",".join(sorted({i.code for i in disallowed}))
        )

    exclusions = tuple(partition.exclusions)
    certified_segments = tuple(sorted(partition.certified_segments, key=lambda s: s.start))

    # Every observed normalized bar must be either certified or deliberately
    # excluded by the manifest. A bar in neither set is a source/manifest
    # mismatch, not a row-level exclusion.
    for bar in bars:
        if not _inside_any(bar.timestamp, certified_segments) and not _inside_any(
            bar.timestamp, exclusions
        ):
            raise PipelineIntegrityError(
                "loaded timestamp is neither certified nor documented as excluded"
            )

    for issue in whole.issues:
        if issue.timestamp is None:
            raise PipelineIntegrityError("missing_interval issue lacks timestamp")
        if not _inside_any(issue.timestamp, exclusions):
            raise PipelineIntegrityError("undocumented missing interval")
        if _inside_any(issue.timestamp, certified_segments):
            raise PipelineIntegrityError("missing interval lies inside certified segment")

    by_timestamp = {bar.timestamp: bar for bar in bars}
    if len(by_timestamp) != len(bars):
        raise PipelineIntegrityError("duplicate timestamp in normalized bundle")

    for segment in certified_segments:
        start, end = _dt(segment.start), _dt(segment.end)
        expected = _expected_hour_grid(start, end)
        actual = tuple(
            bar.timestamp for bar in bars if start <= bar.timestamp < end
        )
        if actual != expected:
            raise PipelineIntegrityError("certified segment hourly grid mismatch")
        segment_bars = [by_timestamp[timestamp] for timestamp in expected]
        segment_report = validate_dataset(
            segment_bars, bundle.symbol, metadata.timestamp_unit
        )
        if not segment_report.valid:
            raise PipelineIntegrityError("certified segment failed validate_dataset")

    missing_timestamps = tuple(
        issue.timestamp for issue in whole.issues if issue.timestamp is not None
    )
    return {
        "symbol": bundle.symbol,
        "raw_source_identity": actual_source_identity,
        "manifest_source_identity": manifest_raw_identity,
        "recomputed_manifest_identity": recomputed_manifest_identity,
        "normalized_dataset_id": metadata.dataset_id,
        "normalized_content_hash": metadata.content_hash,
        "whole_bundle_missing_intervals": len(missing_timestamps),
        "whole_bundle_missing_interval_sha256": _timestamp_digest(
            missing_timestamps
        ),
        "documented_exclusion_count": len(exclusions),
        "certified_segment_count": len(certified_segments),
    }


def _segment_for(timestamp: datetime, segments) -> int | None:
    for index, segment in enumerate(segments):
        if _inside(timestamp, segment.start, segment.end):
            return index
    return None


def build_primary_sample(
    bundle: CertifiedDataBundle,
    *,
    registered_identity: str | None = None,
) -> PrimarySample:
    """Build the only registered AMS-DEP primary sample from a verified bundle."""

    verify_certified_bundle(bundle, registered_identity=registered_identity)
    partition = _development_partition(bundle.manifest)
    segments = tuple(sorted(partition.certified_segments, key=lambda s: s.start))
    bars = tuple(bundle.bars)
    by_timestamp = {bar.timestamp: bar for bar in bars}

    states_by_timestamp = {}
    for segment in segments:
        start, end = _dt(segment.start), _dt(segment.end)
        segment_bars = [bar for bar in bars if start <= bar.timestamp < end]
        for state in build_market_states(segment_bars):
            states_by_timestamp[state.timestamp] = state

    candidates = tuple(
        bar.timestamp
        for bar in bars
        if DEVELOPMENT_START <= bar.timestamp < DEVELOPMENT_END
    )

    accepted: list[PrimaryRow] = []
    rejected: list[RejectedRow] = []

    for t in candidates:
        previous = t - timedelta(hours=1)
        forward = t + timedelta(hours=1)
        reasons: list[str] = []
        segment_id = _segment_for(t, segments)

        if segment_id is None:
            reasons.append("PREDICTOR_NOT_CERTIFIED")

        if previous < DEVELOPMENT_START or forward >= DEVELOPMENT_END:
            reasons.append("PROTECTED_PARTITION_ENDPOINT")

        previous_bar = by_timestamp.get(previous)
        current_bar = by_timestamp.get(t)
        forward_bar = by_timestamp.get(forward)

        if previous_bar is None:
            reasons.append("PREVIOUS_ENDPOINT_UNAVAILABLE")
        if forward_bar is None:
            reasons.append("FORWARD_ENDPOINT_UNAVAILABLE")

        if segment_id is not None:
            if (
                _segment_for(previous, segments) != segment_id
                or _segment_for(forward, segments) != segment_id
            ):
                reasons.append("CROSSES_CONTINUITY_BOUNDARY")

        state = states_by_timestamp.get(t)
        if state is None or not state.complete:
            reasons.append("INCOMPLETE_AMS_V1_STATE")

        x = y = None
        if current_bar is not None and previous_bar is not None and forward_bar is not None:
            try:
                x = math.log(float(current_bar.close / previous_bar.close))
                y = math.log(float(forward_bar.close / current_bar.close))
                if not math.isfinite(x) or not math.isfinite(y):
                    raise ValueError
            except (ValueError, OverflowError, ZeroDivisionError):
                reasons.append("NONFINITE_RETURN")

        if reasons:
            ordered = tuple(code for code in REJECTION_CODES if code in set(reasons))
            rejected.append(RejectedRow(t, ordered))
            continue

        assert state is not None and state.composite is not None
        assert x is not None and y is not None and segment_id is not None
        availability = t + timedelta(hours=1)
        accepted.append(
            PrimaryRow(
                predictor_timestamp=t,
                availability_timestamp=availability,
                x=x,
                y=y,
                year=availability.year,
                volatility_state=state.volatility_state,
                activity_state=state.activity_state,
                trend_state=state.trend_state,
                hour=int(t.timestamp() // 3600),
                segment_id=segment_id,
            )
        )

    accepted_timestamps = tuple(row.predictor_timestamp for row in accepted)
    rejected_timestamps = tuple(row.predictor_timestamp for row in rejected)
    assignments = tuple((row.predictor_timestamp, row.segment_id) for row in accepted)

    if len(candidates) != len(accepted) + len(rejected):
        raise PipelineIntegrityError("candidate accounting mismatch")
    if set(accepted_timestamps) & set(rejected_timestamps):
        raise PipelineIntegrityError("accepted/rejected timestamp overlap")

    inventory = {
        "loaded_normalized_source_timestamps": _timestamp_digest(bar.timestamp for bar in bars),
        "candidate_predictor_timestamps": _timestamp_digest(candidates),
        "accepted_predictor_timestamps": _timestamp_digest(accepted_timestamps),
        "rejected_predictor_timestamps": _timestamp_digest(rejected_timestamps),
        "accepted_segment_assignments": _digest_lines(
            f"{_iso(timestamp)}|{segment_id}" for timestamp, segment_id in assignments
        ),
    }

    return PrimarySample(
        symbol=bundle.symbol,
        rows=tuple(accepted),
        rejected=tuple(rejected),
        loaded_timestamps=tuple(bar.timestamp for bar in bars),
        candidate_timestamps=candidates,
        accepted_timestamps=accepted_timestamps,
        rejected_timestamps=rejected_timestamps,
        segment_assignments=assignments,
        inventory_sha256=inventory,
    )


def support_report(sample: PrimarySample) -> dict:
    cells = {}
    for year in SUPPORT_YEARS:
        for state in SUPPORT_VOLATILITY_STATES:
            rows = [
                row
                for row in sample.rows
                if row.year == year and row.volatility_state == state
            ]
            dates = {row.availability_timestamp.date().isoformat() for row in rows}
            key = f"{year}|{state}"
            cells[key] = {
                "year": year,
                "volatility_state": state,
                "rows": len(rows),
                "distinct_utc_dates": len(dates),
                "pass": len(rows) >= MIN_ROWS_PER_CELL and len(dates) >= MIN_DATES_PER_CELL,
            }
    total_pass = len(sample.rows) >= MIN_ROWS_PER_ASSET
    return {
        "total_rows": len(sample.rows),
        "minimum_rows": MIN_ROWS_PER_ASSET,
        "total_rows_pass": total_pass,
        "cells": cells,
        "pass": total_pass and all(value["pass"] for value in cells.values()),
    }


def numerical_inputs(sample: PrimarySample) -> dict:
    x = np.asarray([row.x for row in sample.rows], dtype=np.float64)
    y = np.asarray([row.y for row in sample.rows], dtype=np.float64)
    years = np.asarray([row.year for row in sample.rows])
    try:
        states = np.asarray([VOLATILITY_LABEL_MAP[row.volatility_state] for row in sample.rows])
    except KeyError as exc:
        raise PipelineIntegrityError("unknown volatility state") from exc
    hours = np.asarray([row.hour for row in sample.rows], dtype=np.int64)
    segments = np.asarray([row.segment_id for row in sample.rows], dtype=np.int64)
    design = primary_design(x, years, states)
    if design.shape != (len(sample.rows), 14):
        raise PipelineIntegrityError("unexpected primary design shape")
    if RESTRICTIONS != {
        "DEP": tuple(range(7, 14)),
        "TIME": tuple(range(8, 12)),
        "STATE": (12, 13),
    }:
        raise PipelineIntegrityError("registered restriction geometry changed")
    return {
        "x": x,
        "target": y,
        "years": years,
        "states": states,
        "hours": hours,
        "segments": segments,
        "design": design,
    }


def assemble_primary_family(raw_p_by_slot: Mapping[str, float | None]) -> list[dict]:
    if tuple(raw_p_by_slot.keys()) != SLOTS:
        raise PipelineIntegrityError("primary family must use exact registered slot order")
    return holm_six([raw_p_by_slot[slot] for slot in SLOTS])


def exact_timestamp_intersection(
    btc: PrimarySample,
    eth: PrimarySample,
) -> tuple[datetime, ...]:
    return tuple(sorted(set(btc.accepted_timestamps) & set(eth.accepted_timestamps)))


def rejection_reason_counts(sample: PrimarySample) -> dict[str, int]:
    counts = {code: 0 for code in REJECTION_CODES}
    for row in sample.rejected:
        for reason in row.reasons:
            counts[reason] += 1
    return counts
