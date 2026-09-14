from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from research_core.data_quality import ArchiveQualityReport, DataQualityEvent, scan_archive
from research_core.data_quality_treatment import (
    TREATMENT_PROTOCOL_VERSION,
    CertifiedSegment,
    ContinuityBreak,
    build_affected_regions,
    build_manifest,
    common_certification,
    common_certified_intervals,
    lookback_eligible,
    return_eligible,
)

UTC = timezone.utc


def ts(hour: int, minute: int = 0) -> str:
    return datetime(2024, 1, 1, hour, minute, tzinfo=UTC).isoformat()


def event(parsed: str, kind: str = "NON_ALIGNED_TIMESTAMP", row: int = 1) -> DataQualityEvent:
    return DataQualityEvent("BTCUSDT", "1h", "BTCUSDT-1h-2024-01.zip", "BTCUSDT-1h-2024-01.csv", row,
                            "1704099600000", parsed, kind, "test rule", "ERROR", "test provenance", "test anomaly")


def report(events=(), valid=(), checksum=True, symbol="BTCUSDT"):
    return ArchiveQualityReport(symbol, f"{symbol}-1h-2024-01.zip", len(valid), tuple(events), checksum, tuple(datetime.fromisoformat(x) for x in valid))


def test_non_aligned_timestamp_is_excluded_without_repair():
    reports = [report([event(ts(9, 28))], [ts(8), ts(10), ts(11)])]
    regions = build_affected_regions(reports)
    assert regions[0].start == ts(9)
    assert regions[0].end == ts(10)
    assert ts(9, 28) not in (regions[0].start, regions[0].end)


def test_shifted_sequence_requires_two_clean_bars_to_restore():
    events = [event(ts(hour, 28), row=hour) for hour in range(9, 13)]
    reports = [report(events, [ts(8), ts(13), ts(14)])]
    regions = build_affected_regions(reports)
    assert regions == (regions[0],)
    assert regions[0].start == ts(9)
    assert regions[0].end == ts(13)


def test_missing_interval_is_a_continuity_break_not_a_return():
    br = ContinuityBreak(ts(10), ts(11), ("a",), "missing hourly interval")
    assert not return_eligible(datetime.fromisoformat(ts(9)), datetime.fromisoformat(ts(11)), (br,))
    assert not return_eligible(datetime.fromisoformat(ts(10)), datetime.fromisoformat(ts(11)), (br,))
    assert return_eligible(datetime.fromisoformat(ts(8)), datetime.fromisoformat(ts(9)), (br,))


def test_duplicate_and_out_of_order_are_linked_to_regions():
    events = [event(ts(10), "DUPLICATE_TIMESTAMP", 2), event(ts(12), "OUT_OF_ORDER_TIMESTAMP", 4)]
    reports = [report(events, [ts(8), ts(9), ts(10), ts(11), ts(12), ts(13)])]
    regions = build_affected_regions(reports)
    assert regions[0].start == ts(10)
    assert regions[0].end == ts(11)
    assert regions[1].start == ts(12)


def test_invalid_ohlc_and_volume_are_eligible_for_region_linkage():
    events = [event(ts(10), "INVALID_OHLC"), event(ts(12), "INVALID_VOLUME")]
    reports = [report(events, [ts(8), ts(9), ts(11), ts(13), ts(14)])]
    regions = build_affected_regions(reports)
    assert regions[0].start == ts(10)
    assert regions[1].start == ts(12)


def test_schema_error_without_timestamp_does_not_invent_interval():
    e = DataQualityEvent("BTCUSDT", "1h", "a.zip", "a.csv", 4, "bad", None, "SCHEMA_ERROR", "schema", "ERROR", "test", "bad row")
    manifest = build_manifest("BTCUSDT", [report([e], [ts(0), ts(1), ts(2)])])
    assert manifest.affected_regions == ()
    assert manifest.research_certification == "VALID"
    assert manifest.anomaly_ids


def test_checksum_failure_is_source_unverified():
    manifest = build_manifest("BTCUSDT", [report([], [ts(0), ts(1)], checksum=False)])
    assert manifest.source_integrity == "SOURCE UNVERIFIED"
    assert manifest.research_certification == "UNVERIFIED"


