import importlib.util
import io
import json
import threading
from pathlib import Path
from urllib.error import HTTPError

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/scripts/claim_ams_dep_v2_holdout.py"
WORKFLOW = ROOT / ".github/workflows/ams-dep-v2-frozen-holdout.yml"


def load_claim():
    spec = importlib.util.spec_from_file_location("v2_holdout_claim", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


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
        self.lock = threading.Lock()
        self.created = None

    def __call__(self, request):
        payload = json.loads(request.data)
        with self.lock:
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


def test_first_dispatch_creates_fixed_claim():
    mod = load_claim()
    backend = AtomicFakeGitHub()
    result = mod.create_claim(
        "owner/repo",
        "a" * 40,
        "token",
        opener=backend,
    )
    assert result == {
        "ref": mod.DEFAULT_CLAIM_REF,
        "sha": "a" * 40,
    }


def test_second_dispatch_fails_closed():
    mod = load_claim()
    backend = AtomicFakeGitHub()
    mod.create_claim("owner/repo", "a" * 40, "token", opener=backend)
    with pytest.raises(mod.HoldoutClaimError, match="already exists"):
        mod.create_claim("owner/repo", "a" * 40, "token", opener=backend)


def test_simultaneous_dispatches_have_exactly_one_winner():
    mod = load_claim()
    backend = AtomicFakeGitHub()
    successes = []
    failures = []

    def attempt():
        try:
            successes.append(
                mod.create_claim(
                    "owner/repo",
                    "a" * 40,
                    "token",
                    opener=backend,
                )
            )
        except mod.HoldoutClaimError as exc:
            failures.append(str(exc))

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(successes) == 1
    assert len(failures) == 1
    assert "already exists" in failures[0]


def test_claim_ref_cannot_be_changed_by_cli_input():
    mod = load_claim()
    with pytest.raises(mod.HoldoutClaimError, match="unexpected holdout claim ref"):
        mod.create_claim(
            "owner/repo",
            "a" * 40,
            "token",
            ref="refs/tags/another-ref",
            opener=AtomicFakeGitHub(),
        )


def test_execution_workflow_serializes_and_claims_before_shard_fanout():
    text = WORKFLOW.read_text()
    assert "group: ams-dep-v2-holdout-one-shot" in text
    assert "cancel-in-progress: false" in text
    assert "contents: write" in text
    claim_pos = text.index("Atomically create durable one-shot holdout claim")
    shard_pos = text.index("\n  shard:")
    assert claim_pos < shard_pos
    assert "claim_ams_dep_v2_holdout.py" in text
    assert "needs: preflight" in text
