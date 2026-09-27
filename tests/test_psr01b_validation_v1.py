from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging
from pathlib import Path
from types import SimpleNamespace
import zipfile

import numpy as np
import pytest

from research_core.ams_dep_treatment_aware_normalization_v2 import (
    _event_linked_to_development_treatment,
    normalize_archive_with_treatment,
)
from research_core.data_interfaces import MarketBar
from research_core.data_quality import ArchiveQualityReport, DataQualityEvent
from research_core.data_quality_treatment_v2 import (
    Exclusion,
    PartitionCertification,
    build_manifest,
    event_id,
)
from research_core.psr01b_core import PSR01BError, split_origin_eligible
from research_core import psr01b_validation as val


UTC = timezone.utc


def _ms(stamp: datetime) -> str:
    return str(int(stamp.timestamp() * 1000))


def _row(stamp: datetime, close: str = "100.0") -> list[str]:
    return [_ms(stamp), "100.0", "101.0", "99.0", close, "10.0"]


def _write_zip(path: Path, rows: list[list[str]]) -> str:
    member = path.name.replace(".zip", ".csv")
    text = "\n".join(",".join(row) for row in rows) + "\n"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(member, text)
    return member


def _event(
    stamp: datetime,
    *,
    archive: str,
    member: str,
    row: int = 1,
    raw_timestamp: str | None = None,
    anomaly_type: str = "SYNTHETIC_ANOMALY",
    parsed: bool = True,
) -> DataQualityEvent:
    return DataQualityEvent(
        symbol="BTCUSDT",
        timeframe="1h",
        archive=archive,
        member=member,
        row=row,
        raw_timestamp=raw_timestamp if raw_timestamp is not None else _ms(stamp),
        parsed_timestamp=stamp.isoformat() if parsed else None,
        anomaly_type=anomaly_type,
        validation_rule="synthetic registered test",
        severity="ERROR",
        source_provenance="synthetic-only",
        message="synthetic event",
    )


def _manifest(reports: list[ArchiveQualityReport]):
    return build_manifest(
        "BTCUSDT",
        reports,
        research_start=val.SOURCE_START,
        research_end=val.HARD_END,
    )


def _without_partition_link(manifest, name: str):
    parts = list(manifest.partitions)
    for i, part in enumerate(parts):
        if part.partition == name:
            parts[i] = replace(part, exclusions=())
    return replace(manifest, partitions=tuple(parts))


def _inventory_reports() -> tuple[ArchiveQualityReport, ...]:
    reports = []
    for name in val.registered_archive_inventory():
        year, month = (int(x) for x in name.removesuffix(".zip").split("-")[-2:])
        stamp = datetime(year, month, 1, tzinfo=UTC)
        reports.append(
            ArchiveQualityReport(
                "BTCUSDT",
                name,
                1,
                (),
                True,
                (stamp,),
            )
        )
    return tuple(reports)


def _august_fixture(tmp_path: Path):
    archive = tmp_path / "BTCUSDT-1h-2020-08.zip"
    t0 = datetime(2020, 8, 30, 22, tzinfo=UTC)
    t1 = t0 + timedelta(hours=1)
    t2 = val.SOURCE_START
    rows = [_row(t0), _row(t1), _row(t2)]
    member = _write_zip(archive, rows)
    anomaly = _event(t0, archive=archive.name, member=member, row=1)
    report = ArchiveQualityReport(
        "BTCUSDT",
        archive.name,
        3,
        (anomaly,),
        True,
        (t1, t2),
    )
    manifest = _manifest([report])
    return archive, report, manifest, anomaly, t0, t1, t2


def test_PRE_BOUNDARY_DEVELOPMENT_LINKAGE_EQUIVALENCE():
    stamp = datetime(2021, 12, 31, 22, tzinfo=UTC)
    archive = "BTCUSDT-1h-2021-12.zip"
    member = "BTCUSDT-1h-2021-12.csv"
    event = _event(stamp, archive=archive, member=member)
    report = ArchiveQualityReport("BTCUSDT", archive, 1, (event,), True, ())
    manifest = _manifest([report])

    parent = _event_linked_to_development_treatment(event, manifest)
    decision = val.phase_treatment_decision(event, manifest)
    assert parent is True
    assert decision.partition == "development"
    assert decision.linked is parent
    assert decision.failure_code is None

    missing = _without_partition_link(manifest, "development")
    parent_missing = _event_linked_to_development_treatment(event, missing)
    decision_missing = val.phase_treatment_decision(event, missing)
    assert parent_missing is False
    assert decision_missing.linked is parent_missing
    assert decision_missing.failure_code == "DEVELOPMENT_TREATMENT_LINKAGE_MISSING"
    with pytest.raises(val.ValidationContractError) as captured:
        val.require_phase_treatment_linkage(event, missing)
    assert captured.value.failure_code == "DEVELOPMENT_TREATMENT_LINKAGE_MISSING"


