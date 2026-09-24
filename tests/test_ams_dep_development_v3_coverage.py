from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest

from research_core.ams_dep_pipeline import (
    DEVELOPMENT_END,
    DEVELOPMENT_START,
    CertifiedDataBundle,
    PipelineIntegrityError,
    recompute_treatment_manifest_identity,
    verify_certified_bundle,
)
from research_core.ams_dep_source_coverage_v3 import (
    BOUNDARY_UNACCOUNTED_CODE,
    COVERAGE_GAP_REASON,
    EMPTY_CERTIFICATION_CODE,
    SourceCoverageV3Error,
    audit_development_source_coverage_v3,
    record_sequence_sha256,
    timestamp_vector_sha256,
)
from research_core.data_ingestion import (
    NORMALIZATION_VERSION,
    TIMEFRAME,
    make_metadata,
)
from research_core.data_interfaces import MarketBar
from research_core.data_quality_treatment_v2 import (
    TREATMENT_PROTOCOL_VERSION,
    CertifiedSegment,
    Exclusion,
    PartitionCertification,
    ResearchTreatmentManifest,
)
from research_core.source_identity import bind_source_identity, source_identity


def _iso(value):
    return value.isoformat()


def _base_manifest(
    segments,
    *,
    exclusions=(),
    anomaly_ids=("scanner-a",),
):
    certification = (
        "VALID WITH DOCUMENTED EXCLUSIONS" if exclusions else "VALID"
    )
    development = PartitionCertification(
        partition="development",
        start=DEVELOPMENT_START.isoformat(),
        end=DEVELOPMENT_END.isoformat(),
        certification=certification,
        certified_segments=tuple(segments),
        exclusions=tuple(exclusions),
    )
    return ResearchTreatmentManifest(
        source_version="unbound",
        treatment_protocol_version=TREATMENT_PROTOCOL_VERSION,
        normalization_version=NORMALIZATION_VERSION,
        symbol="BTCUSDT",
        timeframe=TIMEFRAME,
        research_start=DEVELOPMENT_START.isoformat(),
        research_end=DEVELOPMENT_END.isoformat(),
        anomaly_ids=tuple(anomaly_ids),
        affected_regions=(),
        continuity_breaks=(),
        exclusions=tuple(exclusions),
        certified_segments=tuple(segments),
        partitions=(development,),
        source_integrity="SOURCE VERIFIED",
        research_certification=certification,
        dataset_identity="base-manifest",
    )


def _segment(start, hours):
    return CertifiedSegment(
        _iso(start),
        _iso(start + timedelta(hours=hours)),
    )


def _bar(ts):
    return MarketBar(
        timestamp=ts,
        symbol="BTC/USDT",
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100"),
        volume=Decimal("1"),
    )


def test_leading_unsupported_hour_becomes_exact_gap():
    t0 = DEVELOPMENT_START
    base = _base_manifest((_segment(t0, 4),))
    observed = [t0 + timedelta(hours=i) for i in (1, 2, 3)]
    audit = audit_development_source_coverage_v3(
        "BTCUSDT", base, observed, ("BTCUSDT-1h-2017-08.zip",)
    )
    evidence = audit.evidence
    assert evidence["missing_coverage_hour_vector_exact"] == [_iso(t0)]
    assert evidence["coverage_gap_intervals_exact"][0]["start"] == _iso(t0)
    assert evidence["coverage_gap_intervals_exact"][0]["end"] == _iso(
        t0 + timedelta(hours=1)
    )
    assert evidence["accepted_first_timestamp"] == _iso(
        t0 + timedelta(hours=1)
    )
    assert evidence["no_market_bar_created_or_modified"] is True


