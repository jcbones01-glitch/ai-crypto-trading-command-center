"""Fixed Development-only source adapter and provenance projection for AMS-DEP.

This module contains the only production source inventory for the first
Development empirical execution. It exposes no caller-controlled URL, archive
root, month range, checksum bypass, partition, or mirror.
"""
from __future__ import annotations

import atexit
import hashlib
import json
import shutil
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from .ams_dep_development_execution_lock import (
    assert_claim_environment,
    assert_development_execution_allowed,
)
from .ams_dep_pipeline import (
    DEVELOPMENT_END,
    DEVELOPMENT_START,
    CertifiedDataBundle,
    PipelineIntegrityError,
    build_certified_bundle_from_archives,
    verify_certified_bundle,
)
from .data_ingestion import (
    BINANCE_BASE_URL,
    NORMALIZATION_VERSION,
    TIMEFRAME,
    archive_url,
    download_archive,
)
from .data_quality_treatment_v2 import TREATMENT_PROTOCOL_VERSION
from .source_identity import source_identity

PROJECTION_VERSION = "ams-dep-development-projection-v1"
EXPECTED_ARCHIVES_PER_SYMBOL = 53
PARENT_MANIFEST_IDENTITIES = {
    "BTCUSDT": "1590cf8e69ed757eeb6701a218d561448beb2eb6ea09dcd0ae31d15a8f5197cf",
    "ETHUSDT": "d35bf21e309820abc88090bad29601adc1d1ea6b31dcddf0b80d510af4cf542f",
}
_ALLOWED_SYMBOLS = tuple(PARENT_MANIFEST_IDENTITIES)


class DevelopmentSourceError(RuntimeError):
    """Raised when the frozen Development source/projection contract fails."""


@dataclass(frozen=True)
class ArchiveEvidence:
    symbol: str
    year: int
    month: int
    filename: str
    official_url: str
    official_checksum_sha256: str
    local_zip_sha256: str


@dataclass(frozen=True)
class DevelopmentSourceResult:
    symbol: str
    bundle: CertifiedDataBundle
    archive_evidence: tuple[ArchiveEvidence, ...]
    projection_record: dict
    projection_sha256: str
    staging_root: str


def development_months() -> tuple[tuple[int, int], ...]:
    values: list[tuple[int, int]] = []
    year, month = 2017, 8
    while (year, month) <= (2021, 12):
        values.append((year, month))
        month += 1
        if month == 13:
            year, month = year + 1, 1
    result = tuple(values)
    if len(result) != EXPECTED_ARCHIVES_PER_SYMBOL:
        raise DevelopmentSourceError("unexpected frozen Development month count")
    return result


