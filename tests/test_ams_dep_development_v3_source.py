from __future__ import annotations

import hashlib
import inspect

import pytest

import research_core.ams_dep_development_source_v3 as source
import research_core.ams_dep_empirical_access_v3 as access


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
