"""PSR-01B fail-closed metadata/runtime preflight.

This module deliberately performs no empirical archive reads.  It validates the
frozen registration, runtime versions, archive inventory/digest metadata supplied
by a caller, and the inherited normalization import-closure Git blob identities.
"""
from __future__ import annotations

import importlib.metadata
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

from .psr01b_core import PSR01BError


ROOT = Path(__file__).resolve().parents[2]
REGISTRATION_PATH = ROOT / "research/governance/psr01b_bounded_spec_v1.json"
REGISTRATION_ID = "PSR01B-BOUNDED-DEVELOPMENT-SPOT-V1"
EXPECTED_REVISION = 4
EXPECTED_RUNTIME = {
    "python": "3.12.14",
    "numpy": "2.2.6",
    "scipy": "1.15.3",
    "pandas": "3.0.6",
    "xgboost": "3.4.1",
    "optuna": "5.0.0",
    "arch": "8.0.0",
    "statsmodels": "0.15.0",
}
EXPECTED_RUNNER = "ubuntu-24.04"
EXPECTED_DEVELOPMENT_START = datetime(2017, 8, 17, tzinfo=timezone.utc)
EXPECTED_DEVELOPMENT_END = datetime(2022, 1, 1, tzinfo=timezone.utc)


def load_registration(path: Path = REGISTRATION_PATH) -> dict:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise PSR01BError("cannot load PSR-01B registration") from exc
    if data.get("registration_id") != REGISTRATION_ID:
        raise PSR01BError("unexpected PSR-01B registration identity")
    if data.get("revision") != EXPECTED_REVISION:
        raise PSR01BError("PSR-01B registration revision drift")
    if data.get("runtime_contract") != {
        "os_runner": EXPECTED_RUNNER,
        **EXPECTED_RUNTIME,
        "env": {
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
        },
    }:
        raise PSR01BError("PSR-01B runtime contract drift")
    return data


