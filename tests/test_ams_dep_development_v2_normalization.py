from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

import research_core.ams_dep_treatment_aware_normalization_v2 as norm
from research_core.ams_dep_treatment_aware_normalization_v2 import (
    TreatmentAwareNormalizationError,
    asset_aggregate_sha256,
    normalize_archive_with_treatment,
    normalize_development_archives,
)
from research_core.data_quality import (
    ArchiveQualityReport,
    DataQualityEvent,
    scan_archive,
)
from research_core.data_quality_treatment_v2 import build_manifest


def _ts(hour: int, minute: int = 0) -> str:
    dt = datetime(2017, 8, 17, hour, minute, tzinfo=timezone.utc)
    return str(int(dt.timestamp() * 1000))


def _row(ts: str, *, o="100", h="101", l="99", c="100", v="10"):
    return [ts, o, h, l, c, v, "0", "0", "0", "0", "0", "0"]


def _write_zip(tmp_path: Path, filename: str, rows: list[list[str]]) -> Path:
    symbol = filename.split("-")[0]
    csv_name = filename.removesuffix(".zip") + ".csv"
    path = tmp_path / filename
    payload = "\n".join(",".join(row) for row in rows) + "\n"
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(csv_name, payload)
    return path


def _manifest(symbol: str, reports):
    return build_manifest(
        symbol,
        list(reports),
        research_start=datetime(2017, 8, 17, tzinfo=timezone.utc),
        research_end=datetime(2022, 1, 1, tzinfo=timezone.utc),
    )


def test_non_aligned_row_is_rejected_not_repaired(tmp_path):
    path = _write_zip(
        tmp_path,
        "BTCUSDT-1h-2017-08.zip",
        [_row(_ts(0)), _row(_ts(1, 28)), _row(_ts(2))],
    )
    report = scan_archive(path, "BTCUSDT", checksum_verified=True)
    assert [e.anomaly_type for e in report.events if e.row == 2] == [
        "NON_ALIGNED_TIMESTAMP"
    ]
    manifest = _manifest("BTCUSDT", [report])
    result = normalize_development_archives(
        "BTCUSDT", [path], [report], manifest
    )
    assert [bar.timestamp.hour for bar in result.bars] == [0, 2]
    account = result.archive_accounting[0]
    assert account.raw_data_rows == 3
    assert account.normalized_accepted_raw_rows == 2
    assert account.explicitly_rejected_raw_rows == 1
    rejected = account.rejected_raw_rows[0]
    assert rejected.physical_row_number == 2
    assert rejected.raw_timestamp == _ts(1, 28)
    assert rejected.sorted_anomaly_types == ("NON_ALIGNED_TIMESTAMP",)


def test_valid_row_inside_broader_exclusion_is_still_normalized(tmp_path):
    path = _write_zip(
        tmp_path,
        "BTCUSDT-1h-2017-08.zip",
        [_row(_ts(0)), _row(_ts(1, 28)), _row(_ts(2)), _row(_ts(3))],
    )
    report = scan_archive(path, "BTCUSDT", checksum_verified=True)
    manifest = _manifest("BTCUSDT", [report])
    result = normalize_development_archives(
        "BTCUSDT", [path], [report], manifest
    )
    # The anomalous 01:28 row is dropped, but later valid source rows are not
    # deleted merely because treatment may exclude a wider canonical region.
    assert [bar.timestamp.hour for bar in result.bars] == [0, 2, 3]