def test_BOUNDARY_DISPATCH():
    assert val.partition_name_for_timestamp(
        datetime(2021, 12, 31, 23, tzinfo=UTC)
    ) == "development"
    assert val.partition_name_for_timestamp(
        datetime(2022, 1, 1, 0, tzinfo=UTC)
    ) == "validation"
    assert val.partition_name_for_timestamp(
        datetime(2022, 1, 1, 1, tzinfo=UTC)
    ) == "validation"


def test_VALIDATION_LINKAGE():
    for stamp in (
        datetime(2022, 6, 15, 12, tzinfo=UTC),
        datetime(2023, 6, 15, 12, tzinfo=UTC),
    ):
        archive = f"BTCUSDT-1h-{stamp.year:04d}-{stamp.month:02d}.zip"
        member = archive.replace(".zip", ".csv")
        event = _event(stamp, archive=archive, member=member)
        report = ArchiveQualityReport("BTCUSDT", archive, 1, (event,), True, ())
        manifest = _manifest([report])
        decision = val.phase_treatment_decision(event, manifest)
        assert decision.partition == "validation"
        assert decision.linked
        missing = _without_partition_link(manifest, "validation")
        missing_decision = val.phase_treatment_decision(event, missing)
        assert not missing_decision.linked
        assert missing_decision.failure_code == "VALIDATION_TREATMENT_LINKAGE_MISSING"
        with pytest.raises(val.ValidationContractError) as captured:
            val.require_phase_treatment_linkage(event, missing)
        assert captured.value.failure_code == "VALIDATION_TREATMENT_LINKAGE_MISSING"


def test_HARD_END_REJECTION():
    for stamp in (
        datetime(2024, 1, 1, 0, tzinfo=UTC),
        datetime(2024, 1, 1, 1, tzinfo=UTC),
    ):
        with pytest.raises(val.ValidationContractError) as captured:
            val.partition_name_for_timestamp(stamp)
        assert captured.value.failure_code == "HARD_END_REJECTION"


def test_HISTORICAL_SIDE_DOES_NOT_CHANGE_ANOMALY_TREATMENT(tmp_path):
    dev_path = tmp_path / "BTCUSDT-1h-2021-12.zip"
    val_path = tmp_path / "BTCUSDT-1h-2022-01.zip"
    dev_t0 = datetime(2021, 12, 31, 22, tzinfo=UTC)
    val_t0 = datetime(2022, 1, 1, 0, tzinfo=UTC)
    dev_member = _write_zip(dev_path, [_row(dev_t0), _row(dev_t0 + timedelta(hours=1))])
    val_member = _write_zip(val_path, [_row(val_t0), _row(val_t0 + timedelta(hours=1))])
    dev_event = _event(dev_t0, archive=dev_path.name, member=dev_member)
    val_event = _event(val_t0, archive=val_path.name, member=val_member)
    dev_report = ArchiveQualityReport(
        "BTCUSDT", dev_path.name, 2, (dev_event,), True, (dev_t0 + timedelta(hours=1),)
    )
    val_report = ArchiveQualityReport(
        "BTCUSDT", val_path.name, 2, (val_event,), True, (val_t0 + timedelta(hours=1),)
    )
    manifest = _manifest([dev_report, val_report])

    assert val.phase_treatment_decision(dev_event, manifest).partition == "development"
    assert val.phase_treatment_decision(val_event, manifest).partition == "validation"
    assert val.phase_treatment_decision(dev_event, manifest).linked
    assert val.phase_treatment_decision(val_event, manifest).linked
    assert event_id(dev_event) in manifest.anomaly_ids
    assert event_id(val_event) in manifest.anomaly_ids

    _, _, dev_accounting = normalize_archive_with_treatment(
        dev_path, "BTCUSDT", dev_report, manifest
    )
    _, _, val_accounting = val.normalize_validation_archive_with_phase_treatment(
        val_path, val_report, manifest
    )
    assert dev_accounting.normalized_accepted_raw_rows == val_accounting.normalized_accepted_raw_rows == 1
    assert dev_accounting.explicitly_rejected_raw_rows == val_accounting.explicitly_rejected_raw_rows == 1
    assert dev_accounting.rejected_raw_rows[0].sorted_anomaly_types == val_accounting.rejected_raw_rows[0].sorted_anomaly_types