def test_trailing_and_internal_gaps_are_exact_not_widened():
    t0 = DEVELOPMENT_START
    base = _base_manifest((_segment(t0, 6),))
    observed = [
        t0,
        t0 + timedelta(hours=1),
        t0 + timedelta(hours=3),
        t0 + timedelta(hours=4),
    ]
    audit = audit_development_source_coverage_v3(
        "BTCUSDT", base, observed, ("BTCUSDT-1h-2017-08.zip",)
    )
    missing = audit.evidence["missing_coverage_hour_vector_exact"]
    assert missing == [
        _iso(t0 + timedelta(hours=2)),
        _iso(t0 + timedelta(hours=5)),
    ]
    gaps = audit.evidence["coverage_gap_intervals_exact"]
    assert [(g["start"], g["end"]) for g in gaps] == [
        (
            _iso(t0 + timedelta(hours=2)),
            _iso(t0 + timedelta(hours=3)),
        ),
        (
            _iso(t0 + timedelta(hours=5)),
            _iso(t0 + timedelta(hours=6)),
        ),
    ]


def test_base_excluded_missing_hour_is_not_duplicated_as_v3_gap():
    t0 = DEVELOPMENT_START
    exclusion = Exclusion(
        _iso(t0 + timedelta(hours=2)),
        _iso(t0 + timedelta(hours=3)),
        ("scanner-x",),
        "base exclusion",
    )
    base = _base_manifest(
        (_segment(t0, 2), _segment(t0 + timedelta(hours=3), 2)),
        exclusions=(exclusion,),
        anomaly_ids=("scanner-x",),
    )
    observed = [
        t0,
        t0 + timedelta(hours=1),
        t0 + timedelta(hours=3),
        t0 + timedelta(hours=4),
    ]
    audit = audit_development_source_coverage_v3(
        "BTCUSDT", base, observed, ("BTCUSDT-1h-2017-08.zip",)
    )
    assert audit.evidence["missing_coverage_hour_count"] == 0
    assert audit.evidence["coverage_gap_intervals_exact"] == []
    partition = audit.final_manifest.partitions[0]
    assert partition.exclusions == (exclusion,)


def test_empty_final_certification_fails_before_canonical_verifier():
    t0 = DEVELOPMENT_START
    base = _base_manifest((_segment(t0, 2),))
    with pytest.raises(SourceCoverageV3Error) as info:
        audit_development_source_coverage_v3(
            "BTCUSDT", base, (), ("BTCUSDT-1h-2017-08.zip",)
        )
    assert info.value.failure_code == EMPTY_CERTIFICATION_CODE
    assert (
        info.value.coverage_evidence["evidence_status"]
        == "COMPLETE_COVERAGE_SET_EMPTY"
    )


def test_whole_domain_base_excluded_fails_as_empty_certification():
    exclusion = Exclusion(
        DEVELOPMENT_START.isoformat(),
        DEVELOPMENT_END.isoformat(),
        ("scanner-all",),
        "base exclusion",
    )
    base = _base_manifest(
        (),
        exclusions=(exclusion,),
        anomaly_ids=("scanner-all",),
    )
    with pytest.raises(SourceCoverageV3Error) as info:
        audit_development_source_coverage_v3(
            "BTCUSDT", base, (), ("BTCUSDT-1h-2017-08.zip",)
        )
    assert info.value.failure_code == EMPTY_CERTIFICATION_CODE


def test_coverage_ids_are_not_added_to_top_level_scanner_ids():
    t0 = DEVELOPMENT_START
    base = _base_manifest((_segment(t0, 3),), anomaly_ids=("scan-1", "scan-2"))
    audit = audit_development_source_coverage_v3(
        "BTCUSDT",
        base,
        (t0, t0 + timedelta(hours=2)),
        ("BTCUSDT-1h-2017-08.zip",),
    )
    manifest = audit.final_manifest
    assert manifest.anomaly_ids == ("scan-1", "scan-2")
    coverage_regions = [
        item for item in manifest.affected_regions
        if item.reason == COVERAGE_GAP_REASON
    ]
    coverage_exclusions = [
        item for item in manifest.exclusions
        if item.reason == COVERAGE_GAP_REASON
    ]
    coverage_breaks = [
        item for item in manifest.continuity_breaks
        if item.reason == COVERAGE_GAP_REASON
    ]
    gap_id = audit.evidence["coverage_gap_ids_exact"][0]
    assert [item.anomaly_ids for item in coverage_regions] == [(gap_id,)]
    assert [item.anomaly_ids for item in coverage_exclusions] == [(gap_id,)]
    assert [item.anomaly_ids for item in coverage_breaks] == [(gap_id,)]


