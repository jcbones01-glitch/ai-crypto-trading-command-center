from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import threading
from urllib.error import HTTPError

import numpy as np
import pytest

import research_core.psr01b_execution_lock as lock
import research_core.psr01b_runner as runner
from research_core.data_interfaces import MarketBar
from research_core.psr01b_core import PSR01BError
from research_core.psr01b_preflight import verify_execution_authorization_scope

UTC = timezone.utc


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


class AtomicFakeGitHub:
    def __init__(self):
        self.guard = threading.Lock()
        self.refs = {}
        self.tag_objects = {}
        self.next_tag = 1

    def __call__(self, request):
        method = request.get_method()
        if method == "GET":
            if "/git/tags/" in request.full_url:
                tag_sha = request.full_url.rsplit("/", 1)[-1]
                if tag_sha in self.tag_objects:
                    return FakeResponse(self.tag_objects[tag_sha])
            for ref, sha in self.refs.items():
                short = ref.removeprefix("refs/")
                if request.full_url.endswith("/git/ref/" + short):
                    return FakeResponse({"ref": ref, "object": {"sha": sha}})
            raise HTTPError(
                request.full_url,
                404,
                "Not Found",
                {},
                io.BytesIO(b'{"message":"Not Found"}'),
            )

        payload = json.loads(request.data)
        if request.full_url.endswith("/git/tags"):
            with self.guard:
                tag_sha = f"{self.next_tag:040x}"
                self.next_tag += 1
                created = {
                    "sha": tag_sha,
                    "tag": payload["tag"],
                    "message": payload["message"],
                    "object": {
                        "sha": payload["object"],
                        "type": payload["type"],
                    },
                }
                self.tag_objects[tag_sha] = created
                return FakeResponse(created)

        ref = payload["ref"]
        with self.guard:
            if ref in self.refs:
                raise HTTPError(
                    request.full_url,
                    422,
                    "Reference exists",
                    {},
                    io.BytesIO(b'{"message":"Reference exists"}'),
                )
            self.refs[ref] = payload["sha"]
            return FakeResponse({"ref": ref, "object": {"sha": payload["sha"]}})


def _authorized_scope():
    candidate = "a" * 40
    return {
        "implementation": {"implementation_candidate_commit": candidate},
        "future_governance": {
            "execution_authorized": True,
            "execution_scope": {
                "registration_id": "PSR01B-BOUNDED-DEVELOPMENT-SPOT-V1",
                "revision": 4,
                "implementation_candidate_commit": candidate,
                "symbol": "BTCUSDT",
                "market": "spot",
                "timeframe": "1h",
                "source_start": "2017-12-01T00:00:00Z",
                "source_end_exclusive": "2022-01-01T00:00:00Z",
                "execution_limit": 1,
                "one_shot_claim_ref": "refs/tags/psr01b-development-one-shot-claim-v1",
            },
        },
        "protected_access": {
            "empirical_binance_archive_access_authorized": True,
            "empirical_feature_generation_authorized": True,
            "empirical_model_fit_authorized": True,
            "empirical_forecast_generation_authorized": True,
            "empirical_pnl_authorized": True,
            "validation_or_oos_access_authorized": False,
            "paper_trading_authorized": False,
            "live_trading_authorized": False,
            "leverage_authorized": False,
            "derivatives_execution_authorized": False,
        },
    }


def test_authorized_scope_requires_bounded_empirical_true_and_protected_false():
    observed = verify_execution_authorization_scope(_authorized_scope())
    assert observed["execution_scope"]["execution_limit"] == 1
    assert observed["permissions"]["empirical_model_fit_authorized"] is True
    assert observed["permissions"]["validation_or_oos_access_authorized"] is False

    bad = _authorized_scope()
    bad["future_governance"]["execution_scope"]["symbol"] = "ETHUSDT"
    with pytest.raises(PSR01BError, match="execution scope record mismatch"):
        verify_execution_authorization_scope(bad)

    bad = _authorized_scope()
    bad["protected_access"]["validation_or_oos_access_authorized"] = True
    with pytest.raises(PSR01BError, match="protected scope must remain false"):
        verify_execution_authorization_scope(bad)

    bad = _authorized_scope()
    bad["protected_access"]["empirical_forecast_generation_authorized"] = False
    with pytest.raises(PSR01BError, match="authorized Development scope missing"):
        verify_execution_authorization_scope(bad)


