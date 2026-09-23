from __future__ import annotations

import io
import json
import threading
from urllib.error import HTTPError

import pytest

import research_core.ams_dep_development_execution_lock_v2 as lock


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
                {"ref": ref, "object": {"sha": payload["sha"]}}
            )


def test_v2_claim_absent_then_create_then_duplicate_fails():
    backend = AtomicFakeGitHub()
    lock.assert_claim_absent("owner/repo", "token", opener=backend)
    claim = lock.create_claim(
        "owner/repo", "a" * 40, "token", opener=backend
    )
    assert claim == {"ref": lock.DEFAULT_CLAIM_REF, "sha": "a" * 40}
    with pytest.raises(lock.DevelopmentExecutionV2Error, match="already exists"):
        lock.create_claim(
            "owner/repo", "a" * 40, "token", opener=backend
        )


def test_simultaneous_v2_claim_has_exactly_one_winner():
    backend = AtomicFakeGitHub()
    success = []
    failure = []

    def attempt():
        try:
            success.append(
                lock.create_claim(
                    "owner/repo", "b" * 40, "token", opener=backend
                )
            )
        except lock.DevelopmentExecutionV2Error as exc:
            failure.append(str(exc))

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(success) == 1
    assert len(failure) == 1


def test_v1_claim_cannot_satisfy_v2_claim_contract(monkeypatch):
    sha = "c" * 40
    monkeypatch.setenv("GITHUB_SHA", sha)
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setenv(
        "AMS_DEP_DEVELOPMENT_V2_CLAIM_REF",
        "refs/tags/ams-dep-development-execution-claimed-v1",
    )
    monkeypatch.setenv("AMS_DEP_DEVELOPMENT_V2_CLAIM_SHA", sha)
    backend = AtomicFakeGitHub()
    backend.refs[
        "refs/tags/ams-dep-development-execution-claimed-v1"
    ] = sha
    with pytest.raises(
        lock.DevelopmentExecutionV2Error,
        match="V2 claim ref is missing or incorrect",
    ):
        lock.assert_claim_environment(opener=backend)


def _set_v2_claim_env(monkeypatch, sha):
    monkeypatch.setenv("GITHUB_SHA", sha)
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
    monkeypatch.setenv("GITHUB_TOKEN", "token")
    monkeypatch.setenv(
        "AMS_DEP_DEVELOPMENT_V2_CLAIM_REF",
        lock.DEFAULT_CLAIM_REF,
    )
    monkeypatch.setenv("AMS_DEP_DEVELOPMENT_V2_CLAIM_SHA", sha)


def test_forged_v2_environment_without_durable_ref_fails(monkeypatch):
    sha = "d" * 40
    _set_v2_claim_env(monkeypatch, sha)
    with pytest.raises(
        lock.DevelopmentExecutionV2Error,
        match="does not exist",
    ):
        lock.assert_claim_environment(opener=AtomicFakeGitHub())


def test_wrong_or_repointed_v2_claim_target_fails(monkeypatch):
    sha = "e" * 40
    _set_v2_claim_env(monkeypatch, sha)
    backend = AtomicFakeGitHub()
    backend.refs[lock.DEFAULT_CLAIM_REF] = "f" * 40
    with pytest.raises(
        lock.DevelopmentExecutionV2Error,
        match="target mismatch",
    ):
        lock.assert_claim_environment(opener=backend)


def test_correct_v2_claim_target_passes(monkeypatch):
    sha = "a" * 40
    _set_v2_claim_env(monkeypatch, sha)
    backend = AtomicFakeGitHub()
    backend.refs[lock.DEFAULT_CLAIM_REF] = sha
    assert lock.assert_claim_environment(opener=backend) == {
        "ref": lock.DEFAULT_CLAIM_REF,
        "sha": sha,
    }


def test_v2_review_anchor_is_distinct_and_fixed():
    assert lock.DEFAULT_REVIEW_ANCHOR_REF == (
        "refs/heads/ams-dep-development-implementation-reviewed-v2"
    )
    assert lock.DEFAULT_CLAIM_REF == (
        "refs/tags/ams-dep-development-execution-claimed-v2"
    )
    backend = AtomicFakeGitHub()
    created = lock.create_fixed_ref(
        "owner/repo",
        "a" * 40,
        "token",
        ref=lock.DEFAULT_REVIEW_ANCHOR_REF,
        opener=backend,
    )
    assert created["sha"] == "a" * 40
    with pytest.raises(lock.DevelopmentExecutionV2Error, match="already exists"):
        lock.create_fixed_ref(
            "owner/repo",
            "b" * 40,
            "token",
            ref=lock.DEFAULT_REVIEW_ANCHOR_REF,
            opener=backend,
        )


def test_only_registered_v2_governance_paths_may_change():
    assert lock.ALLOWED_POST_CANDIDATE_PATHS == {
        "research/governance/ams_dep_development_implementation_freeze_v2.json",
        "research/governance/ams_dep_development_execution_manifest_v2.json",
        "research/governance/ams_dep_release_gate_v1.json",
    }


def test_exact_v2_implementation_path_set_is_hard_coded():
    assert lock.EXPECTED_IMPLEMENTATION_PATHS == {
        ".github/workflows/ams-dep-development-empirical-v2.yml",
        "research/scripts/run_ams_dep_development_empirical_v2.py",
        "src/research_core/ams_dep_treatment_aware_normalization_v2.py",
        "src/research_core/ams_dep_development_source_v2.py",
        "src/research_core/ams_dep_empirical_access_v2.py",
        "src/research_core/ams_dep_development_execution_lock_v2.py",
        "tests/test_ams_dep_development_v2_authorized_preflight.py",
        "tests/test_ams_dep_development_v2_execution_lock.py",
        "tests/test_ams_dep_development_v2_normalization.py",
        "tests/test_ams_dep_development_v2_runner.py",
        "tests/test_ams_dep_development_v2_source.py",
        "tests/test_ams_dep_development_v2_workflow.py",
    }


def test_freeze_pin_deletion_cannot_reduce_v2_protected_set():
    registration = lock.load_development_registration()
    freeze = {
        "implementation_file_git_blob_sha1": {
            path: "a" * 40 for path in lock.EXPECTED_IMPLEMENTATION_PATHS
        },
        "pinned_upstream_git_blob_sha1":
            registration["pinned_upstream_git_blob_sha1"],
    }
    freeze["implementation_file_git_blob_sha1"].pop(
        "research/scripts/run_ams_dep_development_empirical_v2.py"
    )
    with pytest.raises(
        lock.DevelopmentExecutionV2Error,
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
    victim = "research/scripts/run_ams_dep_development_empirical_v2.py"
    freeze["implementation_file_git_blob_sha1"][victim] = "0" * 40
    with pytest.raises(
        lock.DevelopmentExecutionV2Error,
        match="blob mismatch",
    ):
        lock.verify_frozen_implementation(freeze)