def expected_filenames(symbol: str) -> tuple[str, ...]:
    if symbol not in _ALLOWED_SYMBOLS:
        raise DevelopmentSourceError("unsupported AMS-DEP Development symbol")
    return tuple(
        f"{symbol}-{TIMEFRAME}-{year:04d}-{month:02d}.zip"
        for year, month in development_months()
    )


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical_sha256(record: dict) -> str:
    payload = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DevelopmentSourceError("manifest timestamp must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _development_partition(bundle: CertifiedDataBundle):
    matches = [
        value for value in bundle.manifest.partitions
        if value.partition == "development"
    ]
    if len(matches) != 1:
        raise DevelopmentSourceError(
            "exactly one Development partition certification required"
        )
    partition = matches[0]
    if _dt(partition.start) != DEVELOPMENT_START or _dt(partition.end) != DEVELOPMENT_END:
        raise DevelopmentSourceError("Development partition boundary mismatch")
    return partition


def _development_breaks(bundle: CertifiedDataBundle) -> tuple[dict, ...]:
    values = []
    for value in bundle.manifest.continuity_breaks:
        start, end = _dt(value.start), _dt(value.end)
        if max(start, DEVELOPMENT_START) < min(end, DEVELOPMENT_END):
            values.append(asdict(value))
    values.sort(key=lambda item: (item["start"], item["end"]))
    return tuple(values)


def build_development_projection(
    bundle: CertifiedDataBundle,
    archive_evidence: tuple[ArchiveEvidence, ...],
) -> tuple[dict, str]:
    """Verify one fixed Development source and build its preregistered projection."""
    if bundle.symbol not in _ALLOWED_SYMBOLS:
        raise DevelopmentSourceError("unsupported AMS-DEP Development symbol")
    if len(archive_evidence) != EXPECTED_ARCHIVES_PER_SYMBOL:
        raise DevelopmentSourceError("Development archive inventory must contain 53 files")

    expected = expected_filenames(bundle.symbol)
    observed = tuple(value.filename for value in archive_evidence)
    if observed != expected:
        raise DevelopmentSourceError("Development archive filename inventory mismatch")

    ordered_paths = tuple(sorted(bundle.raw_archive_paths, key=lambda path: path.name))
    if len(ordered_paths) != EXPECTED_ARCHIVES_PER_SYMBOL:
        raise DevelopmentSourceError("Development bundle must bind exactly 53 raw archives")
    if tuple(path.name for path in ordered_paths) != expected:
        raise DevelopmentSourceError("raw archive paths differ from frozen Development inventory")
    for path, evidence in zip(ordered_paths, archive_evidence):
        local_sha = _sha256_file(path)
        if local_sha != evidence.local_zip_sha256:
            raise DevelopmentSourceError("archive evidence local SHA-256 mismatch")
        if evidence.official_checksum_sha256 != evidence.local_zip_sha256:
            raise DevelopmentSourceError("archive evidence official checksum mismatch")

    try:
        verification = verify_certified_bundle(
            bundle,
            registered_identity=bundle.manifest.dataset_identity,
        )
    except PipelineIntegrityError as exc:
        raise DevelopmentSourceError(
            f"Development helper bundle failed canonical verification: {exc}"
        ) from exc

    partition = _development_partition(bundle)
    if partition.certification not in {"VALID", "VALID WITH DOCUMENTED EXCLUSIONS"}:
        raise DevelopmentSourceError("Development partition is not certified")

    raw_identity = source_identity(list(bundle.raw_archive_paths))
    if verification["raw_source_identity"] != raw_identity:
        raise DevelopmentSourceError("authoritative Development raw-source mismatch")

    breaks = _development_breaks(bundle)
    referenced_ids = set()
    for value in partition.exclusions:
        referenced_ids.update(value.anomaly_ids)
    for value in breaks:
        referenced_ids.update(value["anomaly_ids"])

    record = {
        "projection_version": PROJECTION_VERSION,
        "historical_whole_research_parent_manifest_identity":
            PARENT_MANIFEST_IDENTITIES[bundle.symbol],
        "symbol": bundle.symbol,
        "source_provider": "Binance Public Data",
        "market": "spot",
        "timeframe": TIMEFRAME,
        "normalization_version": NORMALIZATION_VERSION,
        "treatment_protocol_version": TREATMENT_PROTOCOL_VERSION,
        "development_start": DEVELOPMENT_START.isoformat(),
        "development_end": DEVELOPMENT_END.isoformat(),
        "authoritative_development_raw_source_identity": raw_identity,
        "ordered_archive_evidence_53": [
            asdict(value) for value in archive_evidence
        ],
        "development_certification": partition.certification,
        "development_certified_segments": [
            asdict(value) for value in partition.certified_segments
        ],
        "development_exclusions": [
            asdict(value) for value in partition.exclusions
        ],
        "development_intersecting_continuity_breaks": list(breaks),
        "development_referenced_anomaly_ids": sorted(referenced_ids),
        "normalized_dataset_id": bundle.metadata.dataset_id,
        "normalized_content_hash": bundle.metadata.content_hash,
        "normalized_row_count": bundle.metadata.row_count,
        "normalized_start_timestamp": bundle.metadata.start_timestamp,
        "normalized_end_timestamp": bundle.metadata.end_timestamp,
    }
    forbidden = {
        "validation_partition_certification",
        "oos_partition_certification",
        "empirical_statistics",
        "p_values",
        "coefficients",
        "market_outcomes",
    }
    if forbidden & set(record):
        raise DevelopmentSourceError("protected/outcome field leaked into projection")
    return record, _canonical_sha256(record)


def _fixed_official_url(symbol: str, year: int, month: int) -> str:
    url = archive_url(symbol, year, month)
    expected_host = urlparse(BINANCE_BASE_URL).netloc
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != expected_host:
        raise DevelopmentSourceError("unexpected Binance archive host")
    expected_name = f"{symbol}-{TIMEFRAME}-{year:04d}-{month:02d}.zip"
    if Path(parsed.path).name != expected_name:
        raise DevelopmentSourceError("unexpected Binance archive filename")
    return url


def acquire_registered_development_source(symbol: str) -> DevelopmentSourceResult:
    """Acquire and verify the exact registered Development source for one asset.

    The execution gate and durable-claim environment are checked before any
    temporary directory is populated or any network source is requested.
    """
    if symbol not in _ALLOWED_SYMBOLS:
        raise DevelopmentSourceError("unsupported AMS-DEP Development symbol")

    assert_development_execution_allowed()
    assert_claim_environment()

    root = Path(tempfile.mkdtemp(prefix="ams-dep-development-v1-"))
    atexit.register(shutil.rmtree, root, ignore_errors=True)
    symbol_root = root / symbol

    evidence: list[ArchiveEvidence] = []
    paths: list[Path] = []
    try:
        for year, month in development_months():
            url = _fixed_official_url(symbol, year, month)
            filename = Path(urlparse(url).path).name
            destination = symbol_root / filename
            checksum = download_archive(url, destination, verify_checksum=True)
            if checksum is None:
                raise DevelopmentSourceError("official checksum evidence is required")
            local_sha = _sha256_file(destination)
            if local_sha != checksum:
                raise DevelopmentSourceError("local ZIP SHA-256 differs from official checksum")
            evidence.append(
                ArchiveEvidence(
                    symbol=symbol,
                    year=year,
                    month=month,
                    filename=filename,
                    official_url=url,
                    official_checksum_sha256=checksum,
                    local_zip_sha256=local_sha,
                )
            )
            paths.append(destination)

        if tuple(path.name for path in paths) != expected_filenames(symbol):
            raise DevelopmentSourceError("observed archive set differs from frozen inventory")

        bundle = build_certified_bundle_from_archives(
            symbol,
            paths,
            checksum_verified=True,
        )
        projection, projection_sha = build_development_projection(
            bundle,
            tuple(evidence),
        )
        return DevelopmentSourceResult(
            symbol=symbol,
            bundle=bundle,
            archive_evidence=tuple(evidence),
            projection_record=projection,
            projection_sha256=projection_sha,
            staging_root=str(root),
        )
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise
