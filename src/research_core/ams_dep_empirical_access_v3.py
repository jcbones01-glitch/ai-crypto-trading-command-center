"""Fail-closed production access shell for AMS-DEP Development V3."""
from __future__ import annotations

from .ams_dep_development_source_v3 import (
    DevelopmentSourceV3Result,
    acquire_registered_development_source_v3,
)
from .ams_dep_pipeline import (
    REGISTERED_TREATMENT_IDENTITIES,
    CertifiedDataBundle,
    PipelineIntegrityError,
    verify_certified_bundle,
)
from .release_gate import assert_ams_dep_empirical_release_allowed


class EmpiricalAccessV3Error(RuntimeError):
    """Protected V3 empirical access is unavailable or invalid."""

    def __init__(
        self,
        message: str,
        *,
        partial_archive_evidence: tuple = (),
        network_source_access_attempted: bool = False,
        progressive_normalization_evidence: dict | None = None,
        progressive_coverage_evidence: dict | None = None,
    ):
        super().__init__(message)
        self.partial_archive_evidence = partial_archive_evidence
        self.network_source_access_attempted = network_source_access_attempted
        self.progressive_normalization_evidence = (
            None
            if progressive_normalization_evidence is None
            else dict(progressive_normalization_evidence)
        )
        self.progressive_coverage_evidence = (
            None
            if progressive_coverage_evidence is None
            else dict(progressive_coverage_evidence)
        )


def _assert_canonical_empirical_release() -> dict:
    return assert_ams_dep_empirical_release_allowed()


def _authorize_request(partition: str, symbol: str) -> dict:
    if partition != "development":
        raise EmpiricalAccessV3Error(
            "only Development V3 empirical access can be authorized"
        )
    if symbol not in REGISTERED_TREATMENT_IDENTITIES:
        raise EmpiricalAccessV3Error(
            "unsupported AMS-DEP Development V3 symbol"
        )
    return _assert_canonical_empirical_release()


def _load_registered_development_source(
    symbol: str,
) -> DevelopmentSourceV3Result:
    return acquire_registered_development_source_v3(symbol)


def load_development_source(symbol: str) -> DevelopmentSourceV3Result:
    _authorize_request("development", symbol)
    try:
        result = _load_registered_development_source(symbol)
    except Exception as exc:
        if isinstance(exc, EmpiricalAccessV3Error):
            raise
        raise EmpiricalAccessV3Error(
            f"Development V3 source adapter failed: {exc}",
            partial_archive_evidence=tuple(
                getattr(exc, "partial_archive_evidence", ())
            ),
            network_source_access_attempted=bool(
                getattr(exc, "network_source_access_attempted", False)
            ),
            progressive_normalization_evidence=getattr(
                exc, "progressive_normalization_evidence", None
            ),
            progressive_coverage_evidence=getattr(
                exc, "progressive_coverage_evidence", None
            ),
        ) from exc
    if result.symbol != symbol or result.bundle.symbol != symbol:
        raise EmpiricalAccessV3Error(
            "returned Development V3 source symbol mismatch"
        )
    try:
        verify_certified_bundle(
            result.bundle,
            registered_identity=result.bundle.manifest.dataset_identity,
        )
    except PipelineIntegrityError as exc:
        raise EmpiricalAccessV3Error(
            f"returned Development V3 bundle failed canonical integrity: {exc}",
            partial_archive_evidence=result.archive_evidence,
            network_source_access_attempted=True,
            progressive_normalization_evidence={
                "evidence_status": "COMPLETE_NORMALIZATION_ACCOUNTING",
                "completed_archive_accounting": list(result.row_accounting),
                "completed_archive_count": len(result.row_accounting),
                "aggregate_accounting":
                    dict(result.aggregate_row_accounting),
            },
            progressive_coverage_evidence={
                **result.coverage_evidence,
                "failure_code": "EMPIRICAL_ACCESS_CANONICAL_VERIFY_FAIL",
                "failure_stage": "EMPIRICAL_ACCESS_CANONICAL_VERIFY",
            },
        ) from exc
    return result


def _load_registered_development_bundle(symbol: str) -> CertifiedDataBundle:
    return load_development_source(symbol).bundle


def load_development_bundle(symbol: str) -> CertifiedDataBundle:
    _authorize_request("development", symbol)
    return _load_registered_development_bundle(symbol)
