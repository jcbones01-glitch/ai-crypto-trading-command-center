from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import io
import json
import math
import os
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

    def __call__(self, request):
        if request.get_method() == "GET":
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


def test_claim_is_atomic_duplicate_is_consumed_and_race_has_one_winner():
    backend = AtomicFakeGitHub()
    lock.assert_claim_absent("owner/repo", "token", opener=backend)
    claim = lock.create_claim("owner/repo", "a" * 40, "token", opener=backend)
    assert claim == {"ref": lock.DEFAULT_CLAIM_REF, "sha": "a" * 40}
    with pytest.raises(PSR01BError, match="already exists"):
        lock.create_claim("owner/repo", "a" * 40, "token", opener=backend)

    race = AtomicFakeGitHub()
    success, failure = [], []

    def attempt():
        try:
            success.append(lock.create_claim("owner/repo", "b" * 40, "token", opener=race))
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
    monkeypatch.setenv("PSR01B_DEVELOPMENT_V1_CLAIM_REF", lock.DEFAULT_CLAIM_REF)
    monkeypatch.setenv("PSR01B_DEVELOPMENT_V1_CLAIM_SHA", sha)
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
