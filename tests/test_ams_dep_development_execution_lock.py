from __future__ import annotations

import io
import json
import threading
from urllib.error import HTTPError

import pytest

import research_core.ams_dep_development_execution_lock as lock


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
        method = request.get_method()
        if method == "GET":
            for ref, sha in self.refs.items():
                short = ref.removeprefix("refs/")
                if request.full_url.endswith("/git/ref/" + short):
                    return FakeResponse(
                        {"ref": ref, "object": {"sha": sha}}
                    )
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
                    "Reference already exists",
                    {},
                    io.BytesIO(b'{"message":"Reference already exists"}'),
                )
            self.refs[ref] = payload["sha"]
            return FakeResponse(
                {
                    "ref": ref,
                    "object": {"sha": payload["sha"]},
                }
            )


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
    with pytest.raises(
        lock.DevelopmentExecutionError,
        match="unexpected Development claim ref",
    ):
        lock.create_claim(
            "owner/repo",
            "a" * 40,
            "token",
            ref="refs/tags/not-the-registered-claim",
            opener=AtomicFakeGitHub(),
        )


def test_review_anchor_is_fixed_and_one_shot():
    backend = AtomicFakeGitHub()
    created = lock.create_fixed_ref(
        "owner/repo",
        "a" * 40,
        "token",
        ref=lock.DEFAULT_REVIEW_ANCHOR_REF,
        opener=backend,
    )
    assert created == {
        "ref": lock.DEFAULT_REVIEW_ANCHOR_REF,
        "sha": "a" * 40,
    }
    with pytest.raises(lock.DevelopmentExecutionError, match="already exists"):
        lock.create_fixed_ref(
            "owner/repo",
            "b" * 40,
            "token",
            ref=lock.DEFAULT_REVIEW_ANCHOR_REF,
            opener=backend,
        )


def _claim_backend(sha: str | None):
    backend = AtomicFakeGitHub()
    if sha is not None:
        backend.refs[lock.DEFAULT_CLAIM_REF] = sha
    return backend


def _set_forwarded_claim(monkeypatch, sha: str):
    monkeypatch.setenv("GITHUB_SHA", sha)
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setenv(
        "AMS_DEP_DEVELOPMENT_CLAIM_REF",
        lock.DEFAULT_CLAIM_REF,
    )
    monkeypatch.setenv("AMS_DEP_DEVELOPMENT_CLAIM_SHA", sha)


def test_forged_environment_without_durable_claim_fails(monkeypatch):
    sha = "c" * 40
    _set_forwarded_claim(monkeypatch, sha)
    with pytest.raises(
        lock.DevelopmentExecutionError,
        match="durable Development claim does not exist",
    ):
        lock.assert_claim_environment(opener=_claim_backend(None))


def test_wrong_durable_claim_target_fails(monkeypatch):
    sha = "c" * 40
    _set_forwarded_claim(monkeypatch, sha)
    with pytest.raises(
        lock.DevelopmentExecutionError,
        match="durable Development claim target mismatch",
    ):
        lock.assert_claim_environment(
            opener=_claim_backend("d" * 40)
        )


def test_deleted_or_repointed_claim_is_detected(monkeypatch):
    sha = "c" * 40
    _set_forwarded_claim(monkeypatch, sha)
    backend = _claim_backend(sha)
    assert lock.assert_claim_environment(opener=backend) == {
        "ref": lock.DEFAULT_CLAIM_REF,
        "sha": sha,
    }

    del backend.refs[lock.DEFAULT_CLAIM_REF]
    with pytest.raises(
        lock.DevelopmentExecutionError,
        match="durable Development claim does not exist",
    ):
        lock.assert_claim_environment(opener=backend)

    backend.refs[lock.DEFAULT_CLAIM_REF] = "d" * 40
    with pytest.raises(
        lock.DevelopmentExecutionError,
        match="durable Development claim target mismatch",
    ):
        lock.assert_claim_environment(opener=backend)


def test_correct_durable_claim_and_forwarded_values_pass(monkeypatch):
    sha = "e" * 40
    _set_forwarded_claim(monkeypatch, sha)
    assert lock.assert_claim_environment(
        opener=_claim_backend(sha)
    ) == {
        "ref": lock.DEFAULT_CLAIM_REF,
        "sha": sha,
    }


def test_only_governance_paths_may_change_after_candidate():
    assert lock.ALLOWED_POST_CANDIDATE_PATHS == {
        "research/governance/ams_dep_development_implementation_freeze_v1.json",
        "research/governance/ams_dep_development_execution_manifest_v1.json",
        "research/governance/ams_dep_release_gate_v1.json",
    }


def test_exact_frozen_implementation_path_set_is_hard_coded():
    assert lock.EXPECTED_IMPLEMENTATION_PATHS == {
        ".github/workflows/ams-dep-development-empirical-v1.yml",
        "research/scripts/run_ams_dep_development_empirical_v1.py",
        "src/research_core/ams_dep_development_execution_lock.py",
        "src/research_core/ams_dep_development_source.py",
        "src/research_core/ams_dep_empirical_access.py",
        "tests/test_ams_dep_development_authorized_preflight.py",
        "tests/test_ams_dep_development_execution_lock.py",
        "tests/test_ams_dep_development_runner.py",
        "tests/test_ams_dep_development_source.py",
        "tests/test_ams_dep_development_workflow.py",
    }


def test_freeze_path_deletion_cannot_reduce_required_set():
    registration = lock.load_development_registration()
    freeze = {
        "implementation_file_git_blob_sha1": {
            path: "a" * 40 for path in lock.EXPECTED_IMPLEMENTATION_PATHS
        },
        "pinned_upstream_git_blob_sha1":
            registration["pinned_upstream_git_blob_sha1"],
    }
    freeze["implementation_file_git_blob_sha1"].pop(
        "research/scripts/run_ams_dep_development_empirical_v1.py"
    )
    with pytest.raises(
        lock.DevelopmentExecutionError,
        match="path set is incomplete or altered",
    ):
        lock.verify_frozen_implementation(freeze)


def test_freeze_pin_value_replacement_is_rejected():
    registration = lock.load_development_registration()
    implementation = {
        path: lock._git_blob(path)
        for path in lock.EXPECTED_IMPLEMENTATION_PATHS
    }
    freeze = {
        "implementation_file_git_blob_sha1": implementation,
        "pinned_upstream_git_blob_sha1":
            registration["pinned_upstream_git_blob_sha1"],
    }
    victim = "research/scripts/run_ams_dep_development_empirical_v1.py"
    freeze["implementation_file_git_blob_sha1"][victim] = "0" * 40

    with pytest.raises(
        lock.DevelopmentExecutionError,
        match="frozen implementation blob mismatch",
    ):
        lock.verify_frozen_implementation(freeze)
