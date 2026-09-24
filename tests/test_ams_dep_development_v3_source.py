from __future__ import annotations

import hashlib
import inspect
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

import research_core.ams_dep_development_source_v3 as source
import research_core.ams_dep_empirical_access_v3 as access
from research_core.ams_dep_source_coverage_v3 import (
    SourceCoverageV3Error,
    audit_development_source_coverage_v3,
)
from research_core.data_quality_treatment_v2 import (
    CertifiedSegment,
    Exclusion,
    PartitionCertification,
)


def test_v3_inventory_is_exactly_53_development_months():
    months = source.development_months()
    assert len(months) == 53
    assert months[0] == (2017, 8)
    assert months[-1] == (2021, 12)
    assert len(source.expected_filenames("BTCUSDT")) == 53
    assert len(source.expected_filenames("ETHUSDT")) == 53
    assert all(
        "2022-" not in name
        for name in source.expected_filenames("BTCUSDT")
    )


def test_v3_source_public_api_exposes_only_symbol():
    assert tuple(
        inspect.signature(
            source.acquire_registered_development_source_v3
        ).parameters
    ) == ("symbol",)
    assert tuple(inspect.signature(access.load_development_source).parameters) == (
        "symbol",
    )
    assert tuple(inspect.signature(access.load_development_bundle).parameters) == (
        "symbol",
    )


def test_fixed_v3_url_is_official_binance_only():
    url = source._fixed_official_url("BTCUSDT", 2021, 12)
    assert url.startswith("https://data.binance.vision/data/spot/")
    assert url.endswith("/BTCUSDT-1h-2021-12.zip")


def test_v3_claim_failure_prevents_staging_and_download(monkeypatch):
    staged = False
    downloaded = False
    monkeypatch.setattr(
        source,
        "assert_development_execution_allowed",
        lambda: {"authorized": True},
    )

    def blocked_claim():
        raise RuntimeError("V3_DURABLE_CLAIM_MISSING")

    def forbidden_mkdtemp(*args, **kwargs):
        nonlocal staged
        staged = True
        raise AssertionError("V3 staging must not be reached")

    def forbidden_download(*args, **kwargs):
        nonlocal downloaded
        downloaded = True
        raise AssertionError("V3 download must not be reached")

    monkeypatch.setattr(source, "assert_claim_environment", blocked_claim)
    monkeypatch.setattr(source.tempfile, "mkdtemp", forbidden_mkdtemp)
    monkeypatch.setattr(source, "download_archive", forbidden_download)

    with pytest.raises(RuntimeError, match="V3_DURABLE_CLAIM_MISSING"):
        source.acquire_registered_development_source_v3("BTCUSDT")
    assert staged is False
    assert downloaded is False


def test_btc_parent_checksum_mismatch_fails_before_coverage_bundle(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        source, "assert_development_execution_allowed",
        lambda: {"authorized": True},
    )
    monkeypatch.setattr(
        source, "assert_claim_environment",
        lambda: {"ref": "v3", "sha": "a" * 40},
    )
    monkeypatch.setattr(source, "development_months", lambda: ((2017, 8),))
    monkeypatch.setattr(
        source,
        "_load_registration",
        lambda: {
            "btc_parent_checksum_pins": {
                "BTCUSDT-1h-2017-08.zip": "0" * 64
            }
        },
    )
    monkeypatch.setattr(
        source.tempfile, "mkdtemp", lambda **kwargs: str(tmp_path)
    )

    payload = b"synthetic archive bytes"
    actual = hashlib.sha256(payload).hexdigest()

    def fake_download(url, destination, verify_checksum):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        return actual

    reached = False

    def forbidden_bundle(*args, **kwargs):
        nonlocal reached
        reached = True
        raise AssertionError("coverage bundle must not be reached")

    monkeypatch.setattr(source, "download_archive", fake_download)
    monkeypatch.setattr(
        source, "_build_coverage_aware_bundle", forbidden_bundle
    )

    with pytest.raises(
        source.DevelopmentSourceV3Error,
        match="provider-byte continuity mismatch",
    ):
        source.acquire_registered_development_source_v3("BTCUSDT")
    assert reached is False


def test_eth_has_no_parent_checksum_requirement(monkeypatch, tmp_path):
    monkeypatch.setattr(
        source, "assert_development_execution_allowed",
        lambda: {"authorized": True},
    )
    monkeypatch.setattr(
        source, "assert_claim_environment",
        lambda: {"ref": "v3", "sha": "a" * 40},
    )
    monkeypatch.setattr(source, "development_months", lambda: ((2017, 8),))
    monkeypatch.setattr(
        source, "_load_registration",
        lambda: {"btc_parent_checksum_pins": {}},
    )
    monkeypatch.setattr(
        source.tempfile, "mkdtemp", lambda **kwargs: str(tmp_path)
    )

    payload = b"synthetic eth archive bytes"
    checksum = hashlib.sha256(payload).hexdigest()

    def fake_download(url, destination, verify_checksum):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        return checksum

    reached = False

    def stop_at_bundle(*args, **kwargs):
        nonlocal reached
        reached = True
        raise RuntimeError("STOP_AFTER_ETH_CHECKSUM")

    monkeypatch.setattr(source, "download_archive", fake_download)
    monkeypatch.setattr(
        source, "_build_coverage_aware_bundle", stop_at_bundle
    )

    with pytest.raises(
        source.DevelopmentSourceV3Error,
        match="STOP_AFTER_ETH_CHECKSUM",
    ):
        source.acquire_registered_development_source_v3("ETHUSDT")
    assert reached is True