def verify_runtime_versions(*, runner_label: str) -> dict[str, str]:
    if runner_label != EXPECTED_RUNNER:
        raise PSR01BError("unexpected PSR-01B runner")
    observed = {"python": platform.python_version()}
    for package in (
        "numpy",
        "scipy",
        "pandas",
        "xgboost",
        "optuna",
        "arch",
        "statsmodels",
    ):
        try:
            observed[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError as exc:
            raise PSR01BError(f"missing PSR-01B runtime package: {package}") from exc
    if observed != EXPECTED_RUNTIME:
        raise PSR01BError(
            f"PSR-01B runtime version mismatch: observed={observed}"
        )
    return observed


def verify_archive_inventory(
    archive_names: Sequence[str],
    registration: Mapping,
) -> tuple[str, ...]:
    source = registration.get("source") or {}
    expected_map = source.get("archive_sha256") or {}
    if int(source.get("archive_count", -1)) != 49 or len(expected_map) != 49:
        raise PSR01BError("registered PSR-01B archive inventory is not exactly 49")
    expected = tuple(sorted(expected_map))
    observed = tuple(sorted(str(x) for x in archive_names))
    if len(observed) != len(set(observed)):
        raise PSR01BError("duplicate archive filename in PSR-01B inventory")
    if observed != expected:
        raise PSR01BError("PSR-01B archive filename inventory mismatch")
    return observed


def verify_archive_digest_metadata(
    observed_sha256: Mapping[str, str],
    registration: Mapping,
) -> dict[str, str]:
    """Compare caller-supplied archive digests without opening archive bytes."""
    expected = (registration.get("source") or {}).get("archive_sha256") or {}
    observed = {str(k): str(v).lower() for k, v in observed_sha256.items()}
    if set(observed) != set(expected):
        raise PSR01BError("PSR-01B archive digest path set mismatch")
    for name, digest in observed.items():
        if digest != str(expected[name]).lower():
            raise PSR01BError(f"PSR-01B archive SHA-256 mismatch: {name}")
    return observed


def verify_import_closure_blob_metadata(
    observed_git_blob_sha1: Mapping[str, str],
    registration: Mapping,
) -> dict[str, str]:
    row_contract = ((registration.get("source") or {}).get("row_treatment_contract") or {})
    expected = row_contract.get("required_blob_sha1") or {}
    observed = {str(k): str(v) for k, v in observed_git_blob_sha1.items()}
    if set(observed) != set(expected):
        raise PSR01BError("PSR-01B normalization import-closure path set mismatch")
    for path, sha in observed.items():
        if sha != expected[path]:
            raise PSR01BError(f"PSR-01B pinned import blob mismatch: {path}")
    return observed


def verify_upstream_registration_blob_metadata(
    observed_git_blob_sha1: str,
    registration: Mapping,
) -> str:
    """Verify the pinned upstream AMS-DEP registration blob before source read."""
    row_contract = ((registration.get("source") or {}).get("row_treatment_contract") or {})
    expected = row_contract.get("upstream_registration_blob_sha1")
    path = row_contract.get("upstream_registration_path")
    if not isinstance(expected, str) or len(expected) != 40 or not isinstance(path, str) or not path:
        raise PSR01BError("registered upstream normalization registration pin is missing")
    observed = str(observed_git_blob_sha1)
    if observed != expected:
        raise PSR01BError(f"PSR-01B pinned upstream registration blob mismatch: {path}")
    return observed


def verify_timestamp_boundary_metadata(
    unix_seconds: Sequence[int],
    registration: Mapping,
) -> None:
    """Pure boundary check for synthetic/pre-normalized timestamp fixtures."""
    from datetime import datetime, timezone

    source = registration.get("source") or {}
    raw_start = datetime.fromisoformat(source["raw_start"].replace("Z", "+00:00"))
    hard_end = datetime.fromisoformat(source["hard_end_exclusive"].replace("Z", "+00:00"))
    if raw_start.tzinfo is None or hard_end.tzinfo is None:
        raise PSR01BError("registered source boundary must be timezone-aware")
    previous = None
    for value in unix_seconds:
        if isinstance(value, bool) or not isinstance(value, int):
            raise PSR01BError("timestamp fixture must contain integer Unix seconds")
        stamp = datetime.fromtimestamp(value, tz=timezone.utc)
        if stamp.minute or stamp.second or stamp.microsecond:
            raise PSR01BError("PSR-01B timestamp must be an exact UTC hour")
        if not raw_start <= stamp < hard_end:
            raise PSR01BError("PSR-01B timestamp outside registered source boundary")
        if previous is not None and value <= previous:
            raise PSR01BError("PSR-01B timestamps must be strictly increasing")
        previous = value


def verify_development_boundary_constants(pipeline_module=None) -> tuple[datetime, datetime]:
    """Assert the registered inherited Development boundaries before source read."""
    if pipeline_module is None:
        from . import ams_dep_pipeline as pipeline_module

    start = getattr(pipeline_module, "DEVELOPMENT_START", None)
    end = getattr(pipeline_module, "DEVELOPMENT_END", None)
    if start != EXPECTED_DEVELOPMENT_START or end != EXPECTED_DEVELOPMENT_END:
        raise PSR01BError(
            "AMS-DEP Development boundary constants do not match PSR-01B registration"
        )
    return start, end


def verify_import_closure_and_development_boundaries(
    observed_git_blob_sha1: Mapping[str, str],
    registration: Mapping,
    *,
    pipeline_module=None,
) -> tuple[dict[str, str], tuple[datetime, datetime]]:
    """Backward-compatible closure+boundary check used by existing tests."""
    blobs = verify_import_closure_blob_metadata(observed_git_blob_sha1, registration)
    boundaries = verify_development_boundary_constants(pipeline_module)
    return blobs, boundaries


def verify_pre_source_read_contract(
    observed_git_blob_sha1: Mapping[str, str],
    observed_upstream_registration_blob_sha1: str,
    registration: Mapping,
    *,
    pipeline_module=None,
) -> tuple[dict[str, str], str, tuple[datetime, datetime]]:
    """Fail closed on every revision-4 pinned identity before any archive read.

    Order is deliberate: verify the complete project-local import closure, then
    the pinned upstream registration blob, then the inherited Development
    boundary constants.  Callers must complete this function before opening any
    registered archive bytes.
    """
    blobs = verify_import_closure_blob_metadata(observed_git_blob_sha1, registration)
    upstream = verify_upstream_registration_blob_metadata(
        observed_upstream_registration_blob_sha1,
        registration,
    )
    boundaries = verify_development_boundary_constants(pipeline_module)
    return blobs, upstream, boundaries
