"""Fail-closed production access shell for future AMS-DEP empirical work.

The public production API intentionally exposes no gate path, gate object,
partition override, environment override, or loader callback.
"""
from __future__ import annotations

from .ams_dep_pipeline import (
    REGISTERED_TREATMENT_IDENTITIES,
    CertifiedDataBundle,
    PipelineIntegrityError,
    verify_certified_bundle,
)
from .release_gate import assert_ams_dep_empirical_release_allowed


class EmpiricalAccessError(RuntimeError):
    """Protected empirical access is unavailable or invalid."""


def _assert_canonical_empirical_release() -> dict:
    # Deliberately no path argument: production always reads DEFAULT_GATE.
    return assert_ams_dep_empirical_release_allowed()


def _load_registered_development_bundle(symbol: str) -> CertifiedDataBundle:
    """Future source adapter seam.

    This remains deliberately unconfigured until separate empirical-release and
    Development-source authorization work defines the registered local archive
    inventory. Tests may monkeypatch this private function; production callers
    cannot inject a loader through the public API.
    """
    raise EmpiricalAccessError(
        "registered Development archive adapter is not configured; "
        "separate empirical-release work is required"
    )


def _authorize_request(partition: str, symbol: str) -> dict:
    """Private seam used by tests to prove partition blocking."""
    if partition != "development":
        raise EmpiricalAccessError("only Development empirical access can be authorized")
    if symbol not in REGISTERED_TREATMENT_IDENTITIES:
        raise EmpiricalAccessError("unsupported AMS-DEP symbol")
    return _assert_canonical_empirical_release()


def load_development_bundle(symbol: str) -> CertifiedDataBundle:
    """Load one verified Development bundle after all machine gates pass.

    The machine gate is checked before the private source adapter is invoked.
    The returned bundle is cryptographically/source-certified before return.
    """
    _authorize_request("development", symbol)
    bundle = _load_registered_development_bundle(symbol)
    if bundle.symbol != symbol:
        raise EmpiricalAccessError("returned bundle symbol mismatch")
    try:
        verify_certified_bundle(bundle)
    except PipelineIntegrityError as exc:
        raise EmpiricalAccessError(f"returned Development bundle failed integrity: {exc}") from exc
    return bundle
