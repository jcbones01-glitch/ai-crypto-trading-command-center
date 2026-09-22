from __future__ import annotations

import io
import json
import threading
from urllib.error import HTTPError

import pytest

import research_core.ams_dep_development_execution_lock as lock
from research_core.release_gate import ResearchGateError


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
        self.created = None

    def __call__(self, request):
        method = request.get_method()
        if method == "GET":
            with self.guard:
                if self.created is None:
                    raise HTTPError(
                        request.full_url,
                        404,
                        "Not Found",
                        {},
                        io.BytesIO(b'{"message":"Not Found"}'),
                    )
                return FakeResponse(
                    {
                        "ref": self.created["ref"],
                        "object": {"sha": self.created["sha"]},
                    }
                )

        payload = json.loads(request.data)
        with self.guard:
            if self.created is not None:
                raise HTTPError(
                    request.full_url,
                    422,
                    "Reference already exists",
                    {},
                    io.BytesIO(b'{"message":"Reference already exists"}'),
                )
            self.created = payload
            return FakeResponse(
                {
                    "ref": payload["ref"],
                    "object": {"sha": payload["sha"]},
                }
            )


def test_current_machine_gate_blocks_before_execution_manifest(monkeypatch):
    called = False

    def forbidden_manifest():
        nonlocal called
        called = True
        raise AssertionError("execution manifest must not be reached")

    monkeypatch.setattr(lock, "load_development_execution_manifest", forbidden_manifest)
    with pytest.raises(ResearchGateError, match="empirical execution blocked"):
        lock.assert_development_execution_allowed("a" * 40)
    assert called is False


def test_current_execution_manifest_is_locked():
    manifest = lock.load_development_execution_manifest()
    assert manifest["status"] == "DRAFT_LOCKED"
    assert manifest["development_execution_authorized"] is False
    assert manifest["first_empirical_execution_claimed"] is False
    assert manifest["first_empirical_execution_executed"] is False
    assert manifest["reviewed_implementation_commit"] is None


def test_claim_absent_then_atomic_create_then_second_create_fails():
    backend = AtomicFakeGitHub()
    lock.assert_claim_absent("owner/repo", "token", opener=backend)
    claim = lock.create_claim(
        "owner/repo",
        "a" * 40,
        "token",
        opener=backend,
    )
    assert claim == {"ref": lock.DEFAULT_CLAIM_REF, "sha": "a" * 40}
    with pytest.raises(lock.DevelopmentExecutionError, match="already exists"):
        lock.create_claim(
            "owner/repo",
            "a" * 40,
            "token",
            opener=backend,
        )


def test_simultaneous_claim_creation_has_one_winner():
    backend = AtomicFakeGitHub()
    successes = []
    failures = []

    def attempt():
        try:
            successes.append(
                lock.create_claim(
                    "owner/repo",
                    "b" * 40,
                    "token",
                    opener=backend,
                )
            )
        except lock.DevelopmentExecutionError as exc:
            failures.append(str(exc))

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(successes) == 1
    assert len(failures) == 1
    assert "already exists" in failures[0]


def test_claim_ref_is_fixed():
    with pytest.raises(lock.DevelopmentExecutionError, match="unexpected Development claim ref"):
        lock.create_claim(
            "owner/repo",
            "a" * 40,
            "token",
            ref="refs/tags/not-the-registered-claim",
            opener=AtomicFakeGitHub(),
        )


def test_claim_environment_requires_exact_ref_and_execution_sha(monkeypatch):
    monkeypatch.setenv("GITHUB_SHA", "c" * 40)
    monkeypatch.setenv("AMS_DEP_DEVELOPMENT_CLAIM_REF", lock.DEFAULT_CLAIM_REF)
    monkeypatch.setenv("AMS_DEP_DEVELOPMENT_CLAIM_SHA", "c" * 40)
    assert lock.assert_claim_environment() == {
        "ref": lock.DEFAULT_CLAIM_REF,
        "sha": "c" * 40,
    }

    monkeypatch.setenv("AMS_DEP_DEVELOPMENT_CLAIM_SHA", "d" * 40)
    with pytest.raises(lock.DevelopmentExecutionError, match="claim SHA mismatch"):
        lock.assert_claim_environment()


def test_only_governance_paths_may_change_after_candidate():
    assert lock.ALLOWED_POST_CANDIDATE_PATHS == {
        "research/governance/ams_dep_development_implementation_freeze_v1.json",
        "research/governance/ams_dep_development_execution_manifest_v1.json",
        "research/governance/ams_dep_release_gate_v1.json",
    }
