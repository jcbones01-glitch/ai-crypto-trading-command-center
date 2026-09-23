"""Fail-closed production access shell for AMS-DEP Development work.

The public production API intentionally exposes no gate path, gate object,
partition override, environment override, source URL, archive root, or loader
callback.
"""
from __future__ import annotations

from .ams_dep_development_source import (
    DevelopmentSourceResult,
    acquire_registered_development_source,
)
from .ams_dep_pipeline import (
    REGISTERED_TREATMENT_IDENTITIES,
    CertifiedDataBundle,
    PipelineIntegrityError,
    verify_certified_bundle,
)
from .release_gate import assert_ams_dep_empirical_release_allowed


class EmpiricalAccessError(RuntimeError):
    """Protected empirical access is unavailable or invalid."""

    def __init__(
        self,
        message: str,
        *,
        partial_archive_evidence: tuple = (),
        network_source_access_attempted: bool = False,
    ):
        super().__init__(message)
        self.partial_archive_evidence = partial_archive_evidence
        self.network_source_access_attempted = network_source_access_attempted


def _assert_canonical_empirical_release() -> dict:
    # Deliberately no path argument: production always reads DEFAULT_GATE.
    return assert_ams_dep_empirical_release_allowed()


def _authorize_request(partition: str, symbol: str) -> dict:
    """Reject protected partitions and unsupported assets before source access."""
    if partition != "development":
        raise EmpiricalAccessError("only Development empirical access can be authorized")
    if symbol not in REGISTERED_TREATMENT_IDENTITIES:
        raise EmpiricalAccessError("unsupported AMS-DEP symbol")
    return _assert_canonical_empirical_release()


def _load_registered_development_source(symbol: str) -> DevelopmentSourceResult:
    """Invoke the fixed, non-overridable Development source adapter."""
    return acquire_registered_development_source(symbol)


def load_development_source(symbol: str) -> DevelopmentSourceResult:
    """Load one provenance-complete Development source after every lock passes."""
    _authorize_request("development", symbol)
    try:
        result = _load_registered_development_source(symbol)
    except Exception as exc:
        if isinstance(exc, EmpiricalAccessError):
            raise
        raise EmpiricalAccessError(
            f"Development source adapter failed: {exc}",
            partial_archive_evidence=tuple(
                getattr(exc, "partial_archive_evidence", ())
            ),
            network_source_access_attempted=bool(
                getattr(exc, "network_source_access_attempted", False)
            ),
        ) from exc
    if result.symbol != symbol or result.bundle.symbol != symbol:
        raise EmpiricalAccessError("returned Development source symbol mismatch")
    try:
        # The fixed Development adapter already enforced the projection contract.
        # Re-run canonical bundle/sample invariants with the helper manifest's own
        # recomputed identity, never with the historical whole-research parent ID.
        verify_certified_bundle(
            result.bundle,
            registered_identity=result.bundle.manifest.dataset_identity,
        )
    except PipelineIntegrityError as exc:
        raise EmpiricalAccessError(
            f"returned Development bundle failed canonical integrity: {exc}"
        ) from exc
    return result


def _load_registered_development_bundle(symbol: str) -> CertifiedDataBundle:
    """Private compatibility seam returning only the verified bundle."""
    return load_development_source(symbol).bundle


def load_development_bundle(symbol: str) -> CertifiedDataBundle:
    """Compatibility API exposing only symbol and returning a verified bundle."""
    _authorize_request("development", symbol)
    return _load_registered_development_bundle(symbol)
