from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import numpy as np
import pytest

from research_core.ams_dep_pipeline import (
    DEVELOPMENT_END,
    DEVELOPMENT_START,
    CertifiedDataBundle,
    PipelineIntegrityError,
    PrimaryRow,
    PrimarySample,
    assemble_primary_family,
    build_primary_sample,
    exact_timestamp_intersection,
    numerical_inputs,
    recompute_treatment_manifest_identity,
    support_report,
    verify_certified_bundle,
)
from research_core.data_ingestion import make_metadata
from research_core.data_interfaces import MarketBar
from research_core.data_quality_treatment_v2 import (
    CertifiedSegment,
    Exclusion,
    PartitionCertification,
    ResearchTreatmentManifest,
)
from research_core.dependence_statistics import SLOTS
from research_core.dependent_wild_bootstrap_v2 import engineering_fixture
from research_core.source_identity import source_identity


def _bars(start: datetime, count: int, symbol: str = "BTCUSDT") -> tuple[MarketBar, ...]:
    canonical = "BTC/USDT" if symbol == "BTCUSDT" else "ETH/USDT"
    out = []
    for i in range(count):
        t = start + timedelta(hours=i)
        # Deterministic nonconstant price/volume path.
        close = Decimal("100") + Decimal(i) / Decimal("20") + Decimal((i % 17) - 8) / Decimal("50")
        open_ = close - Decimal("0.03")
        high = close + Decimal("0.10")
        low = close - Decimal("0.10")
        volume = Decimal("1000") + Decimal((i * 37) % 211)
        out.append(MarketBar(t, canonical, open_, high, low, close, volume))
    return tuple(out)


def _manifest(
    raw_identity: str,
    *,
    symbol: str,
    segments: tuple[CertifiedSegment, ...],
    exclusions: tuple[Exclusion, ...] = (),
) -> ResearchTreatmentManifest:
    certification = "VALID" if not exclusions else "VALID WITH DOCUMENTED EXCLUSIONS"
    partition = PartitionCertification(
        "development",
        DEVELOPMENT_START.isoformat(),
        DEVELOPMENT_END.isoformat(),
        certification,
        segments,
        exclusions,
    )
    manifest = ResearchTreatmentManifest(
        source_version=f"binance-public-data-spot-1h:{raw_identity}",
        treatment_protocol_version="gate1a-v1",
        normalization_version="gate1-v1",
        symbol=symbol,
        timeframe="1h",
        research_start=DEVELOPMENT_START.isoformat(),
        research_end=DEVELOPMENT_END.isoformat(),
        anomaly_ids=(),
        affected_regions=(),
        continuity_breaks=(),
        exclusions=exclusions,
        certified_segments=segments,
        partitions=(partition,),
        source_integrity="SOURCE VERIFIED",
        research_certification=certification,
        dataset_identity="",
    )
    return replace(
        manifest,
        dataset_identity=recompute_treatment_manifest_identity(manifest),
    )


def _bundle(
    tmp_path: Path,
    bars: tuple[MarketBar, ...],
    *,
    symbol: str = "BTCUSDT",
    segments: tuple[CertifiedSegment, ...] | None = None,
    exclusions: tuple[Exclusion, ...] = (),
) -> CertifiedDataBundle:
    raw = tmp_path / f"{symbol}-synthetic.zip"
    raw.write_bytes(b"synthetic raw archive fixture")
    raw_id = source_identity([raw])
    if segments is None:
        segments = (
            CertifiedSegment(
                bars[0].timestamp.isoformat(),
                (bars[-1].timestamp + timedelta(hours=1)).isoformat(),
            ),
        )
    manifest = _manifest(raw_id, symbol=symbol, segments=segments, exclusions=exclusions)
    metadata = make_metadata(list(bars), symbol, "milliseconds", source_identity=raw_id)
    return CertifiedDataBundle(symbol, bars, metadata, manifest, (raw,))


def _sample(rows: list[PrimaryRow], symbol: str = "BTCUSDT") -> PrimarySample:
    timestamps = tuple(row.predictor_timestamp for row in rows)
    assignments = tuple((row.predictor_timestamp, row.segment_id) for row in rows)
    return PrimarySample(
        symbol=symbol,
        rows=tuple(rows),
        rejected=(),
        loaded_timestamps=timestamps,
        candidate_timestamps=timestamps,
        accepted_timestamps=timestamps,
        rejected_timestamps=(),
        segment_assignments=assignments,
        inventory_sha256={},
    )