@pytest.mark.parametrize(
    "rows, expected_type",
    [
        (
            [_row(_ts(0)), _row(_ts(1), o="105", h="101", l="99", c="100")],
            "INVALID_OHLC",
        ),
        (
            [_row(_ts(0)), _row(_ts(1), v="-1")],
            "INVALID_VOLUME",
        ),
        (
            [_row(_ts(0)), _row(_ts(0))],
            "DUPLICATE_TIMESTAMP",
        ),
        (
            [_row(_ts(1)), _row(_ts(0))],
            "OUT_OF_ORDER_TIMESTAMP",
        ),
    ],
)
def test_generalized_localized_anomaly_rows_are_rejected(
    tmp_path, rows, expected_type
):
    path = _write_zip(tmp_path, "BTCUSDT-1h-2017-08.zip", rows)
    report = scan_archive(path, "BTCUSDT", checksum_verified=True)
    assert expected_type in {event.anomaly_type for event in report.events}
    manifest = _manifest("BTCUSDT", [report])
    result = normalize_development_archives(
        "BTCUSDT", [path], [report], manifest
    )
    assert result.aggregate_accounting["explicitly_rejected_raw_rows"] >= 1
    assert any(
        expected_type in rejected.sorted_anomaly_types
        for rejected in result.archive_accounting[0].rejected_raw_rows
    )


def test_unlocalized_schema_event_is_fatal(tmp_path):
    path = _write_zip(
        tmp_path,
        "BTCUSDT-1h-2017-08.zip",
        [["timestamp", "open", "high", "low", "close", "volume"]],
    )
    report = scan_archive(path, "BTCUSDT", checksum_verified=True)
    assert report.events[0].parsed_timestamp is None
    manifest = _manifest("BTCUSDT", [report])
    with pytest.raises(
        TreatmentAwareNormalizationError,
        match="unlocalized scanner event",
    ):
        normalize_development_archives(
            "BTCUSDT", [path], [report], manifest
        )


def test_scanner_normalizer_mismatch_hard_fails(tmp_path):
    path = _write_zip(
        tmp_path,
        "BTCUSDT-1h-2017-08.zip",
        [_row(_ts(1, 28))],
    )
    # Deliberately lie about scanner output: zero events on a bad row.
    report = ArchiveQualityReport(
        symbol="BTCUSDT",
        archive=path.name,
        rows_processed=1,
        events=(),
        checksum_verified=True,
        valid_timestamps=(),
    )
    manifest = _manifest("BTCUSDT", [report])
    with pytest.raises(
        TreatmentAwareNormalizationError,
        match="scanner/normalizer mismatch",
    ):
        normalize_development_archives(
            "BTCUSDT", [path], [report], manifest
        )


def test_cross_archive_row_number_collision_cannot_cross_reject(tmp_path):
    a = _write_zip(
        tmp_path,
        "BTCUSDT-1h-2017-08.zip",
        [_row(_ts(0)), _row(_ts(1, 28))],
    )
    b = _write_zip(
        tmp_path,
        "BTCUSDT-1h-2017-09.zip",
        [_row(_ts(2)), _row(_ts(3))],
    )
    ra = scan_archive(a, "BTCUSDT", checksum_verified=True)
    rb = scan_archive(b, "BTCUSDT", checksum_verified=True)
    assert any(event.row == 2 for event in ra.events)
    assert not any(event.row == 2 for event in rb.events)
    manifest = _manifest("BTCUSDT", [ra, rb])
    result = normalize_development_archives(
        "BTCUSDT", [a, b], [ra, rb], manifest
    )
    by_file = {item.filename: item for item in result.archive_accounting}
    assert by_file[a.name].explicitly_rejected_raw_rows == 1
    assert by_file[b.name].explicitly_rejected_raw_rows == 0


def test_mismatched_event_archive_identity_hard_fails(tmp_path):
    path = _write_zip(
        tmp_path,
        "BTCUSDT-1h-2017-08.zip",
        [_row(_ts(0))],
    )
    bad = DataQualityEvent(
        symbol="BTCUSDT",
        timeframe="1h",
        archive="BTCUSDT-1h-2017-09.zip",
        member="BTCUSDT-1h-2017-08.csv",
        row=1,
        raw_timestamp=_ts(0),
        parsed_timestamp=datetime(
            2017, 8, 17, 0, tzinfo=timezone.utc
        ).isoformat(),
        anomaly_type="INVALID_OHLC",
        validation_rule="synthetic",
        severity="ERROR",
        source_provenance="synthetic",
        message="synthetic",
    )
    report = ArchiveQualityReport(
        symbol="BTCUSDT",
        archive=path.name,
        rows_processed=1,
        events=(bad,),
        checksum_verified=True,
        valid_timestamps=(),
    )
    manifest = _manifest("BTCUSDT", [report])
    with pytest.raises(
        TreatmentAwareNormalizationError,
        match="physical-row identity mismatch",
    ):
        normalize_archive_with_treatment(
            path, "BTCUSDT", report, manifest
        )


