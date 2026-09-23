"""Fail-closed production access shell for AMS-DEP Development V2."""
from __future__ import annotations

from .ams_dep_development_source_v2 import (
    DevelopmentSourceV2Result,
    acquire_registered_development_source_v2,
)
from .ams_dep_pipeline import (
    REGISTERED_TREATMENT_IDENTITIES,
    CertifiedDataBundle,
    PipelineIntegrityError,
    verify_certified_bundle,
)
from .release_gate import assert_ams_dep_empirical_release_allowed


class EmpiricalAccessV2Error(RuntimeError):
    """Protected V2 empirical access is unavailable or invalid."""

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
    return assert_ams_dep_empirical_release_allowed()


def _authorize_request(partition: str, symbol: str) -> dict:
    if partition != "development":
        raise EmpiricalAccessV2Error(
            "only Development V2 empirical access can be authorized"
        )
    if symbol not in REGISTERED_TREATMENT_IDENTITIES:
        raise EmpiricalAccessV2Error(
            "unsupported AMS-DEP Development V2 symbol"
        )
    return _assert_canonical_empirical_release()


def _load_registered_development_source(
    symbol: str,
) -> DevelopmentSourceV2Result:
    return acquire_registered_development_source_v2(symbol)


def load_development_source(symbol: str) -> DevelopmentSourceV2Result:
    _authorize_request("development", symbol)
    try:
        result = _load_registered_development_source(symbol)
    except Exception as exc:
        if isinstance(exc, EmpiricalAccessV2Error):
            raise
        raise EmpiricalAccessV2Error(
            f"Development V2 source adapter failed: {exc}",
            partial_archive_evidence=tuple(
                getattr(exc, "partial_archive_evidence", ())
            ),
            network_source_access_attempted=bool(
                getattr(exc, "network_source_access_attempted", False)
            ),
        ) from exc
    if result.symbol != symbol or result.bundle.symbol != symbol:
        raise EmpiricalAccessV2Error(
            "returned Development V2 source symbol mismatch"
        )
    try:
        verify_certified_bundle(
            result.bundle,
            registered_identity=result.bundle.manifest.dataset_identity,
        )
    except PipelineIntegrityError as exc:
        raise EmpiricalAccessV2Error(
            f"returned Development V2 bundle failed canonical integrity: {exc}"
        ) from exc
    return result


def _load_registered_development_bundle(symbol: str) -> CertifiedDataBundle:
    return load_development_source(symbol).bundle


def load_development_bundle(symbol: str) -> CertifiedDataBundle:
    _authorize_request("development", symbol)
    return _load_registered_development_bundle(symbol)
