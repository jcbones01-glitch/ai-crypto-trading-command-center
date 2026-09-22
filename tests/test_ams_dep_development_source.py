from __future__ import annotations

import hashlib
import inspect
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

import research_core.ams_dep_development_source as source
import research_core.ams_dep_empirical_access as empirical_access
from research_core.ams_dep_pipeline import (
    DEVELOPMENT_END,
    DEVELOPMENT_START,
    CertifiedDataBundle,
    recompute_treatment_manifest_identity,
)
from research_core.data_ingestion import make_metadata
from research_core.data_interfaces import MarketBar
from research_core.data_quality_treatment_v2 import (
    CertifiedSegment,
    PartitionCertification,
    ResearchTreatmentManifest,
)
from research_core.source_identity import source_identity


def _fixture_bundle(tmp_path: Path, symbol: str = "BTCUSDT"):
    canonical = "BTC/USDT" if symbol == "BTCUSDT" else "ETH/USDT"
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    bars = []
    for i in range(3):
        t = start + timedelta(hours=i)
        close = Decimal("100") + i
        bars.append(
            MarketBar(
                t,
                canonical,
                close,
                close + Decimal("1"),
                close - Decimal("1"),
                close,
                Decimal("1000"),
            )
        )

    paths = []
    evidence = []
    for (year, month), filename in zip(
        source.development_months(),
        source.expected_filenames(symbol),
    ):
        path = tmp_path / filename
        payload = f"{symbol}-{year:04d}-{month:02d}".encode()
        path.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        paths.append(path)
        evidence.append(
            source.ArchiveEvidence(
                symbol=symbol,
                year=year,
                month=month,
                filename=filename,
                official_url=(
                    "https://data.binance.vision/data/spot/monthly/klines/"
                    f"{symbol}/1h/{filename}"
                ),
                official_checksum_sha256=digest,
                local_zip_sha256=digest,
            )
        )

    raw_identity = source_identity(paths)
    segment = CertifiedSegment(
        bars[0].timestamp.isoformat(),
        (bars[-1].timestamp + timedelta(hours=1)).isoformat(),
    )
    development = PartitionCertification(
        "development",
        DEVELOPMENT_START.isoformat(),
        DEVELOPMENT_END.isoformat(),
        "VALID",
        (segment,),
        (),
    )
    validation = PartitionCertification(
        "validation",
        datetime(2022, 1, 1, tzinfo=timezone.utc).isoformat(),
        datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat(),
        "VALID",
        (),
        (),
    )
    oos = PartitionCertification(
        "oos",
        datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat(),
        datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat(),
        "VALID",
        (),
        (),
    )
    manifest = ResearchTreatmentManifest(
        f"binance-public-data-spot-1h:{raw_identity}",
        "gate1a-v1",
        "gate1-v1",
        symbol,
        "1h",
        DEVELOPMENT_START.isoformat(),
        DEVELOPMENT_END.isoformat(),
        (),
        (),
        (),
        (),
        (segment,),
        (development, validation, oos),
        "SOURCE VERIFIED",
        "VALID",
        "",
    )
    manifest = replace(
        manifest,
        dataset_identity=recompute_treatment_manifest_identity(manifest),
    )
    metadata = make_metadata(
        bars,
        symbol,
        "milliseconds",
        source_identity=raw_identity,
    )
    bundle = CertifiedDataBundle(
        symbol,
        tuple(bars),
        metadata,
        manifest,
        tuple(paths),
    )
    return bundle, tuple(evidence)


def test_frozen_development_month_inventory_is_exact():
    months = source.development_months()
    assert len(months) == 53
    assert months[0] == (2017, 8)
    assert months[-1] == (2021, 12)
    assert all((year, month) < (2022, 1) for year, month in months)

    for symbol in ("BTCUSDT", "ETHUSDT"):
        names = source.expected_filenames(symbol)
        assert len(names) == 53
        assert names[0] == f"{symbol}-1h-2017-08.zip"
        assert names[-1] == f"{symbol}-1h-2021-12.zip"


def test_production_acquisition_api_exposes_only_symbol():
    signature = inspect.signature(source.acquire_registered_development_source)
    assert tuple(signature.parameters) == ("symbol",)


