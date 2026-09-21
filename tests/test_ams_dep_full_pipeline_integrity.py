from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import math
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
from research_core.historical_dataset import _archive_set_identity
from research_core.market_state import build_market_states
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


def test_private_archive_set_identity_cannot_substitute_authoritative_source_identity(tmp_path):
    start = datetime(2019, 1, 1, tzinfo=timezone.utc)
    bundle = _bundle(tmp_path, _bars(start, 800))
    private_identity = _archive_set_identity(list(bundle.raw_archive_paths))
    authoritative = source_identity(list(bundle.raw_archive_paths))
    assert private_identity != authoritative

    stale_manifest = replace(
        bundle.manifest,
        source_version=f"binance-public-data-spot-1h:{private_identity}",
        dataset_identity="",
    )
    stale_manifest = replace(
        stale_manifest,
        dataset_identity=recompute_treatment_manifest_identity(stale_manifest),
    )
    stale_metadata = replace(bundle.metadata, source_identity=private_identity)
    altered = replace(bundle, manifest=stale_manifest, metadata=stale_metadata)
    with pytest.raises(PipelineIntegrityError, match="raw archive set"):
        verify_certified_bundle(
            altered, registered_identity=stale_manifest.dataset_identity
        )


def test_unknown_volatility_state_hard_fails_numerical_wiring():
    t = datetime(2020, 1, 1, tzinfo=timezone.utc)
    row = PrimaryRow(
        t,
        t + timedelta(hours=1),
        0.01,
        0.02,
        2020,
        "VOL_UNKNOWN",
        "ACTIVITY_NORMAL",
        "TREND_NEUTRAL",
        int(t.timestamp() // 3600),
        0,
    )
    with pytest.raises(PipelineIntegrityError, match="unknown volatility"):
        numerical_inputs(_sample([row]))


def test_non_missing_whole_bundle_validation_issue_hard_fails(tmp_path):
    start = datetime(2019, 1, 1, tzinfo=timezone.utc)
    original = _bars(start, 800)
    bad_first = replace(original[0], symbol="WRONG/SYMBOL")
    bars = (bad_first,) + original[1:]
    bundle = _bundle(tmp_path, bars)
    with pytest.raises(PipelineIntegrityError):
        verify_certified_bundle(
            bundle, registered_identity=bundle.manifest.dataset_identity
        )


def test_loaded_bar_outside_certified_or_excluded_inventory_hard_fails(tmp_path):
    start = datetime(2019, 1, 1, tzinfo=timezone.utc)
    bars = _bars(start, 800)
    segment = CertifiedSegment(
        (start + timedelta(hours=1)).isoformat(),
        (start + timedelta(hours=800)).isoformat(),
    )
    bundle = _bundle(tmp_path, bars, segments=(segment,))
    with pytest.raises(PipelineIntegrityError, match="neither certified nor documented"):
        verify_certified_bundle(
            bundle, registered_identity=bundle.manifest.dataset_identity
        )


def test_future_bar_mutation_cannot_change_past_ams_v1_state():
    start = datetime(2019, 1, 1, tzinfo=timezone.utc)
    bars = list(_bars(start, 900))
    original = build_market_states(bars)
    last = bars[-1]
    changed_close = last.close * Decimal("2")
    bars[-1] = replace(
        last,
        open=changed_close,
        high=changed_close + Decimal("1"),
        low=changed_close - Decimal("1"),
        close=changed_close,
        volume=last.volume * Decimal("3"),
    )
    mutated = build_market_states(bars)
    assert original[800] == mutated[800]
    assert original[800].complete is True


def test_continuity_break_restarts_744_bar_warmup_and_is_never_bridged(tmp_path):
    start = datetime(2019, 1, 1, tzinfo=timezone.utc)
    full = _bars(start, 1700)
    gap = start + timedelta(hours=800)
    bars = tuple(bar for bar in full if bar.timestamp != gap)
    exclusion = Exclusion(
        gap.isoformat(),
        (gap + timedelta(hours=1)).isoformat(),
        ("registered-break",),
        "registered synthetic continuity break",
    )
    second_start = gap + timedelta(hours=1)
    segments = (
        CertifiedSegment(start.isoformat(), gap.isoformat()),
        CertifiedSegment(
            second_start.isoformat(),
            (start + timedelta(hours=1700)).isoformat(),
        ),
    )
    bundle = _bundle(tmp_path, bars, segments=segments, exclusions=(exclusion,))
    sample = build_primary_sample(
        bundle, registered_identity=bundle.manifest.dataset_identity
    )
    second_rows = [row for row in sample.rows if row.segment_id == 1]
    assert second_rows
    assert second_rows[0].predictor_timestamp == second_start + timedelta(hours=744)
    assert gap - timedelta(hours=1) not in sample.accepted_timestamps
    assert second_start not in sample.accepted_timestamps
    crossing = next(
        row for row in sample.rejected if row.predictor_timestamp == gap - timedelta(hours=1)
    )
    assert "FORWARD_ENDPOINT_UNAVAILABLE" in crossing.reasons
    assert "CROSSES_CONTINUITY_BOUNDARY" in crossing.reasons


def test_primary_return_values_use_exact_t_minus_one_t_and_t_plus_one(tmp_path):
    start = datetime(2019, 1, 1, tzinfo=timezone.utc)
    bars = _bars(start, 900)
    bundle = _bundle(tmp_path, bars)
    sample = build_primary_sample(
        bundle, registered_identity=bundle.manifest.dataset_identity
    )
    first = sample.rows[0]
    i = 744
    expected_x = math.log(float(bars[i].close / bars[i - 1].close))
    expected_y = math.log(float(bars[i + 1].close / bars[i].close))
    assert first.predictor_timestamp == bars[i].timestamp
    assert first.x == pytest.approx(expected_x)
    assert first.y == pytest.approx(expected_y)


def _support_fixture_rows():
    rows = []
    counter = 0
    for year in range(2017, 2022):
        for state_index, state in enumerate(("VOL_LOW", "VOL_NORMAL", "VOL_HIGH")):
            base = datetime(year, 2 + state_index, 1, tzinfo=timezone.utc)
            for j in range(334):
                t = base + timedelta(hours=j * 2)
                rows.append(
                    PrimaryRow(
                        t,
                        t + timedelta(hours=1),
                        0.001 + counter * 1e-8,
                        0.002,
                        year,
                        state,
                        "ACTIVITY_NORMAL",
                        "TREND_NEUTRAL",
                        int(t.timestamp() // 3600),
                        year - 2017,
                    )
                )
                counter += 1
    return rows


def test_support_fails_one_cell_below_200_even_when_total_exceeds_5000():
    rows = _support_fixture_rows()
    target = [
        row for row in rows
        if row.year == 2021 and row.volatility_state == "VOL_HIGH"
    ]
    remove = set(row.predictor_timestamp for row in target[199:])
    rows = [
        row for row in rows
        if not (
            row.year == 2021
            and row.volatility_state == "VOL_HIGH"
            and row.predictor_timestamp in remove
        )
    ]
    # Replace removed rows in a different already-sufficient cell with unique
    # 2017 timestamps so the total-row threshold still passes.
    needed = 5010 - len(rows)
    base = datetime(2017, 11, 1, tzinfo=timezone.utc)
    for j in range(needed):
        t = base + timedelta(hours=j)
        rows.append(
            PrimaryRow(
                t, t + timedelta(hours=1), .001, .002, 2017, "VOL_LOW",
                "ACTIVITY_NORMAL", "TREND_NEUTRAL",
                int(t.timestamp() // 3600), 0,
            )
        )
    report = support_report(_sample(rows))
    assert report["total_rows_pass"] is True
    assert report["cells"]["2021|VOL_HIGH"]["rows"] == 199
    assert report["cells"]["2021|VOL_HIGH"]["pass"] is False
    assert report["pass"] is False


def test_support_fails_cell_with_fewer_than_ten_dates_at_adequate_row_count():
    rows = _support_fixture_rows()
    rows = [
        row for row in rows
        if not (row.year == 2021 and row.volatility_state == "VOL_HIGH")
    ]
    base = datetime(2021, 12, 1, tzinfo=timezone.utc)
    # 200 hourly rows occupy nine UTC dates: row support passes, date support fails.
    for j in range(200):
        t = base + timedelta(hours=j)
        rows.append(
            PrimaryRow(
                t, t + timedelta(hours=1), .001, .002, 2021, "VOL_HIGH",
                "ACTIVITY_NORMAL", "TREND_NEUTRAL",
                int(t.timestamp() // 3600), 4,
            )
        )
    # Restore total >= 5000 in a different cell.
    extra = 5010 - len(rows)
    extra_base = datetime(2018, 11, 1, tzinfo=timezone.utc)
    for j in range(extra):
        t = extra_base + timedelta(hours=j)
        rows.append(
            PrimaryRow(
                t, t + timedelta(hours=1), .001, .002, 2018, "VOL_LOW",
                "ACTIVITY_NORMAL", "TREND_NEUTRAL",
                int(t.timestamp() // 3600), 1,
            )
        )
    report = support_report(_sample(rows))
    cell = report["cells"]["2021|VOL_HIGH"]
    assert cell["rows"] == 200
    assert cell["distinct_utc_dates"] == 9
    assert cell["pass"] is False
    assert report["pass"] is False


def test_registered_asynchronous_cross_asset_pattern_uses_exact_intersection():
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    offsets = range(1500)
    btc_offsets = [i for i in offsets if i % 97 != 0]
    eth_offsets = [
        i for i in offsets
        if i % 89 != 0 and not (1000 <= i < 1024)
    ]

    def rows(which):
        return [
            PrimaryRow(
                start + timedelta(hours=i),
                start + timedelta(hours=i + 1),
                .01, .02, 2020, "VOL_NORMAL", "ACTIVITY_NORMAL", "TREND_NEUTRAL",
                int((start + timedelta(hours=i)).timestamp() // 3600), 0,
            )
            for i in which
        ]

    btc = _sample(rows(btc_offsets))
    eth = _sample(rows(eth_offsets), "ETHUSDT")
    joined = exact_timestamp_intersection(btc, eth)
    expected = tuple(
        start + timedelta(hours=i)
        for i in sorted(set(btc_offsets) & set(eth_offsets))
    )
    assert joined == expected
    assert list(btc.accepted_timestamps[:50]) != list(eth.accepted_timestamps[:50])
    assert len(joined) < min(len(btc.accepted_timestamps), len(eth.accepted_timestamps))


def test_same_numerical_arrays_feed_all_three_registered_hypotheses():
    rows = []
    counter = 0
    for year in range(2017, 2022):
        for state_index, state in enumerate(("VOL_LOW", "VOL_NORMAL", "VOL_HIGH")):
            for j in range(5):
                t = datetime(year, 2 + state_index, 1, tzinfo=timezone.utc) + timedelta(hours=j)
                x = .001 * (counter + 1) + .00003 * ((counter % 7) - 3)
                y = .0007 * ((counter % 11) - 5) + .2 * x * x
                rows.append(
                    PrimaryRow(
                        t, t + timedelta(hours=1), x, y, year, state,
                        "ACTIVITY_NORMAL", "TREND_NEUTRAL",
                        int(t.timestamp() // 3600), year - 2017,
                    )
                )
                counter += 1
    wired = numerical_inputs(_sample(rows))
    for hypothesis in ("DEP", "TIME", "STATE"):
        result = engineering_fixture(
            wired["design"],
            wired["target"],
            wired["hours"],
            wired["segments"],
            hypothesis,
            draws=1,
        )
        assert result["classification"] == "ENGINEERING_ONLY_NOT_CALIBRATION"
        assert result["p_value"] is None
