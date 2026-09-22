from __future__ import annotations

import inspect
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

import research_core.ams_dep_empirical_access as access
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
from research_core.release_gate import ResearchGateError
from research_core.source_identity import source_identity


def _synthetic_bundle(tmp_path: Path, symbol: str = "BTCUSDT") -> CertifiedDataBundle:
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    canonical = "BTC/USDT" if symbol == "BTCUSDT" else "ETH/USDT"
    bars = []
    for i in range(800):
        t = start + timedelta(hours=i)
        close = Decimal("100") + Decimal(i) / Decimal("50")
        bars.append(
            MarketBar(
                t,
                canonical,
                close - Decimal(".01"),
                close + Decimal(".05"),
                close - Decimal(".05"),
                close,
                Decimal("1000") + Decimal(i % 17),
            )
        )
    bars = tuple(bars)
    raw = tmp_path / f"{symbol}-fixture.zip"
    raw.write_bytes(b"test-only synthetic raw archive")
    raw_id = source_identity([raw])
    segment = CertifiedSegment(
        bars[0].timestamp.isoformat(),
        (bars[-1].timestamp + timedelta(hours=1)).isoformat(),
    )
    partition = PartitionCertification(
        "development",
        DEVELOPMENT_START.isoformat(),
        DEVELOPMENT_END.isoformat(),
        "VALID",
        (segment,),
        (),
    )
    manifest = ResearchTreatmentManifest(
        f"binance-public-data-spot-1h:{raw_id}",
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
        (partition,),
        "SOURCE VERIFIED",
        "VALID",
        "",
    )
    manifest = replace(
        manifest,
        dataset_identity=recompute_treatment_manifest_identity(manifest),
    )
    metadata = make_metadata(
        list(bars), symbol, "milliseconds", source_identity=raw_id
    )
    return CertifiedDataBundle(symbol, bars, metadata, manifest, (raw,))


def test_current_machine_gate_blocks_before_private_loader(monkeypatch):
    called = False

    def forbidden_loader(symbol):
        nonlocal called
        called = True
        raise AssertionError("loader must not be reached")

    monkeypatch.setattr(access, "_load_registered_development_bundle", forbidden_loader)
    with pytest.raises(ResearchGateError):
        access.load_development_bundle("BTCUSDT")
    assert called is False


@pytest.mark.parametrize("partition", ["validation", "oos", "Validation", "OOS"])
def test_non_development_partition_is_rejected_before_gate_or_loader(monkeypatch, partition):
    gate_called = False

    def forbidden_gate():
        nonlocal gate_called
        gate_called = True
        raise AssertionError("gate should not be reached for forbidden partition")

    monkeypatch.setattr(access, "_assert_canonical_empirical_release", forbidden_gate)
    with pytest.raises(access.EmpiricalAccessError, match="only Development"):
        access._authorize_request(partition, "BTCUSDT")
    assert gate_called is False


def test_public_production_api_exposes_no_gate_partition_or_loader_override():
    signature = inspect.signature(access.load_development_bundle)
    assert tuple(signature.parameters) == ("symbol",)

    source = inspect.getsource(access.load_development_bundle)
    forbidden = (
        "gate_path",
        "partition=",
        "loader=",
        "callback",
        "os.environ",
        "getenv",
    )
    for token in forbidden:
        assert token not in source


def test_test_only_monkeypatch_can_reach_synthetic_loader_only_after_fake_gate(
    tmp_path, monkeypatch
):
    bundle = _synthetic_bundle(tmp_path)
    # Production has no injection parameter. The only test seam is monkeypatching
    # private functions in-process.
    monkeypatch.setattr(
        access,
        "_assert_canonical_empirical_release",
        lambda: {
            "full_pipeline_synthetic_integrity_passed": True,
            "separate_empirical_release_approved": True,
            "development_market_data_execution_authorized": True,
            "validation_or_oos_access_authorized": False,
        },
    )
    monkeypatch.setattr(
        access,
        "_load_registered_development_bundle",
        lambda symbol: bundle,
    )
    # Synthetic manifest identity is test-only; production verification requires
    # the registered asset identity. Patch the private verifier seam rather than
    # adding any public override parameter.
    original = access.verify_certified_bundle
    monkeypatch.setattr(
        access,
        "verify_certified_bundle",
        lambda value: original(
            value, registered_identity=value.manifest.dataset_identity
        ),
    )

    loaded = access.load_development_bundle("BTCUSDT")
    assert loaded is bundle

    with pytest.raises(access.EmpiricalAccessError):
        access._authorize_request("validation", "BTCUSDT")
    with pytest.raises(access.EmpiricalAccessError):
        access._authorize_request("oos", "BTCUSDT")


def test_wrong_symbol_rejected_before_machine_gate(monkeypatch):
    gate_called = False

    def forbidden_gate():
        nonlocal gate_called
        gate_called = True
        raise AssertionError

    monkeypatch.setattr(access, "_assert_canonical_empirical_release", forbidden_gate)
    with pytest.raises(access.EmpiricalAccessError, match="unsupported"):
        access._authorize_request("development", "DOGEUSDT")
    assert gate_called is False


def test_empirical_cli_exposes_only_symbol_option():
    root = Path(__file__).resolve().parents[1]
    script = root / "research/scripts/run_ams_dep_empirical.py"
    source = script.read_text()
    assert 'parser.add_argument("--symbol"' in source
    for forbidden in (
        "--gate",
        "--gate-path",
        "--partition",
        "--loader",
        "--validation",
        "--oos",
        "--pnl",
        "--paper",
        "--live",
    ):
        assert forbidden not in source