def test_multiple_events_one_physical_row_counts_once(tmp_path):
    path = _write_zip(
        tmp_path,
        "BTCUSDT-1h-2017-08.zip",
        [_row(_ts(0)), _row(_ts(1))],
    )
    member = "BTCUSDT-1h-2017-08.csv"
    parsed = datetime(2017, 8, 17, 0, tzinfo=timezone.utc).isoformat()
    events = tuple(
        DataQualityEvent(
            symbol="BTCUSDT",
            timeframe="1h",
            archive=path.name,
            member=member,
            row=2,
            raw_timestamp=_ts(1),
            parsed_timestamp=datetime(
                2017, 8, 17, 1, tzinfo=timezone.utc
            ).isoformat(),
            anomaly_type=kind,
            validation_rule="synthetic",
            severity="ERROR",
            source_provenance="synthetic",
            message="synthetic",
        )
        for kind in ("INVALID_OHLC", "INVALID_VOLUME")
    )
    report = ArchiveQualityReport(
        symbol="BTCUSDT",
        archive=path.name,
        rows_processed=2,
        events=events,
        checksum_verified=True,
        valid_timestamps=(
            datetime(2017, 8, 17, 0, tzinfo=timezone.utc),
        ),
    )
    manifest = _manifest("BTCUSDT", [report])
    result = normalize_development_archives(
        "BTCUSDT", [path], [report], manifest
    )
    account = result.archive_accounting[0]
    assert account.explicitly_rejected_raw_rows == 1
    rejected = account.rejected_raw_rows[0]
    assert rejected.physical_row_number == 2
    assert rejected.sorted_anomaly_types == (
        "INVALID_OHLC",
        "INVALID_VOLUME",
    )
    assert len(rejected.sorted_anomaly_ids) == 2


def test_digest_canonicalization_is_deterministic_under_dict_order():
    first = [
        {"filename": "a.zip", "digest": "1" * 64, "count": 2},
        {"filename": "b.zip", "digest": "2" * 64, "count": 0},
    ]
    second = [
        {"count": 2, "digest": "1" * 64, "filename": "a.zip"},
        {"digest": "2" * 64, "filename": "b.zip", "count": 0},
    ]
    assert asset_aggregate_sha256(
        "BTCUSDT", "ALL_RAW_KEYS", first
    ) == asset_aggregate_sha256(
        "BTCUSDT", "ALL_RAW_KEYS", second
    )


def test_archive_order_is_part_of_aggregate_identity():
    first = [
        {"filename": "a.zip", "digest": "1" * 64, "count": 2},
        {"filename": "b.zip", "digest": "2" * 64, "count": 0},
    ]
    assert asset_aggregate_sha256(
        "BTCUSDT", "ALL_RAW_KEYS", first
    ) != asset_aggregate_sha256(
        "BTCUSDT", "ALL_RAW_KEYS", list(reversed(first))
    )