def test_claim_is_atomic_run_bound_duplicate_consumed_and_race_has_one_winner():
    env = {
        "GITHUB_RUN_ID": "123",
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_ACTOR": "reviewed-operator",
    }
    backend = AtomicFakeGitHub()
    lock.assert_claim_absent("owner/repo", "token", opener=backend)
    claim = lock.create_claim(
        "owner/repo", "a" * 40, "token", environ=env, opener=backend
    )
    assert claim["ref"] == lock.DEFAULT_CLAIM_REF
    assert claim["sha"] == "a" * 40
    assert claim["run_id"] == "123"
    assert backend.refs[lock.DEFAULT_CLAIM_REF] == claim["tag_object_sha"]

    forwarded = {
        **env,
        "GITHUB_REPOSITORY": "owner/repo",
        "GITHUB_TOKEN": "token",
        "PSR01B_DEVELOPMENT_V1_CLAIM_REF": lock.DEFAULT_CLAIM_REF,
        "PSR01B_DEVELOPMENT_V1_CLAIM_SHA": "a" * 40,
        "PSR01B_DEVELOPMENT_V1_CLAIM_TAG_OBJECT_SHA": claim["tag_object_sha"],
        "PSR01B_DEVELOPMENT_V1_CLAIM_RUN_ID": "123",
    }
    assert lock.assert_claim_environment(
        "a" * 40, environ=forwarded, opener=backend
    )["run_id"] == "123"
    replay = {
        **forwarded,
        "GITHUB_RUN_ID": "124",
        "PSR01B_DEVELOPMENT_V1_CLAIM_RUN_ID": "124",
    }
    with pytest.raises(PSR01BError, match="belongs to another workflow run"):
        lock.assert_claim_environment("a" * 40, environ=replay, opener=backend)

    with pytest.raises(PSR01BError, match="already exists"):
        lock.create_claim(
            "owner/repo", "a" * 40, "token", environ=env, opener=backend
        )

    race = AtomicFakeGitHub()
    success, failure = [], []

    def attempt():
        try:
            success.append(
                lock.create_claim(
                    "owner/repo", "b" * 40, "token", environ=env, opener=race
                )
            )
        except PSR01BError as exc:
            failure.append(str(exc))

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(success) == 1
    assert len(failure) == 1


def test_forged_claim_environment_fails_without_live_ref(monkeypatch):
    sha = "c" * 40
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setenv("GITHUB_RUN_ID", "123")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    monkeypatch.setenv("GITHUB_ACTOR", "reviewed-operator")
    monkeypatch.setenv("PSR01B_DEVELOPMENT_V1_CLAIM_REF", lock.DEFAULT_CLAIM_REF)
    monkeypatch.setenv("PSR01B_DEVELOPMENT_V1_CLAIM_SHA", sha)
    monkeypatch.setenv("PSR01B_DEVELOPMENT_V1_CLAIM_TAG_OBJECT_SHA", "d" * 40)
    monkeypatch.setenv("PSR01B_DEVELOPMENT_V1_CLAIM_RUN_ID", "123")
    with pytest.raises(PSR01BError, match="does not exist"):
        lock.assert_claim_environment(sha, opener=AtomicFakeGitHub())


def test_live_review_anchor_must_equal_candidate():
    candidate = "d" * 40
    freeze = {
        "review_anchor_ref": lock.DEFAULT_REVIEW_ANCHOR_REF,
        "review_anchor_sha": candidate,
    }
    backend = AtomicFakeGitHub()
    backend.refs[lock.DEFAULT_REVIEW_ANCHOR_REF] = candidate
    observed = lock.assert_review_anchor(
        candidate,
        freeze,
        repository="owner/repo",
        token="token",
        opener=backend,
    )
    assert observed["sha"] == candidate
    backend.refs[lock.DEFAULT_REVIEW_ANCHOR_REF] = "e" * 40
    with pytest.raises(PSR01BError, match="target mismatch"):
        lock.assert_review_anchor(
            candidate,
            freeze,
            repository="owner/repo",
            token="token",
            opener=backend,
        )


def test_manual_confirmation_binds_candidate_execution_actor_and_run():
    candidate = "a" * 40
    execution = "b" * 40
    env = {
        "GITHUB_EVENT_NAME": "workflow_dispatch",
        "GITHUB_ACTOR": "reviewed-operator",
        "GITHUB_RUN_ID": "123",
        "GITHUB_RUN_ATTEMPT": "1",
    }
    exact = lock.expected_confirmation(candidate, execution)
    evidence = lock.assert_manual_confirmation(
        candidate, execution, confirmation=exact, environ=env
    )
    assert evidence["actor"] == "reviewed-operator"
    assert evidence["run_id"] == "123"
    with pytest.raises(PSR01BError, match="exact PSR-01B manual confirmation"):
        lock.assert_manual_confirmation(
            candidate, execution, confirmation="wrong", environ=env
        )


