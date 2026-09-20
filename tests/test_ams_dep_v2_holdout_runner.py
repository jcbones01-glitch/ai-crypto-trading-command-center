import ast
import importlib.util
import json
from pathlib import Path

import pytest

from research_core.ams_dep_v2_holdout_gate import load_holdout_addendum
from research_core.release_gate import ResearchGateError, load_ams_dep_release_gate

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/scripts/run_ams_dep_v2_holdout_shard.py"
CONFIG = ROOT / "research/experiments/ams_dep_synthetic_core_v2.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("v2_holdout_runner", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_current_holdout_runner_authority_check_consumes_no_reserved_rng():
    runner = load_runner()
    gate = load_ams_dep_release_gate()
    addendum = load_holdout_addendum()
    currently_open = (
        gate.get("v2_synthetic_calibration_passed") is True
        and gate.get("v2_holdout_execution_authorized") is True
        and addendum.get("status") == "AUTHORIZED"
        and addendum.get("explicit_holdout_execution_authorized") is True
    )
    if currently_open:
        verified_gate, verified_addendum, _, _, _ = runner._verify_authority()
        assert verified_gate["v2_holdout_execution_authorized"] is True
        assert verified_addendum["explicit_holdout_execution_authorized"] is True
    else:
        with pytest.raises(ResearchGateError):
            runner._verify_authority()


def test_registered_holdout_seed_namespaces_are_separate_without_rng_instantiation():
    runner = load_runner()
    cfg = json.loads(CONFIG.read_text())
    roots = runner._seed_namespace(cfg)
    assert roots["data_calibration"] != roots["data_holdout"]
    assert len(
        {
            roots["bootstrap_engineering"],
            roots["bootstrap_calibration"],
            roots["bootstrap_holdout"],
        }
    ) == 3


def test_all_132000_holdout_tasks_are_assigned_exactly_once():
    runner = load_runner()
    cfg = json.loads(CONFIG.read_text())
    seen = set()
    counts = []
    for shard in range(128):
        tasks = list(runner._tasks_for_shard(cfg, shard))
        counts.append(len(tasks))
        for task in tasks:
            idx = task[0]
            assert idx not in seen
            assert idx % 128 == shard
            seen.add(idx)
    assert seen == set(range(132000))
    assert counts.count(1032) == 32
    assert counts.count(1031) == 96


def test_holdout_runner_has_no_market_data_imports():
    tree = ast.parse(SCRIPT.read_text())
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(node.module or "")
    forbidden = ("binance", "market_data", "historical_data", "dataset_loader")
    lowered = "\n".join(modules).lower()
    for token in forbidden:
        assert token not in lowered


def test_holdout_runner_selects_only_reserved_holdout_roots():
    text = SCRIPT.read_text()
    assert 'config["data_roots"]["holdout"]' in text
    assert 'config["bootstrap_roots"]["holdout"]' in text
    assert "--suite" not in text


def test_claim_record_requires_exact_ref_sha_and_remote_binding():
    runner = load_runner()
    addendum = {"one_shot_claim_ref": "refs/tags/fixed"}
    runner._validate_claim_record(
        addendum,
        "a" * 40,
        "refs/tags/fixed",
        "a" * 40,
        ("a" * 40) + "\trefs/tags/fixed\n",
    )
    with pytest.raises(RuntimeError, match="claim SHA"):
        runner._validate_claim_record(
            addendum,
            "a" * 40,
            "refs/tags/fixed",
            "b" * 40,
            ("b" * 40) + "\trefs/tags/fixed\n",
        )
    with pytest.raises(RuntimeError, match="claim ref"):
        runner._validate_claim_record(
            addendum,
            "a" * 40,
            "refs/tags/other",
            "a" * 40,
            ("a" * 40) + "\trefs/tags/other\n",
        )


def test_run_slot_rejects_direct_call_without_authorization_context():
    runner = load_runner()
    with pytest.raises(RuntimeError, match="authorization context"):
        runner._run_slot(
            None,
            {},
            0,
            "iid_null",
            0,
            0,
            0,
            "DEP",
        )


def test_forged_constructed_context_cannot_reach_reserved_holdout_roots(monkeypatch):
    runner = load_runner()
    forged = runner._HoldoutExecutionContext("fake-ref", "fake-sha")

    reached_simulation = False

    def forbidden_simulation(*args, **kwargs):
        nonlocal reached_simulation
        reached_simulation = True
        raise AssertionError("reserved holdout simulation must not be reached")

    monkeypatch.setattr(runner, "simulate_case", forbidden_simulation)

    # Empty config is intentional: context verification must fail before either
    # reserved holdout root is read from config.
    with pytest.raises(RuntimeError, match="active verified authorization context"):
        runner._run_slot(
            forged,
            {},
            0,
            "iid_null",
            0,
            0,
            0,
            "DEP",
        )
    assert reached_simulation is False


def test_only_activated_context_identity_is_accepted():
    runner = load_runner()
    forged = runner._HoldoutExecutionContext("same-ref", "same-sha")
    active = runner._activate_context("same-ref", "same-sha")

    with pytest.raises(RuntimeError, match="active verified authorization context"):
        runner._require_context(forged)
    assert runner._require_context(active) is active