def test_empirical_access_preserves_progressive_coverage_evidence(monkeypatch):
    evidence = (
        source.ArchiveEvidenceV3(
            symbol="BTCUSDT",
            year=2017,
            month=8,
            filename="BTCUSDT-1h-2017-08.zip",
            official_url="https://data.binance.vision/example.zip",
            official_checksum_sha256="a" * 64,
            local_zip_sha256="a" * 64,
            parent_btc_checksum_sha256="a" * 64,
            parent_checksum_continuity_pass=True,
        ),
    )
    monkeypatch.setattr(
        access,
        "_authorize_request",
        lambda partition, symbol: {"authorized": True},
    )
    coverage = {
        "evidence_status": "PARTIAL_COVERAGE_AUDIT",
        "failure_code": "ARCHIVE_BOUNDARY_COVERAGE_UNACCOUNTED",
        "accepted_normalized_timestamp_vector_exact": [
            "2017-08-17T00:00:00+00:00"
        ],
    }

    def fail_source(symbol):
        raise source.DevelopmentSourceV3Error(
            "injected",
            partial_archive_evidence=evidence,
            network_source_access_attempted=True,
            progressive_normalization_evidence={
                "evidence_status": "COMPLETE_NORMALIZATION_ACCOUNTING"
            },
            progressive_coverage_evidence=coverage,
        )

    monkeypatch.setattr(
        access, "_load_registered_development_source", fail_source
    )
    with pytest.raises(access.EmpiricalAccessV3Error) as info:
        access.load_development_source("BTCUSDT")
    assert info.value.partial_archive_evidence == evidence
    assert info.value.network_source_access_attempted is True
    assert info.value.progressive_coverage_evidence == coverage


def test_v3_registration_retains_v2_normalizer_pin():
    registration = source._load_registration()
    inherited = registration["row_treatment_inheritance"]
    assert inherited["reuse_exact_v2_treatment_aware_normalizer"] is True
    assert inherited["v2_normalizer_git_blob_sha1"] == (
        "8c257290ff04e726b53cafa433596311dcec32c4"
    )


def test_v3_imports_the_frozen_v2_treatment_aware_normalizer():
    assert source.normalize_development_archives.__module__ == (
        "research_core.ams_dep_treatment_aware_normalization_v2"
    )


def test_coverage_manifest_is_constructed_only_after_v2_row_normalization():
    text = inspect.getsource(source._build_coverage_aware_bundle)
    normalize_pos = text.index("normalize_development_archives(")
    coverage_pos = text.index("audit_development_source_coverage_v3(")
    bundle_pos = text.index("CertifiedDataBundle(")
    assert normalize_pos < coverage_pos < bundle_pos
    assert text.count("normalize_development_archives(") == 1


def _ms(value: datetime) -> str:
    return str(int(value.timestamp() * 1000))


def _row(ts: str):
    return [ts, "100", "101", "99", "100", "10", "0", "0", "0", "0", "0", "0"]


def _write_zip(tmp_path: Path, filename: str, rows: list[list[str]]) -> Path:
    member = filename.removesuffix(".zip") + ".csv"
    path = tmp_path / filename
    payload = "\n".join(",".join(row) for row in rows) + "\n"
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(member, payload)
    return path


def test_v3_integration_preserves_43_row_style_non_aligned_treatment(
    monkeypatch, tmp_path
):
    start = datetime(2018, 2, 9, 8, tzinfo=timezone.utc)
    malformed = [
        start + timedelta(hours=index, minutes=28)
        for index in range(1, 44)
    ]
    final = start + timedelta(hours=44)
    path = _write_zip(
        tmp_path,
        "BTCUSDT-1h-2018-02.zip",
        [_row(_ms(start))]
        + [_row(_ms(value)) for value in malformed]
        + [_row(_ms(final))],
    )

    real_normalizer = source.normalize_development_archives
    captured = {}

    def capture_normalization(*args, **kwargs):
        result = real_normalizer(*args, **kwargs)
        captured["result"] = result
        return result

    def stop_after_normalization(*args, **kwargs):
        raise SourceCoverageV3Error(
            "STOP_AFTER_V2_ROW_TREATMENT",
            failure_code="TEST_STOP_AFTER_V2_ROW_TREATMENT",
        )

    monkeypatch.setattr(
        source, "normalize_development_archives", capture_normalization
    )
    monkeypatch.setattr(
        source, "audit_development_source_coverage_v3",
        stop_after_normalization,
    )

    with pytest.raises(
        source.DevelopmentSourceV3Error,
        match="STOP_AFTER_V2_ROW_TREATMENT",
    ):
        source._build_coverage_aware_bundle("BTCUSDT", (path,))

    normalized = captured["result"]
    assert [bar.timestamp for bar in normalized.bars] == [start, final]
    account = normalized.archive_accounting[0]
    assert account.raw_data_rows == 45
    assert account.normalized_accepted_raw_rows == 2
    assert account.explicitly_rejected_raw_rows == 43
    assert account.accounting_equal is True
    assert [
        rejected.physical_row_number
        for rejected in account.rejected_raw_rows
    ] == list(range(2, 45))
    assert all(
        rejected.sorted_anomaly_types == ("NON_ALIGNED_TIMESTAMP",)
        for rejected in account.rejected_raw_rows
    )