def _git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def test_execution_commit_and_candidate_blob_contract_direct_against_scratch_git(
    tmp_path, monkeypatch
):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "psr01b@example.invalid"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "PSR01B Synthetic Test"],
        cwd=tmp_path,
        check=True,
    )
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("candidate\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "candidate"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    candidate = _git(tmp_path, "rev-parse", "HEAD")
    candidate_blob = _git(tmp_path, "rev-parse", f"{candidate}:tracked.txt")

    freeze_path = (
        tmp_path / "research/governance/psr01b_implementation_freeze_v1.json"
    )
    freeze_path.parent.mkdir(parents=True)
    freeze_path.write_text("{}\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", "research/governance/psr01b_implementation_freeze_v1.json"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "governance"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    governance = _git(tmp_path, "rev-parse", "HEAD")

    monkeypatch.setattr(lock, "ROOT", tmp_path)
    assert lock.verify_execution_commit(candidate, governance) == (
        "research/governance/psr01b_implementation_freeze_v1.json",
    )
    assert lock.verify_candidate_blob_contract(
        candidate, {"tracked.txt": candidate_blob}
    ) == {"tracked.txt": candidate_blob}

    tracked.write_text("tampered\n", encoding="utf-8")
    with pytest.raises(PSR01BError, match="checkout differs"):
        lock.verify_candidate_blob_contract(
            candidate, {"tracked.txt": candidate_blob}
        )

    tracked.write_text("candidate\n", encoding="utf-8")
    forbidden = tmp_path / "forbidden.txt"
    forbidden.write_text("changed\n", encoding="utf-8")
    subprocess.run(["git", "add", "forbidden.txt"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "forbidden"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    forbidden_head = _git(tmp_path, "rev-parse", "HEAD")
    with pytest.raises(PSR01BError, match="unapproved post-candidate path changed"):
        lock.verify_execution_commit(candidate, forbidden_head)


def test_cli_preflight_and_claim_use_env_confirmation_and_emit_run_bound_claim(
    tmp_path, monkeypatch, capsys
):
    candidate = "a" * 40
    execution = "b" * 40
    confirmation = lock.expected_confirmation(candidate, execution)
    fake_freeze = {"implementation": {"implementation_candidate_commit": candidate}}
    calls = []

    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setenv("GITHUB_RUN_ID", "321")
    monkeypatch.setenv("GITHUB_RUN_ATTEMPT", "1")
    monkeypatch.setenv("GITHUB_ACTOR", "reviewed-operator")
    monkeypatch.setenv("PSR01B_DEVELOPMENT_V1_CONFIRMATION", confirmation)
    monkeypatch.setattr(runner, "load_implementation_freeze", lambda: fake_freeze)
    monkeypatch.setattr(
        runner,
        "verify_frozen_execution_identity",
        lambda **kwargs: {"implementation_candidate_commit": candidate},
    )

    def fake_preclaim(candidate_arg, freeze_arg, result_path, **kwargs):
        calls.append(("preclaim", candidate_arg, kwargs["confirmation"]))
        return {"executing_sha": kwargs["executing_sha"]}

    monkeypatch.setattr(lock, "assert_preclaim_environment", fake_preclaim)
    monkeypatch.setattr(
        lock,
        "create_claim",
        lambda repository, sha, token, **kwargs: {
            "ref": lock.DEFAULT_CLAIM_REF,
            "sha": sha,
            "tag_object_sha": "c" * 40,
            "run_id": "321",
            "run_attempt": "1",
            "actor": "reviewed-operator",
        },
    )

    result_path = tmp_path / "result.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "psr01b_execution_lock",
            "preflight",
            "--repository",
            "owner/repo",
            "--sha",
            execution,
            "--result-path",
            str(result_path),
        ],
    )
    lock.main()
    assert "PSR01B_DEVELOPMENT_V1_PREFLIGHT_PASS" in capsys.readouterr().out
    assert calls[-1] == ("preclaim", candidate, confirmation)

    output = tmp_path / "github-output.txt"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "psr01b_execution_lock",
            "claim",
            "--repository",
            "owner/repo",
            "--sha",
            execution,
            "--result-path",
            str(result_path),
            "--github-output",
            str(output),
        ],
    )
    lock.main()
    written = output.read_text(encoding="utf-8")
    assert f"claim_ref={lock.DEFAULT_CLAIM_REF}" in written
    assert f"claim_sha={execution}" in written
    assert f"claim_tag_object_sha={'c' * 40}" in written
    assert "claim_run_id=321" in written