class _OOSSentinelPartitions:
    def __init__(self, development, validation):
        self.development = development
        self.validation = validation
        self.accessed = []

    def __len__(self):
        return 3

    def __getitem__(self, index):
        self.accessed.append(index)
        if index == 0:
            return self.development
        if index == 1:
            return self.validation
        raise AssertionError("OOS partition touched")

    def __iter__(self):
        raise AssertionError("partition enumeration touched OOS sentinel")


def test_NO_OOS_PARTITION_READ_ENUMERATION_OR_FALLBACK():
    dev = PartitionCertification(
        "development",
        "2017-08-17T00:00:00+00:00",
        "2022-01-01T00:00:00+00:00",
        "VALID",
        (),
        (),
    )
    validation = PartitionCertification(
        "validation",
        "2022-01-01T00:00:00+00:00",
        "2024-01-01T00:00:00+00:00",
        "VALID",
        (),
        (),
    )
    sentinel = _OOSSentinelPartitions(dev, validation)
    manifest = SimpleNamespace(partitions=sentinel)

    dev_event = _event(
        datetime(2021, 12, 31, 23, tzinfo=UTC),
        archive="BTCUSDT-1h-2021-12.zip",
        member="BTCUSDT-1h-2021-12.csv",
    )
    val_event = _event(
        datetime(2022, 1, 1, 0, tzinfo=UTC),
        archive="BTCUSDT-1h-2022-01.zip",
        member="BTCUSDT-1h-2022-01.csv",
    )
    assert val.phase_treatment_decision(dev_event, manifest).partition == "development"
    assert val.phase_treatment_decision(val_event, manifest).partition == "validation"
    with pytest.raises(val.ValidationContractError):
        val.partition_name_for_timestamp(datetime(2024, 1, 1, tzinfo=UTC))
    assert set(sentinel.accessed) <= {0, 1}


def test_OPERATOR_LOG_OUTCOME_SUPPRESSION(capsys):
    sentinel = "FORBIDDEN_EMPIRICAL_SENTINEL_937521"

    def noisy_science():
        print(sentinel)
        import sys
        print(sentinel, file=sys.stderr)
        logging.warning(sentinel)
        return {"final_evidence_value": sentinel}

    result = val.run_with_operator_log_suppression(noisy_science)
    captured = capsys.readouterr()
    assert sentinel not in captured.out
    assert sentinel not in captured.err
    assert result["final_evidence_value"] == sentinel


def test_EXACT_MANIFEST_BUILD_AND_PRE_SOURCE_FAIL_CLOSED(tmp_path):
    reports = _inventory_reports()
    manifest = val.build_validation_manifest(reports)
    assert datetime.fromisoformat(manifest.research_start) == val.SOURCE_START
    assert datetime.fromisoformat(manifest.research_end) == val.HARD_END
    assert val._registered_partition(manifest, "development").partition == "development"
    assert val._registered_partition(manifest, "validation").partition == "validation"

    with pytest.raises(val.ValidationContractError):
        val.build_validation_manifest(reports[:-1])

    bad_checksum = list(reports)
    bad_checksum[0] = replace(bad_checksum[0], checksum_verified=False)
    with pytest.raises(val.ValidationContractError) as checksum_failure:
        val.build_validation_manifest(bad_checksum)
    assert checksum_failure.value.failure_code == "VALIDATION_CHECKSUM_UNVERIFIED"

    unlocalized = _event(
        datetime(2020, 8, 1, tzinfo=UTC),
        archive=reports[0].archive,
        member="BTCUSDT-1h-2020-08.csv",
        parsed=False,
    )
    bad_unlocalized = list(reports)
    bad_unlocalized[0] = replace(bad_unlocalized[0], events=(unlocalized,))
    with pytest.raises(val.ValidationContractError) as unlocalized_failure:
        val.build_validation_manifest(bad_unlocalized)
    assert unlocalized_failure.value.failure_code == "VALIDATION_UNLOCALIZED_EVENT"

    archive, report, august_manifest, _, _, _, t2 = _august_fixture(tmp_path)
    clipped, _, accounting = val.normalize_pre_source_august_with_parent(
        archive, report, august_manifest
    )
    assert accounting.explicitly_rejected_raw_rows == 1
    assert [bar.timestamp for bar in clipped] == [t2]