def test_lossless_vectors_round_trip_and_validate_digests():
    t0 = DEVELOPMENT_START
    base = _base_manifest((_segment(t0, 5),))
    observed = (t0, t0 + timedelta(hours=2), t0 + timedelta(hours=4))
    audit = audit_development_source_coverage_v3(
        "BTCUSDT", base, observed, ("BTCUSDT-1h-2017-08.zip",)
    )
    evidence = audit.evidence
    accepted = evidence["accepted_normalized_timestamp_vector_exact"]
    missing = evidence["missing_coverage_hour_vector_exact"]
    assert timestamp_vector_sha256(tuple(accepted)) == (
        evidence["accepted_timestamp_vector_sha256"]
    )
    assert timestamp_vector_sha256(tuple(missing)) == (
        evidence["missing_coverage_hour_vector_sha256"]
    )
    assert record_sequence_sha256(
        evidence["final_certified_segments_exact"]
    ) == evidence["final_certified_segments_sha256"]


def test_adjacent_archive_boundary_has_exactly_one_record_and_is_accounted():
    boundary = DEVELOPMENT_START.replace(
        year=2017, month=9, day=1, hour=0
    )
    start = boundary - timedelta(hours=2)
    base = _base_manifest((_segment(start, 4),))
    observed = (
        boundary - timedelta(hours=1),
        boundary + timedelta(hours=1),
    )
    audit = audit_development_source_coverage_v3(
        "BTCUSDT",
        base,
        observed,
        (
            "BTCUSDT-1h-2017-08.zip",
            "BTCUSDT-1h-2017-09.zip",
        ),
    )
    records = audit.evidence["adjacent_archive_boundary_records_exact"]
    assert len(records) == 1
    record = records[0]
    assert record["left_expected_hour"] == _iso(
        boundary - timedelta(hours=1)
    )
    assert record["right_expected_hour"] == _iso(boundary)
    assert record["right"]["v3_coverage_excluded"] is True
    assert record["boundary_fully_accounted"] is True


def test_unaccounted_adjacent_archive_boundary_fails_closed():
    t0 = DEVELOPMENT_START
    base = _base_manifest((_segment(t0, 2),))
    with pytest.raises(SourceCoverageV3Error) as info:
        audit_development_source_coverage_v3(
            "BTCUSDT",
            base,
            (t0, t0 + timedelta(hours=1)),
            (
                "BTCUSDT-1h-2017-08.zip",
                "BTCUSDT-1h-2017-09.zip",
            ),
        )
    assert info.value.failure_code == BOUNDARY_UNACCOUNTED_CODE


def test_coverage_manifest_identity_is_deterministic():
    t0 = DEVELOPMENT_START
    base = _base_manifest((_segment(t0, 4),))
    observed = (t0, t0 + timedelta(hours=2), t0 + timedelta(hours=3))
    first = audit_development_source_coverage_v3(
        "BTCUSDT", base, observed, ("BTCUSDT-1h-2017-08.zip",)
    )
    second = audit_development_source_coverage_v3(
        "BTCUSDT", base, tuple(observed), ("BTCUSDT-1h-2017-08.zip",)
    )
    assert (
        first.final_manifest.to_record_without_identity()
        == second.final_manifest.to_record_without_identity()
    )
    assert (
        first.final_manifest.dataset_identity
        == second.final_manifest.dataset_identity
    )


