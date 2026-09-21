from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/scripts/run_ams_dep_full_pipeline_integrity.py"
REGISTRATION = ROOT / "research/governance/ams_dep_full_pipeline_integrity_v1.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("full_pipeline_runner", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_certification_runner_is_locked_before_freeze_authorization():
    runner = load_runner()
    with pytest.raises(runner.CertificationLockError):
        runner._verify_freeze()


def test_representative_fixture_evidence_is_complete_and_synthetic(tmp_path):
    runner = load_runner()
    evidence = runner._fixture_evidence(tmp_path)

    assert set(evidence["bundle_verification"]) == {"BTCUSDT", "ETHUSDT"}
    for symbol, accounting in evidence["primary_accounting"].items():
        assert accounting["candidate_rows"] == (
            accounting["accepted_rows"] + accounting["rejected_rows"]
        )
        assert accounting["loaded_rows"] > 0
        assert len(accounting["inventory_sha256"]) == 5

    assert evidence["support"]["BTCUSDT"]["pass"] is True
    assert evidence["support"]["ETHUSDT"]["pass"] is True
    assert len(evidence["support"]["BTCUSDT"]["cells"]) == 15
    assert len(evidence["support"]["ETHUSDT"]["cells"]) == 15

    assert evidence["exact_cross_asset_join"]["count"] > 0
    assert (
        evidence["numerical_wiring"]["engineering_fixture"]["classification"]
        == "ENGINEERING_ONLY_NOT_CALIBRATION"
    )
    assert evidence["numerical_wiring"]["engineering_fixture"]["p_value"] is None
    assert len(evidence["six_slot_assembly"]) == 6
    assert (
        evidence["directed_cross_asset_lagged_diagnostics"]["status"]
        == "BLOCKED_PENDING_SEPARATE_CROSS_ASSET_LAG_INTEGRITY_SPEC"
    )
    assert (
        evidence["directed_cross_asset_lagged_diagnostics"][
            "authorized_by_v1_pass"
        ]
        is False
    )


def test_oracle_map_matches_registered_oracles_except_fp11_internal_inventory():
    runner = load_runner()
    registration = json.loads(REGISTRATION.read_text())
    registered = set(registration["oracles"])
    runner_oracles = set(runner.ORACLE_TESTS)
    assert runner_oracles == registered - {
        "FP-11_IMMUTABLE_PROVENANCE_OUTPUT_INVENTORY"
    }


def test_certification_runner_has_no_network_or_empirical_data_imports():
    tree = ast.parse(SCRIPT.read_text())
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    lowered = "\n".join(imports).lower()
    for token in (
        "urllib",
        "requests",
        "data_ingestion.download_archive",
        "historical_dataset",
    ):
        assert token not in lowered