def test_completed_archive_accounting_survives_later_archive_failure(tmp_path):
    first = _write_zip(
        tmp_path,
        "BTCUSDT-1h-2017-08.zip",
        [_row(_ts(0)), _row(_ts(1))],
    )
    second = _write_zip(
        tmp_path,
        "BTCUSDT-1h-2017-09.zip",
        [_row(_ts(2, 28))],
    )
    r1 = scan_archive(first, "BTCUSDT", checksum_verified=True)
    r2_real = scan_archive(second, "BTCUSDT", checksum_verified=True)
    manifest = _manifest("BTCUSDT", [r1, r2_real])
    # Remove the known row-level event only from the normalization input,
    # forcing a scanner/normalizer mismatch in archive 2.
    r2_lied = ArchiveQualityReport(
        symbol=r2_real.symbol,
        archive=r2_real.archive,
        rows_processed=r2_real.rows_processed,
        events=(),
        checksum_verified=r2_real.checksum_verified,
        valid_timestamps=r2_real.valid_timestamps,
    )
    with pytest.raises(TreatmentAwareNormalizationError) as info:
        normalize_development_archives(
            "BTCUSDT", [first, second], [r1, r2_lied], manifest
        )
    evidence = info.value.incident_evidence()
    assert evidence["failure_code"] == "SCANNER_NORMALIZER_MISMATCH"
    assert evidence["completed_archive_count"] == 1
    completed = evidence["completed_archive_accounting"][0]
    assert completed["filename"] == first.name
    assert completed["accounting_equal"] is True
    current = evidence["current_archive_progress"]
    assert current["filename"] == second.name
    assert current["processed_raw_data_rows"] == 1
    assert current["normalized_accepted_raw_rows"] == 0
    assert current["explicitly_rejected_raw_rows"] == 0
    assert current["unresolved_raw_rows"] == 1


def test_mid_archive_failure_records_exact_row_and_progress(tmp_path):
    path = _write_zip(
        tmp_path,
        "BTCUSDT-1h-2017-08.zip",
        [_row(_ts(0)), _row(_ts(1, 28)), _row(_ts(2))],
    )
    real = scan_archive(path, "BTCUSDT", checksum_verified=True)
    manifest = _manifest("BTCUSDT", [real])
    lied = ArchiveQualityReport(
        symbol=real.symbol,
        archive=real.archive,
        rows_processed=real.rows_processed,
        events=(),
        checksum_verified=real.checksum_verified,
        valid_timestamps=real.valid_timestamps,
    )
    with pytest.raises(TreatmentAwareNormalizationError) as info:
        normalize_development_archives(
            "BTCUSDT", [path], [lied], manifest
        )
    evidence = info.value.incident_evidence()
    assert evidence["failure_code"] == "SCANNER_NORMALIZER_MISMATCH"
    assert evidence["failing_row"] == {
        "archive": path.name,
        "member": "BTCUSDT-1h-2017-08.csv",
        "physical_row_number": 2,
        "raw_timestamp": _ts(1, 28),
    }
    current = evidence["current_archive_progress"]
    assert current["processed_raw_data_rows"] == 2
    assert current["normalized_accepted_raw_rows"] == 1
    assert current["explicitly_rejected_raw_rows"] == 0
    assert current["unresolved_raw_rows"] == 1


def test_treatment_linkage_failure_retains_anomaly_evidence(
    monkeypatch, tmp_path
):
    path = _write_zip(
        tmp_path,
        "BTCUSDT-1h-2017-08.zip",
        [_row(_ts(0)), _row(_ts(1, 28)), _row(_ts(2))],
    )
    report = scan_archive(path, "BTCUSDT", checksum_verified=True)
    manifest = _manifest("BTCUSDT", [report])
    monkeypatch.setattr(
        norm,
        "_event_linked_to_development_treatment",
        lambda event, manifest: False,
    )
    with pytest.raises(TreatmentAwareNormalizationError) as info:
        normalize_development_archives(
            "BTCUSDT", [path], [report], manifest
        )
    evidence = info.value.incident_evidence()
    assert evidence["failure_code"] == "DEVELOPMENT_TREATMENT_LINKAGE_MISSING"
    assert evidence["failing_row"]["physical_row_number"] == 2
    assert evidence["anomaly_types"] == ["NON_ALIGNED_TIMESTAMP"]
    assert len(evidence["anomaly_ids"]) == 1
    assert evidence["parsed_timestamps"]