def test_exclusion_preserves_anomaly_provenance():
    e = event(ts(10))
    manifest = build_manifest("BTCUSDT", [report([e], [ts(8), ts(9), ts(11), ts(12)])])
    assert manifest.exclusions
    assert manifest.exclusions[0].anomaly_ids == manifest.affected_regions[0].anomaly_ids
    assert manifest.anomaly_ids[0] == manifest.exclusions[0].anomaly_ids[0]


def test_segmentation_creates_two_continuous_segments():
    e = event(ts(10))
    manifest = build_manifest("BTCUSDT", [report([e], [ts(8), ts(9), ts(11), ts(12)])], datetime.fromisoformat(ts(8)), datetime.fromisoformat(ts(13)))
    assert manifest.certified_segments == (CertifiedSegment(ts(8), ts(10)), CertifiedSegment(ts(11), ts(13)))


def test_twenty_bar_lookback_fails_across_break_and_recovers_after_warmup():
    start = datetime(2024, 1, 1, tzinfo=UTC)
    timestamps = [start + timedelta(hours=i) for i in range(40)]
    br = ContinuityBreak((start + timedelta(hours=10)).isoformat(), (start + timedelta(hours=11)).isoformat(), ("x",), "break")
    assert not lookback_eligible(timestamps, start + timedelta(hours=20), 20, start, start + timedelta(hours=40), (br,))
    assert lookback_eligible(timestamps, start + timedelta(hours=30), 20, start + timedelta(hours=11), start + timedelta(hours=40), (br,))


def test_equivalent_input_is_byte_deterministic():
    e = event(ts(10))
    reports = [report([e], [ts(8), ts(9), ts(11), ts(12)])]
    a = build_manifest("BTCUSDT", reports)
    b = build_manifest("BTCUSDT", reports)
    assert a.to_record_without_identity() == b.to_record_without_identity()
    assert a.dataset_identity == b.dataset_identity
    assert a.treatment_protocol_version == TREATMENT_PROTOCOL_VERSION


def test_common_dataset_is_intersection_not_union():
    btc = build_manifest("BTCUSDT", [], datetime.fromisoformat(ts(0)), datetime.fromisoformat(ts(20)))
    eth = build_manifest("ETHUSDT", [report([event(ts(10))], [ts(8), ts(9), ts(11), ts(12)], symbol="ETHUSDT")], datetime.fromisoformat(ts(0)), datetime.fromisoformat(ts(20)))
    common = common_certified_intervals(btc, eth)
    assert common
    assert all(segment.end <= ts(10) or segment.start >= ts(11) for segment in common)
    assert common_certification(btc, eth) == "VALID WITH DOCUMENTED EXCLUSIONS"


def test_partition_boundaries_are_not_moved():
    manifest = build_manifest("BTCUSDT", [report([event("2021-12-31T23:30:00+00:00")], ["2021-12-31T22:00:00+00:00", "2022-01-01T00:00:00+00:00", "2022-01-01T01:00:00+00:00"])])
    by_name = {p.partition: p for p in manifest.partitions}
    assert by_name["development"].start == "2017-08-17T00:00:00+00:00"
    assert by_name["development"].end == "2022-01-01T00:00:00+00:00"
    assert by_name["validation"].start == "2022-01-01T00:00:00+00:00"
    assert by_name["validation"].end == "2024-01-01T00:00:00+00:00"
    assert by_name["oos"].start == "2024-01-01T00:00:00+00:00"
    assert by_name["oos"].end == "2026-01-01T00:00:00+00:00"


def test_oos_boundary_is_locked():
    manifest = build_manifest("BTCUSDT", [], datetime.fromisoformat("2024-01-01T00:00:00+00:00"), datetime.fromisoformat("2026-01-01T00:00:00+00:00"))
    assert manifest.research_start == "2024-01-01T00:00:00+00:00"
    assert manifest.research_end == "2026-01-01T00:00:00+00:00"


def test_source_row_anomaly_fixture_is_preserved_by_scanner(tmp_path: Path):
    path = tmp_path / "BTCUSDT-1h-2024-01.zip"
    member = "BTCUSDT-1h-2024-01.csv"
    rows = "\n".join([
        "1704067200000,100,101,99,100,1",
        "1704072494789,100,101,99,100,1",
        "1704074400000,100,101,99,100,1",
    ])
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr(member, rows)
    report = scan_archive(path, "BTCUSDT")
    assert report.rows_processed == 3
    assert any(e.anomaly_type == "NON_ALIGNED_TIMESTAMP" for e in report.events)
    assert report.valid_timestamps[0].isoformat() == "2024-01-01T00:00:00+00:00"
