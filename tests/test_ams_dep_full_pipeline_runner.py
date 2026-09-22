from __future__ import annotations

import ast
import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/scripts/run_ams_dep_full_pipeline_integrity.py"
REGISTRATION = ROOT / "research/governance/ams_dep_full_pipeline_integrity_v1.json"
FREEZE = ROOT / "research/governance/ams_dep_full_pipeline_implementation_freeze_v1.json"
RELEASE_GATE = ROOT / "research/governance/ams_dep_release_gate_v1.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("full_pipeline_runner", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def runner():
    return load_runner()


def _authorized_documents():
    freeze = json.loads(FREEZE.read_text())
    registration = json.loads(REGISTRATION.read_text())
    gate = json.loads(RELEASE_GATE.read_text())
    freeze["status"] = "AUTHORIZED_FOR_FIRST_CERTIFICATION"
    freeze["independent_implementation_reviewed"] = True
    freeze["certification_execution_authorized"] = True
    freeze["reviewed_implementation_commit"] = freeze["implementation_candidate_commit"]
    return freeze, registration, gate


def _blob_lookup(freeze, registration):
    combined = {
        **freeze["file_git_blob_sha1"],
        **registration["pinned_existing_production_git_blob_sha1"],
    }
    return lambda path: combined[path]


def _validate(runner, freeze, registration, gate, *, ancestor=True, current_blob=None, candidate_blob=None):
    good_blob = _blob_lookup(freeze, registration)
    runner._validate_freeze_contract(
        freeze,
        registration,
        gate,
        "authorized-governance-head",
        current_blob=current_blob or good_blob,
        candidate_blob=candidate_blob or good_blob,
        is_ancestor=(lambda reviewed, current: ancestor),
    )


def test_valid_authorized_contract_passes(runner):
    freeze, registration, gate = _authorized_documents()
    _validate(runner, freeze, registration, gate)


def test_draft_status_fails(runner):
    freeze, registration, gate = _authorized_documents()
    freeze["status"] = "DRAFT_LOCKED"
    with pytest.raises(runner.CertificationLockError, match="not authorized"):
        _validate(runner, freeze, registration, gate)


def test_independent_review_flag_false_fails(runner):
    freeze, registration, gate = _authorized_documents()
    freeze["independent_implementation_reviewed"] = False
    with pytest.raises(runner.CertificationLockError, match="independent implementation review"):
        _validate(runner, freeze, registration, gate)


def test_reviewed_commit_must_equal_candidate(runner):
    freeze, registration, gate = _authorized_documents()
    freeze["reviewed_implementation_commit"] = "0" * 40
    with pytest.raises(runner.CertificationLockError, match="does not equal frozen candidate"):
        _validate(runner, freeze, registration, gate)


def test_reviewed_candidate_must_be_ancestor(runner):
    freeze, registration, gate = _authorized_documents()
    with pytest.raises(runner.CertificationLockError, match="not an ancestor"):
        _validate(runner, freeze, registration, gate, ancestor=False)


def test_missing_required_implementation_pin_fails(runner):
    freeze, registration, gate = _authorized_documents()
    removed = next(iter(freeze["file_git_blob_sha1"]))
    del freeze["file_git_blob_sha1"][removed]
    with pytest.raises(runner.CertificationLockError, match="path set"):
        _validate(runner, freeze, registration, gate)


def test_candidate_blob_mismatch_fails(runner):
    freeze, registration, gate = _authorized_documents()
    good = _blob_lookup(freeze, registration)
    target = "research/scripts/run_ams_dep_full_pipeline_integrity.py"

    def bad_candidate(path):
        return "0" * 40 if path == target else good(path)

    with pytest.raises(runner.CertificationLockError, match="candidate implementation blob"):
        _validate(
            runner,
            freeze,
            registration,
            gate,
            candidate_blob=bad_candidate,
        )


def test_executing_blob_mismatch_fails(runner):
    freeze, registration, gate = _authorized_documents()
    good = _blob_lookup(freeze, registration)
    target = "tests/test_ams_dep_full_pipeline_runner.py"

    def bad_current(path):
        return "f" * 40 if path == target else good(path)

    with pytest.raises(runner.CertificationLockError, match="executing implementation blob"):
        _validate(
            runner,
            freeze,
            registration,
            gate,
            current_blob=bad_current,
        )