def test_PRE_SOURCE_AUGUST_2020_PINNED_NORMALIZER_EQUIVALENCE(tmp_path):
    archive, report, manifest, anomaly, _, _, t2 = _august_fixture(tmp_path)
    parent_linked = _event_linked_to_development_treatment(anomaly, manifest)
    phase = val.phase_treatment_decision(anomaly, manifest)
    assert parent_linked is True
    assert phase.partition == "development"
    assert phase.linked is parent_linked

    parent_bars, _, parent_accounting = normalize_archive_with_treatment(
        archive, "BTCUSDT", report, manifest
    )
    clipped, _, wrapped_accounting = val.normalize_pre_source_august_with_parent(
        archive, report, manifest
    )
    assert len(parent_bars) == 2
    assert [bar.timestamp for bar in clipped] == [t2]
    assert wrapped_accounting == parent_accounting
    assert wrapped_accounting.explicitly_rejected_raw_rows == 1
    assert all(bar.timestamp >= val.SOURCE_START for bar in clipped)


def test_fold_definitions_and_split_endpoint():
    folds = val.registered_validation_folds()
    assert [fold["fold"] for fold in folds] == list(range(12, 20))
    assert [fold["fold_index"] for fold in folds] == list(range(11, 19))
    end = datetime(2024, 1, 1, tzinfo=UTC)
    start = datetime(2023, 10, 1, tzinfo=UTC)
    assert split_origin_eligible(datetime(2023, 12, 31, 22, tzinfo=UTC), start, end)
    assert not split_origin_eligible(datetime(2023, 12, 31, 23, tzinfo=UTC), start, end)


def test_module_blob_identity():
    observed = val.verify_pinned_module_identities()
    assert len(observed) == 17


def test_protected_url_firewall():
    called = {"value": False}

    def opener(*args, **kwargs):
        called["value"] = True
        raise AssertionError("network opener must not be called")

    for url in (
        "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-2022-01.zip",
        "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-2023-12.zip.CHECKSUM",
        "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-2024-01.zip",
    ):
        with pytest.raises(val.ValidationContractError) as captured:
            val.bounded_urlopen(url, opener=opener)
        assert captured.value.failure_code == "PROTECTED_URL_FIREWALL"
    assert called["value"] is False


def test_egarch_scientific_vs_technical_classification():
    assert val.classify_egarch_failure(
        all_registered_orders_unavailable=True
    ) == val.SCIENTIFIC_NON_REPLICATION
    assert val.classify_egarch_failure(
        structural_exception=True
    ) == val.TECHNICAL_INDETERMINATE
    assert val.classify_exception(
        PSR01BError("all four EGARCH orders unavailable")
    ).classification == val.SCIENTIFIC_NON_REPLICATION
    assert val.classify_exception(
        ImportError("arch ABI missing")
    ).classification == val.TECHNICAL_INDETERMINATE


def test_nonfinite_forecast_classification():
    assert val.classify_forecast_vector(
        [0.1, float("nan")],
        expected_length=2,
        model_returned_normally=True,
    ) == val.SCIENTIFIC_NON_REPLICATION
    assert val.classify_forecast_vector(
        [0.1],
        expected_length=2,
        model_returned_normally=True,
    ) == val.TECHNICAL_INDETERMINATE
    assert val.classify_forecast_vector(
        [0.1, 0.2],
        expected_length=2,
        model_returned_normally=True,
    ) is None


def test_metric_null_semantics():
    value, classification = val.serialize_registered_metric(
        "FOLD_ASD_UNAVAILABLE",
        float("nan"),
    )
    assert value is None
    assert classification == "DESCRIPTIVE_METRIC_UNAVAILABLE"

    value, classification = val.serialize_registered_metric(
        "CONSOLIDATED_COST_AWARE_SHARPE_UNAVAILABLE",
        None,
    )
    assert value is None
    assert classification == val.SCIENTIFIC_NON_REPLICATION

    with pytest.raises(val.ValidationContractError) as captured:
        val.serialize_registered_metric(
            "NONFINITE_FOLD_METRIC_NOT_PERMITTED_AS_NULL",
            float("inf"),
        )
    assert captured.value.failure_code == "NONFINITE_REGISTERED_METRIC_FORBIDDEN"