def test_v3_coverage_overlay_does_not_change_v2_raw_row_accounting(tmp_path):
    start = datetime(2017, 8, 17, 1, tzinfo=timezone.utc)
    path = _write_zip(
        tmp_path,
        "BTCUSDT-1h-2017-08.zip",
        [_row(_ms(start + timedelta(hours=index))) for index in range(3)],
    )
    report = source.scan_archive(path, "BTCUSDT", checksum_verified=True)
    base = source.build_manifest(
        "BTCUSDT",
        [report],
        research_start=source.DEVELOPMENT_START,
        research_end=source.DEVELOPMENT_END,
    )
    base = source.bind_source_identity(base, [path])
    normalized = source.normalize_development_archives(
        "BTCUSDT", [path], [report], base
    )
    before_aggregate = dict(normalized.aggregate_accounting)
    before_archives = [
        item.to_record(include_rejected_rows=True)
        for item in normalized.archive_accounting
    ]

    with_gaps = audit_development_source_coverage_v3(
        "BTCUSDT",
        base,
        (bar.timestamp for bar in normalized.bars),
        (path.name,),
    )
    assert with_gaps.evidence["missing_coverage_hour_count"] > 0

    observed_start = normalized.bars[0].timestamp
    observed_end = normalized.bars[-1].timestamp + timedelta(hours=1)
    no_gap_segment = CertifiedSegment(
        observed_start.isoformat(), observed_end.isoformat()
    )
    development = next(
        item for item in base.partitions if item.partition == "development"
    )
    no_gap_partition = replace(
        development,
        certification="VALID",
        certified_segments=(no_gap_segment,),
        exclusions=(),
    )
    no_gap_base = replace(
        base,
        exclusions=(),
        continuity_breaks=(),
        certified_segments=(no_gap_segment,),
        partitions=(no_gap_partition,),
        research_certification="VALID",
    )
    without_gaps = audit_development_source_coverage_v3(
        "BTCUSDT",
        no_gap_base,
        (bar.timestamp for bar in normalized.bars),
        (path.name,),
    )
    assert without_gaps.evidence["missing_coverage_hour_count"] == 0

    assert dict(normalized.aggregate_accounting) == before_aggregate
    assert [
        item.to_record(include_rejected_rows=True)
        for item in normalized.archive_accounting
    ] == before_archives
    assert normalized.aggregate_accounting["raw_data_rows"] == 3
    assert normalized.aggregate_accounting[
        "normalized_accepted_raw_rows"
    ] == 3
    assert normalized.aggregate_accounting[
        "explicitly_rejected_raw_rows"
    ] == 0


def test_canonical_verifier_failure_preserves_complete_lossless_coverage(
    monkeypatch, tmp_path
):
    start = datetime(2017, 8, 17, 1, tzinfo=timezone.utc)
    path = _write_zip(
        tmp_path,
        "BTCUSDT-1h-2017-08.zip",
        [_row(_ms(start + timedelta(hours=index))) for index in range(3)],
    )

    def fail_canonical(*args, **kwargs):
        raise source.PipelineIntegrityError("INJECTED_CANONICAL_FAILURE")

    monkeypatch.setattr(source, "verify_certified_bundle", fail_canonical)

    with pytest.raises(source.DevelopmentSourceV3Error) as info:
        source._build_coverage_aware_bundle("BTCUSDT", (path,))

    error = info.value
    assert "coverage-aware bundle failed canonical verification" in str(error)
    evidence = error.progressive_coverage_evidence
    assert evidence["evidence_status"] == "COMPLETE_SOURCE_COVERAGE_AUDIT"
    assert evidence["failure_code"] == "CANONICAL_BUNDLE_VERIFICATION_FAIL"
    assert evidence["failure_stage"] == "CANONICAL_BUNDLE_VERIFICATION"
    assert evidence["accepted_normalized_timestamp_vector_exact"] == [
        (start + timedelta(hours=index)).isoformat()
        for index in range(3)
    ]
    assert evidence["missing_coverage_hour_vector_exact"]
    assert source.DEVELOPMENT_START.isoformat() in (
        evidence["missing_coverage_hour_vector_exact"]
    )
    assert evidence["base_certified_segment_records_exact"]
    assert evidence["coverage_gap_intervals_exact"]
    assert evidence["final_certified_segments_exact"]
    assert error.progressive_normalization_evidence[
        "evidence_status"
    ] == "COMPLETE_NORMALIZATION_ACCOUNTING"