def test_unchanged_canonical_verifier_accepts_correct_overlay_and_rejects_corruption(
    tmp_path,
):
    t0 = DEVELOPMENT_START
    raw = tmp_path / "BTCUSDT-1h-2017-08.zip"
    raw.write_bytes(b"synthetic raw identity only")
    base = bind_source_identity(
        _base_manifest((_segment(t0, 5),)),
        [raw],
    )
    bars = tuple(
        _bar(t0 + timedelta(hours=i))
        for i in (0, 1, 3, 4)
    )
    audit = audit_development_source_coverage_v3(
        "BTCUSDT", base, (bar.timestamp for bar in bars), (raw.name,)
    )
    identity = source_identity([raw])
    metadata = make_metadata(
        list(bars), "BTCUSDT", "milliseconds", source_identity=identity
    )
    bundle = CertifiedDataBundle(
        symbol="BTCUSDT",
        bars=bars,
        metadata=metadata,
        manifest=audit.final_manifest,
        raw_archive_paths=(raw,),
    )
    verify_certified_bundle(
        bundle,
        registered_identity=audit.final_manifest.dataset_identity,
    )

    bad_segment = CertifiedSegment(
        _iso(t0),
        _iso(t0 + timedelta(hours=5)),
    )
    partition = audit.final_manifest.partitions[0]
    bad_partition = replace(
        partition,
        certified_segments=(bad_segment,),
    )
    bad_manifest = replace(
        audit.final_manifest,
        certified_segments=(bad_segment,),
        partitions=(bad_partition,),
        dataset_identity="",
    )
    bad_manifest = replace(
        bad_manifest,
        dataset_identity=recompute_treatment_manifest_identity(bad_manifest),
    )
    bad_bundle = replace(bundle, manifest=bad_manifest)
    with pytest.raises(PipelineIntegrityError):
        verify_certified_bundle(
            bad_bundle,
            registered_identity=bad_manifest.dataset_identity,
        )


def test_complete_53_archive_asset_has_exactly_52_boundary_records():
    names = []
    year, month = 2017, 8
    while (year, month) <= (2021, 12):
        names.append(f"BTCUSDT-1h-{year:04d}-{month:02d}.zip")
        month += 1
        if month == 13:
            year, month = year + 1, 1
    assert len(names) == 53

    base = _base_manifest(
        (CertifiedSegment(
            DEVELOPMENT_START.isoformat(),
            DEVELOPMENT_END.isoformat(),
        ),)
    )
    observed = []
    cursor = DEVELOPMENT_START
    while cursor < DEVELOPMENT_END:
        observed.append(cursor)
        cursor += timedelta(hours=1)
    audit = audit_development_source_coverage_v3(
        "BTCUSDT", base, observed, tuple(names)
    )
    records = audit.evidence["adjacent_archive_boundary_records_exact"]
    assert len(records) == 52
    assert all(item["boundary_fully_accounted"] for item in records)


def test_boundary_failure_preserves_lossless_timestamp_evidence():
    t0 = DEVELOPMENT_START
    base = _base_manifest((_segment(t0, 2),))
    observed = (t0, t0 + timedelta(hours=1))
    with pytest.raises(SourceCoverageV3Error) as info:
        audit_development_source_coverage_v3(
            "BTCUSDT",
            base,
            observed,
            (
                "BTCUSDT-1h-2017-08.zip",
                "BTCUSDT-1h-2017-09.zip",
            ),
        )
    evidence = info.value.coverage_evidence
    assert evidence["accepted_normalized_timestamp_vector_exact"] == [
        _iso(t0), _iso(t0 + timedelta(hours=1))
    ]
    assert evidence["missing_coverage_hour_vector_exact"] == []
    assert evidence["failure_code"] == BOUNDARY_UNACCOUNTED_CODE


def test_accepted_row_inside_base_exclusion_stays_observed_but_uncertified():
    t0 = DEVELOPMENT_START
    exclusion = Exclusion(
        _iso(t0 + timedelta(hours=1)),
        _iso(t0 + timedelta(hours=2)),
        ("scanner-x",),
        "base exclusion",
    )
    base = _base_manifest(
        (_segment(t0, 1), _segment(t0 + timedelta(hours=2), 1)),
        exclusions=(exclusion,),
        anomaly_ids=("scanner-x",),
    )
    observed = (
        t0,
        t0 + timedelta(hours=1),
        t0 + timedelta(hours=2),
    )
    audit = audit_development_source_coverage_v3(
        "BTCUSDT", base, observed, ("BTCUSDT-1h-2017-08.zip",)
    )
    assert _iso(t0 + timedelta(hours=1)) in (
        audit.evidence["accepted_normalized_timestamp_vector_exact"]
    )
    final = audit.evidence["final_certified_segments_exact"]
    assert all(
        not (item["start"] <= _iso(t0 + timedelta(hours=1)) < item["end"])
        for item in final
    )