def test_result_path_reservation_and_atomic_write_never_overwrite(tmp_path):
    result = tmp_path / "result.json"
    candidate = "a" * 40
    execution = "b" * 40
    reservation = lock.reserve_result_path(
        result, candidate=candidate, executing_sha=execution
    )
    assert lock.assert_result_reservation(
        result, candidate=candidate, executing_sha=execution
    ) == reservation
    with pytest.raises(PSR01BError, match="identity mismatch"):
        lock.assert_result_reservation(
            result, candidate=candidate, executing_sha="c" * 40
        )

    runner.write_result_json(result, {"b": 2, "a": 1})
    assert json.loads(result.read_text()) == {"a": 1, "b": 2}
    with pytest.raises(PSR01BError, match="already exists"):
        runner.write_result_json(result, {"a": 9})


def test_execution_workflow_is_manual_only_and_ordered():
    text = (
        lock.ROOT / ".github/workflows/psr01b-development-execution-v1.yml"
    ).read_text()
    assert "workflow_dispatch:" in text
    for forbidden in (
        "pull_request:",
        "push:",
        "schedule:",
        "repository_dispatch:",
        "workflow_run:",
    ):
        assert forbidden not in text
    positions = [
        text.index("Run full 11x2 production-math synthetic dry run"),
        text.index("Reserve result path and verify authority before claim"),
        text.index("Atomically create durable PSR-01B one-shot claim"),
        text.index("Reverify durable claim and run registered Development execution"),
    ]
    assert positions == sorted(positions)
    assert lock.DEFAULT_CLAIM_REF in text
    assert "contents: write" in text
    assert "python-version: '3.12.14'" in text
    assert "--confirmation" not in text
    assert "PSR01B_DEVELOPMENT_V1_CONFIRMATION:" in text
    assert "PSR01B_DEVELOPMENT_V1_CLAIM_TAG_OBJECT_SHA:" in text
    assert "PSR01B_DEVELOPMENT_V1_CLAIM_RUN_ID:" in text


def _full_synthetic_bars():
    start = datetime(2017, 12, 1, tzinfo=UTC)
    end = datetime(2022, 1, 1, tzinfo=UTC)
    gap_start = datetime(2020, 5, 1, tzinfo=UTC)
    gap_end = gap_start + timedelta(hours=2)
    rng = np.random.Generator(np.random.PCG64(2026092502))
    out = []
    previous_close = 10_000.0
    stamp = start
    i = 0
    while stamp < end:
        cyclical = 0.00032 * math.sin(i / 17.0) + 0.00018 * math.cos(i / 73.0)
        close = previous_close * math.exp(
            cyclical + float(rng.normal(0.0, 0.00115))
        )
        open_value = previous_close * math.exp(float(rng.normal(0.0, 0.00025)))
        spread = 0.0008 + abs(float(rng.normal(0.0, 0.0002)))
        high = max(open_value, close) * (1.0 + spread)
        low = min(open_value, close) / (1.0 + spread)
        volume = math.exp(math.log(125.0) + float(rng.normal(0.0, 0.18)))
        if not (gap_start <= stamp < gap_end):
            out.append(
                MarketBar(
                    timestamp=stamp,
                    symbol="BTCUSDT",
                    open=Decimal(f"{open_value:.12f}"),
                    high=Decimal(f"{high:.12f}"),
                    low=Decimal(f"{low:.12f}"),
                    close=Decimal(f"{close:.12f}"),
                    volume=Decimal(f"{volume:.12f}"),
                )
            )
        previous_close = close
        stamp += timedelta(hours=1)
        i += 1
    return tuple(out)


@pytest.mark.skipif(
    os.environ.get("PSR01B_FULL_SYNTHETIC_DRY_RUN") != "1",
    reason="full 11x2 production-math dry run executes only in dedicated CI",
)
def test_full_11x2_production_math_synthetic_dry_run(tmp_path):
    result = runner.run_from_normalized_bars(_full_synthetic_bars())
    assert [x["fold"] for x in result["arms"]["PAPER_FILL"]["folds"]] == list(range(1, 12))
    assert [x["fold"] for x in result["arms"]["PROJECT_GAP_PRESERVING"]["folds"]] == list(range(1, 12))
    assert result["execution_order"]["arms"] == ["PAPER_FILL", "PROJECT_GAP_PRESERVING"]
    assert result["execution_order"]["bootstrap_hours"] == [168, 24, 72]
    first, second = tmp_path / "one.json", tmp_path / "two.json"
    runner.write_result_json(first, result)
    runner.write_result_json(second, result)
    assert first.read_bytes() == second.read_bytes()
    print("PSR01B_FULL_11X2_SYNTHETIC_DRY_RUN_PASS")