def test_existing_production_pin_map_must_equal_registration(runner):
    freeze, registration, gate = _authorized_documents()
    freeze["pinned_existing_production_git_blob_sha1"] = dict(
        freeze["pinned_existing_production_git_blob_sha1"]
    )
    freeze["pinned_existing_production_git_blob_sha1"].pop(
        "src/research_core/market_state.py"
    )
    with pytest.raises(runner.CertificationLockError, match="approved registration"):
        _validate(runner, freeze, registration, gate)


@pytest.fixture(scope="module")
def fixture_evidence(runner, tmp_path_factory):
    return runner._fixture_evidence(tmp_path_factory.mktemp("full-pipeline-runner"))


def _fp11_report(runner, evidence):
    freeze, registration, _ = _authorized_documents()
    report = {
        "plan_sha256": "a" * 64,
        "registration_sha256": "b" * 64,
        "implementation_freeze_sha256": "c" * 64,
        "existing_production_blobs": {
            path: {"expected": expected, "observed": expected}
            for path, expected in registration[
                "pinned_existing_production_git_blob_sha1"
            ].items()
        },
        "implementation_blobs": {
            path: {"expected": expected, "observed": expected}
            for path, expected in freeze["file_git_blob_sha1"].items()
        },
        "market_data_accessed": False,
        "development_market_outcomes_accessed": False,
        "validation_or_oos_accessed": False,
        "strategy_pnl_calculated": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
        "calibration_or_holdout_seed_used": False,
    }
    return report, freeze, registration


def test_representative_fixture_evidence_is_complete_and_synthetic(runner, fixture_evidence):
    evidence = fixture_evidence
    assert set(evidence["bundle_verification"]) == {"BTCUSDT", "ETHUSDT"}
    for accounting in evidence["primary_accounting"].values():
        assert accounting["candidate_rows"] == (
            accounting["accepted_rows"] + accounting["rejected_rows"]
        )
        assert accounting["loaded_rows"] > 0
        assert len(accounting["inventory_sha256"]) == 5

    assert evidence["support"]["BTCUSDT"]["pass"] is True
    assert evidence["support"]["ETHUSDT"]["pass"] is True
    assert len(evidence["support"]["BTCUSDT"]["cells"]) == 15
    assert len(evidence["support"]["ETHUSDT"]["cells"]) == 15

    assert set(evidence["fixture_identities"]) == {"BTCUSDT", "ETHUSDT"}
    assert all(len(value) == 64 for value in evidence["fixture_identities"].values())
    assert evidence["exact_cross_asset_join"]["count"] > 0
    fixtures = evidence["numerical_wiring"]["engineering_fixtures"]
    assert set(fixtures) == {"DEP", "TIME", "STATE"}
    assert all(
        item["classification"] == "ENGINEERING_ONLY_NOT_CALIBRATION"
        for item in fixtures.values()
    )
    assert all(item["p_value"] is None for item in fixtures.values())
    assert len(evidence["six_slot_assembly"]) == 6


def test_fp11_valid_semantics_pass(runner, fixture_evidence):
    report, freeze, registration = _fp11_report(runner, fixture_evidence)
    result = runner._evaluate_fp11(report, fixture_evidence, freeze, registration)
    assert result["pass"] is True
    assert result["checks"]
    assert all(result["checks"].values())


@pytest.mark.parametrize(
    "mutation",
    ("fixture_identity", "slot_order", "access_flag", "blob_evidence"),
)
def test_fp11_semantic_mutations_fail(runner, fixture_evidence, mutation):
    evidence = copy.deepcopy(fixture_evidence)
    report, freeze, registration = _fp11_report(runner, evidence)

    if mutation == "fixture_identity":
        evidence["fixture_identities"]["BTCUSDT"] = "0" * 64
    elif mutation == "slot_order":
        evidence["six_slot_assembly"][0], evidence["six_slot_assembly"][1] = (
            evidence["six_slot_assembly"][1],
            evidence["six_slot_assembly"][0],
        )
    elif mutation == "access_flag":
        report["market_data_accessed"] = True
    elif mutation == "blob_evidence":
        target = next(iter(report["implementation_blobs"]))
        report["implementation_blobs"][target]["observed"] = "0" * 40

    result = runner._evaluate_fp11(report, evidence, freeze, registration)
    assert result["pass"] is False
    assert not all(result["checks"].values())


def test_oracle_map_matches_registered_oracles_except_fp11_internal_inventory(runner):
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
