from __future__ import annotations

import json

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


class FixedRefBackend:
    def __init__(self, refs):
        self.refs = dict(refs)

    def __call__(self, request):
        url = request.full_url
        for ref, sha in self.refs.items():
            short = ref.removeprefix("refs/")
            if url.endswith("/git/ref/" + short):
                return FakeResponse({"ref": ref, "object": {"sha": sha}})
        raise AssertionError(f"unexpected URL: {url}")


def _authorized_gate():
    return {
        "development_market_data_execution_authorized": True,
        "validation_or_oos_access_authorized": False,
        "strategy_pnl_authorized": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
    }


def _authorized_manifest(candidate):
    return {
        "status": "AUTHORIZED_FOR_FIRST_DEVELOPMENT_EXECUTION",
        "implementation_candidate_commit": candidate,
        "reviewed_implementation_commit": candidate,
        "independent_implementation_reviewed": True,
        "development_execution_authorized": True,
        "first_empirical_execution_claimed": False,
        "first_empirical_execution_executed": False,
        "one_shot_claim_ref": lock.DEFAULT_CLAIM_REF,
        "review_anchor_ref": lock.DEFAULT_REVIEW_ANCHOR_REF,
        "confirmation_token": lock.EXACT_CONFIRMATION,
        "protected_permissions": {
            "validation_or_oos_access_authorized": False,
            "strategy_pnl_authorized": False,
            "paper_trading_authorized": False,
            "live_trading_authorized": False,
            "directed_cross_asset_lagged_diagnostics_authorized": False,
        },
    }


def _freeze(candidate):
    return {
        "status": "FROZEN_FOR_INDEPENDENT_REVIEW",
        "implementation_candidate_commit": candidate,
        "independent_review_required": True,
    }


def _install_authorized_fixture(monkeypatch, candidate, changed=()):
    manifest = _authorized_manifest(candidate)
    freeze = _freeze(candidate)
    gate = _authorized_gate()

    monkeypatch.setattr(
        lock,
        "assert_ams_dep_empirical_release_allowed",
        lambda: gate,
    )
    monkeypatch.setattr(
        lock,
        "load_development_execution_manifest",
        lambda: manifest,
    )
    monkeypatch.setattr(
        lock,
        "load_development_implementation_freeze",
        lambda: freeze,
    )
    monkeypatch.setattr(
        lock,
        "verify_frozen_implementation",
        lambda value: {},
    )
    monkeypatch.setattr(
        lock,
        "_verify_execution_commit",
        lambda reviewed, executing: tuple(changed),
    )
    return manifest, freeze, gate


def test_exact_authorized_pre_execution_contract_passes(monkeypatch):
    candidate = "a" * 40
    executing = "b" * 40
    _install_authorized_fixture(
        monkeypatch,
        candidate,
        changed=(
            "research/governance/ams_dep_development_execution_manifest_v1.json",
            "research/governance/ams_dep_release_gate_v1.json",
        ),
    )
    backend = FixedRefBackend(
        {lock.DEFAULT_REVIEW_ANCHOR_REF: candidate}
    )

    result = lock.assert_development_execution_allowed(
        executing,
        repository="owner/repo",
        token="token",
        ref_opener=backend,
    )
    assert result["review_anchor"] == {
        "ref": lock.DEFAULT_REVIEW_ANCHOR_REF,
        "sha": candidate,
    }
    assert result["executing_sha"] == executing


def test_mutable_governance_cannot_rebind_reviewed_candidate(monkeypatch):
    independently_reviewed = "a" * 40
    malicious_rebind = "c" * 40
    executing = "d" * 40
    _install_authorized_fixture(
        monkeypatch,
        malicious_rebind,
        changed=(
            "research/governance/ams_dep_development_execution_manifest_v1.json",
            "research/governance/ams_dep_development_implementation_freeze_v1.json",
            "research/governance/ams_dep_release_gate_v1.json",
        ),
    )
    backend = FixedRefBackend(
        {lock.DEFAULT_REVIEW_ANCHOR_REF: independently_reviewed}
    )

    with pytest.raises(
        lock.DevelopmentExecutionError,
        match="candidate anchor target mismatch",
    ):
        lock.assert_development_execution_allowed(
            executing,
            repository="owner/repo",
            token="token",
            ref_opener=backend,
        )


@pytest.mark.parametrize(
    "field",
    [
        "validation_or_oos_access_authorized",
        "strategy_pnl_authorized",
        "paper_trading_authorized",
        "live_trading_authorized",
    ],
)
def test_canonical_downstream_permissions_must_remain_closed(
    monkeypatch,
    field,
):
    candidate = "a" * 40
    _, _, gate = _install_authorized_fixture(monkeypatch, candidate)
    gate[field] = True
    backend = FixedRefBackend(
        {lock.DEFAULT_REVIEW_ANCHOR_REF: candidate}
    )

    with pytest.raises(
        lock.DevelopmentExecutionError,
        match=f"canonical {field}=false",
    ):
        lock.assert_development_execution_allowed(
            "b" * 40,
            repository="owner/repo",
            token="token",
            ref_opener=backend,
        )