def test_manifest_identity_is_recomputed_and_stale_content_fails(tmp_path):
    start = datetime(2019, 1, 1, tzinfo=timezone.utc)
    bars = _bars(start, 800)
    bundle = _bundle(tmp_path, bars)
    identity = bundle.manifest.dataset_identity
    verify_certified_bundle(bundle, registered_identity=identity)

    changed_segment = CertifiedSegment(start.isoformat(), (start + timedelta(hours=799)).isoformat())
    partition = replace(bundle.manifest.partitions[0], certified_segments=(changed_segment,))
    stale = replace(
        bundle.manifest,
        certified_segments=(changed_segment,),
        partitions=(partition,),
        dataset_identity=identity,
    )
    with pytest.raises(PipelineIntegrityError, match="manifest identity"):
        verify_certified_bundle(replace(bundle, manifest=stale), registered_identity=identity)


def test_altered_raw_archive_bytes_fail_before_pipeline(tmp_path):
    start = datetime(2019, 1, 1, tzinfo=timezone.utc)
    bundle = _bundle(tmp_path, _bars(start, 800))
    identity = bundle.manifest.dataset_identity
    verify_certified_bundle(bundle, registered_identity=identity)
    bundle.raw_archive_paths[0].write_bytes(b"altered archive bytes")
    with pytest.raises(PipelineIntegrityError, match="raw archive set"):
        verify_certified_bundle(bundle, registered_identity=identity)


def test_missing_hour_inside_certified_segment_hard_fails(tmp_path):
    start = datetime(2019, 1, 1, tzinfo=timezone.utc)
    full = _bars(start, 800)
    bars = full[:400] + full[401:]
    segment = CertifiedSegment(start.isoformat(), (start + timedelta(hours=800)).isoformat())
    bundle = _bundle(tmp_path, bars, segments=(segment,))
    with pytest.raises(PipelineIntegrityError):
        verify_certified_bundle(bundle, registered_identity=bundle.manifest.dataset_identity)


def test_documented_gap_is_allowed_only_between_clean_segments(tmp_path):
    start = datetime(2019, 1, 1, tzinfo=timezone.utc)
    full = _bars(start, 1600)
    missing = start + timedelta(hours=800)
    bars = tuple(bar for bar in full if bar.timestamp != missing)
    exclusion = Exclusion(
        missing.isoformat(),
        (missing + timedelta(hours=1)).isoformat(),
        ("synthetic-gap",),
        "synthetic documented exclusion",
    )
    segments = (
        CertifiedSegment(start.isoformat(), missing.isoformat()),
        CertifiedSegment(
            (missing + timedelta(hours=1)).isoformat(),
            (start + timedelta(hours=1600)).isoformat(),
        ),
    )
    bundle = _bundle(tmp_path, bars, segments=segments, exclusions=(exclusion,))
    result = verify_certified_bundle(
        bundle, registered_identity=bundle.manifest.dataset_identity
    )
    assert result["whole_bundle_missing_intervals"] == 1
    sample = build_primary_sample(bundle, registered_identity=bundle.manifest.dataset_identity)
    assert sample.candidate_count == len(bars)
    assert sample.candidate_count == sample.accepted_count + sample.rejected_count
    assert all(row.segment_id in (0, 1) for row in sample.rows)