def test_execution_lock_fails_before_any_download(monkeypatch):
    called = False

    def blocked():
        raise RuntimeError("LOCKED")

    def forbidden_download(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("download must not be reached")

    monkeypatch.setattr(source, "assert_development_execution_allowed", blocked)
    monkeypatch.setattr(source, "download_archive", forbidden_download)

    with pytest.raises(RuntimeError, match="LOCKED"):
        source.acquire_registered_development_source("BTCUSDT")
    assert called is False


def test_projection_binds_exact_raw_inventory_and_excludes_future_partition_claims(tmp_path):
    bundle, evidence = _fixture_bundle(tmp_path)
    record, digest = source.build_development_projection(bundle, evidence)

    assert len(digest) == 64
    assert record["projection_version"] == source.PROJECTION_VERSION
    assert (
        record["historical_whole_research_parent_manifest_identity"]
        == source.PARENT_MANIFEST_IDENTITIES["BTCUSDT"]
    )
    assert len(record["ordered_archive_evidence_53"]) == 53
    assert record["development_certification"] == "VALID"
    assert "validation_partition_certification" not in record
    assert "oos_partition_certification" not in record
    assert "market_outcomes" not in record
    assert "p_values" not in record


def test_projection_rejects_archive_evidence_not_bound_to_raw_paths(tmp_path):
    bundle, evidence = _fixture_bundle(tmp_path)
    bad = list(evidence)
    bad[0] = replace(bad[0], local_zip_sha256="0" * 64)
    with pytest.raises(source.DevelopmentSourceError, match="local SHA-256 mismatch"):
        source.build_development_projection(bundle, tuple(bad))


def test_fixed_url_is_official_binance_only():
    url = source._fixed_official_url("BTCUSDT", 2021, 12)
    assert url.startswith("https://data.binance.vision/data/spot/")
    assert url.endswith("/BTCUSDT-1h-2021-12.zip")


def test_durable_claim_verification_fails_before_staging_or_download(monkeypatch):
    staged = False
    downloaded = False

    monkeypatch.setattr(
        source,
        "assert_development_execution_allowed",
        lambda: {"authorized": True},
    )

    def blocked_claim():
        raise RuntimeError("DURABLE_CLAIM_MISSING")

    def forbidden_mkdtemp(*args, **kwargs):
        nonlocal staged
        staged = True
        raise AssertionError("staging must not be reached")

    def forbidden_download(*args, **kwargs):
        nonlocal downloaded
        downloaded = True
        raise AssertionError("download must not be reached")

    monkeypatch.setattr(source, "assert_claim_environment", blocked_claim)
    monkeypatch.setattr(source.tempfile, "mkdtemp", forbidden_mkdtemp)
    monkeypatch.setattr(source, "download_archive", forbidden_download)

    with pytest.raises(RuntimeError, match="DURABLE_CLAIM_MISSING"):
        source.acquire_registered_development_source("BTCUSDT")
    assert staged is False
    assert downloaded is False


def test_source_failure_carries_completed_archive_evidence(monkeypatch, tmp_path):
    monkeypatch.setattr(
        source,
        "assert_development_execution_allowed",
        lambda: {"authorized": True},
    )
    monkeypatch.setattr(
        source,
        "assert_claim_environment",
        lambda: {"ref": "claim", "sha": "a" * 40},
    )
    monkeypatch.setattr(
        source.tempfile,
        "mkdtemp",
        lambda **kwargs: str(tmp_path),
    )

    calls = 0

    def fake_download(url, destination, verify_checksum):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected second archive failure")
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = b"first"
        destination.write_bytes(payload)
        return hashlib.sha256(payload).hexdigest()

    monkeypatch.setattr(source, "download_archive", fake_download)

    with pytest.raises(source.DevelopmentSourceError) as info:
        source.acquire_registered_development_source("BTCUSDT")

    assert len(info.value.partial_archive_evidence) == 1
    assert info.value.partial_archive_evidence[0].filename.endswith(
        "2017-08.zip"
    )


def test_empirical_access_preserves_partial_archive_evidence(monkeypatch):
    evidence = (
        source.ArchiveEvidence(
            symbol="BTCUSDT",
            year=2017,
            month=8,
            filename="BTCUSDT-1h-2017-08.zip",
            official_url=(
                "https://data.binance.vision/data/spot/monthly/klines/"
                "BTCUSDT/1h/BTCUSDT-1h-2017-08.zip"
            ),
            official_checksum_sha256="a" * 64,
            local_zip_sha256="a" * 64,
        ),
    )

    monkeypatch.setattr(
        empirical_access,
        "_authorize_request",
        lambda partition, symbol: {"authorized": True},
    )

    def fail_source(symbol):
        raise source.DevelopmentSourceError(
            "injected",
            partial_archive_evidence=evidence,
        )

    monkeypatch.setattr(
        empirical_access,
        "_load_registered_development_source",
        fail_source,
    )

    with pytest.raises(empirical_access.EmpiricalAccessError) as info:
        empirical_access.load_development_source("BTCUSDT")

    assert info.value.partial_archive_evidence == evidence