def test_result_and_incident_no_overwrite(tmp_path):
    result = tmp_path / "result.json"
    incident = tmp_path / "terminal_incident.json"
    val.write_json_exclusive(result, {"validation_result_token": val.VALIDATION_FAIL})
    val.write_json_exclusive(incident, {"terminal_classification": val.SCIENTIFIC_NON_REPLICATION})
    with pytest.raises(val.ValidationContractError):
        val.write_json_exclusive(result, {"second": True})
    with pytest.raises(val.ValidationContractError):
        val.write_json_exclusive(incident, {"second": True})


def test_runner_loss_evidence_gap_state_machine():
    incident = val.build_runner_loss_incident(
        execution_sha="a" * 40,
        reviewed_candidate_sha="b" * 40,
        first_protected_request_occurred=True,
        stage="SOURCE_ACQUISITION",
        evidence_gap_status="RAW_SOURCE_PARTIAL_UNRECOVERABLE",
    )
    assert incident["terminal_classification"] == val.TECHNICAL_INDETERMINATE
    assert incident["validation_result_token"] == val.VALIDATION_TECHNICAL
    assert incident["parent_h2_classification"] is None
    assert incident["practical_benchmark_token"] is None
    assert incident["protected_validation_interval_consumed"] is True
    assert incident["rerun_authorized"] is False
    assert incident["oos_progression_authorized"] is False

    with pytest.raises(val.ValidationContractError):
        val.build_runner_loss_incident(
            execution_sha="a" * 40,
            reviewed_candidate_sha="b" * 40,
            first_protected_request_occurred=False,
            stage="PRE_SOURCE",
            evidence_gap_status="NONE",
        )


def test_validation_orchestration_uses_8x2_registered_sequence(monkeypatch):
    calls = []

    def fake_run(_bars, *, arm_name, fold):
        calls.append((arm_name, fold["fold"], fold["fold_index"]))
        baseline = (np.array([0.001, -0.0005], dtype=np.float64),)
        cost = (np.array([0.0015, 0.0002], dtype=np.float64),)
        buy = (np.array([0.0001, 0.0002], dtype=np.float64),)
        momentum = (np.array([0.0002, -0.0001], dtype=np.float64),)
        return val.parent_runner.FoldExecution(
            arm=arm_name,
            fold_number=fold["fold"],
            fold_index=fold["fold_index"],
            forecast_sha256="0" * 64,
            forecast_count=2,
            selected_features=("x",) * 10,
            egarch_order=(1, 1, 1),
            egarch_aic=1.0,
            selected_trial_index=0,
            final_model_seed=1,
            baseline_segments=baseline,
            cost_aware_segments=cost,
            buy_hold_segments=buy,
            momentum_segments=momentum,
            baseline_turnover=2.0,
            cost_aware_turnover=1.0,
            baseline_completed_trades=1,
            cost_aware_completed_trades=1,
        )

    monkeypatch.setattr(val.parent_runner, "_run_arm_fold", fake_run)
    bar = MarketBar(
        timestamp=val.SOURCE_START,
        symbol="BTC/USDT",
        open=Decimal("100"),
        high=Decimal("101"),
        low=Decimal("99"),
        close=Decimal("100"),
        volume=Decimal("10"),
    )
    result = val.run_validation_from_normalized_bars((bar,))
    assert len(calls) == 16
    assert calls[:8] == [
        ("PAPER_FILL", fold, index)
        for fold, index in zip(range(12, 20), range(11, 19))
    ]
    assert calls[8:] == [
        ("PROJECT_GAP_PRESERVING", fold, index)
        for fold, index in zip(range(12, 20), range(11, 19))
    ]
    assert result["execution_order"]["folds"] == list(range(12, 20))
    assert result["execution_order"]["fold_indices"] == list(range(11, 19))
    assert result["validation_result_token"] in {val.VALIDATION_PASS, val.VALIDATION_FAIL}


def test_bounded_static_contract_reports_all_authorizations_closed():
    result = val.verify_bounded_static_contracts()
    assert result["folds"] == list(range(12, 20))
    assert result["fold_indices"] == list(range(11, 19))
    assert result["archive_count"] == 41
    assert result["pinned_module_count"] == 17
    assert result["protected_source_access_authorized"] is False
    assert result["oos_access_authorized"] is False