def test_ams_v1_warmup_and_row_timing_use_t_state_and_t_plus_one_year(tmp_path):
    start = datetime(2019, 1, 1, tzinfo=timezone.utc)
    bundle = _bundle(tmp_path, _bars(start, 900))
    sample = build_primary_sample(bundle, registered_identity=bundle.manifest.dataset_identity)
    assert sample.rows
    assert sample.rows[0].predictor_timestamp == start + timedelta(hours=744)
    first = sample.rows[0]
    assert first.availability_timestamp == first.predictor_timestamp + timedelta(hours=1)
    assert first.year == first.availability_timestamp.year
    assert first.hour == int(first.predictor_timestamp.timestamp() // 3600)


def test_development_end_forward_endpoint_is_never_accepted(tmp_path):
    start = DEVELOPMENT_END - timedelta(hours=900)
    bundle = _bundle(tmp_path, _bars(start, 900))
    sample = build_primary_sample(bundle, registered_identity=bundle.manifest.dataset_identity)
    final = next(row for row in sample.rejected if row.predictor_timestamp == DEVELOPMENT_END - timedelta(hours=1))
    assert "PROTECTED_PARTITION_ENDPOINT" in final.reasons
    assert DEVELOPMENT_END - timedelta(hours=1) not in sample.accepted_timestamps


def test_support_report_enforces_all_fifteen_cells_and_total():
    rows = []
    base = datetime(2017, 1, 1, tzinfo=timezone.utc)
    i = 0
    for year in range(2017, 2022):
        for state in ("VOL_LOW", "VOL_NORMAL", "VOL_HIGH"):
            for j in range(334):
                t = datetime(year, 1, 1, tzinfo=timezone.utc) + timedelta(hours=j * 2)
                rows.append(
                    PrimaryRow(t, t + timedelta(hours=1), 0.001 + i * 1e-8, 0.002, year,
                               state, "ACTIVITY_NORMAL", "TREND_NEUTRAL",
                               int(t.timestamp() // 3600), year - 2017)
                )
                i += 1
    report = support_report(_sample(rows))
    assert report["total_rows"] == 5010
    assert len(report["cells"]) == 15
    assert report["pass"] is True

    reduced = _sample(rows[:-20])
    assert support_report(reduced)["pass"] is False


def test_exact_timestamp_join_is_set_intersection_not_row_index():
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    btc_rows = [
        PrimaryRow(start + timedelta(hours=i), start + timedelta(hours=i + 1), .1, .2, 2020,
                   "VOL_NORMAL", "ACTIVITY_NORMAL", "TREND_NEUTRAL",
                   int((start + timedelta(hours=i)).timestamp() // 3600), 0)
        for i in (0, 1, 3, 4)
    ]
    eth_rows = [
        PrimaryRow(start + timedelta(hours=i), start + timedelta(hours=i + 1), .1, .2, 2020,
                   "VOL_NORMAL", "ACTIVITY_NORMAL", "TREND_NEUTRAL",
                   int((start + timedelta(hours=i)).timestamp() // 3600), 0)
        for i in (0, 2, 3, 4)
    ]
    joined = exact_timestamp_intersection(_sample(btc_rows), _sample(eth_rows, "ETHUSDT"))
    assert joined == (
        start,
        start + timedelta(hours=3),
        start + timedelta(hours=4),
    )


def test_numerical_wiring_preserves_epoch_hours_segments_and_engineering_only():
    rows = []
    i = 0
    states = ("VOL_LOW", "VOL_NORMAL", "VOL_HIGH")
    for year in range(2017, 2022):
        for sidx, state in enumerate(states):
            for j in range(5):
                t = datetime(year, 2 + sidx, 1, tzinfo=timezone.utc) + timedelta(hours=j)
                x = 0.001 * (i + 1) + 0.00003 * ((i % 7) - 3)
                y = 0.0007 * ((i % 11) - 5) + 0.2 * x * x
                rows.append(
                    PrimaryRow(
                        t, t + timedelta(hours=1), x, y, year, state,
                        "ACTIVITY_NORMAL", "TREND_NEUTRAL",
                        int(t.timestamp() // 3600), year - 2017,
                    )
                )
                i += 1
    sample = _sample(rows)
    wired = numerical_inputs(sample)
    assert wired["design"].shape == (75, 14)
    assert np.array_equal(wired["hours"], np.array([row.hour for row in rows], dtype=np.int64))
    assert np.array_equal(wired["segments"], np.array([row.segment_id for row in rows], dtype=np.int64))

    result = engineering_fixture(
        wired["design"], wired["target"], wired["hours"], wired["segments"], "DEP", draws=2
    )
    assert result["classification"] == "ENGINEERING_ONLY_NOT_CALIBRATION"
    assert result["p_value"] is None


def test_holm_family_keeps_exact_six_slots_and_unavailable_entries():
    raw = {
        "BTC_DEP": 0.01,
        "BTC_TIME": None,
        "BTC_STATE": 0.20,
        "ETH_DEP": 0.02,
        "ETH_TIME": 0.50,
        "ETH_STATE": 0.03,
    }
    result = assemble_primary_family(raw)
    assert tuple(item["slot"] for item in result) == SLOTS
    assert result[1]["available"] is False
    assert result[1]["calculation_p"] == 1.0
    assert len(result) == 6
