"""Fixed Development-only source adapter for AMS-DEP empirical recovery V2."""
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

from .ams_dep_development_execution_lock_v2 import (
    assert_claim_environment,
    assert_development_execution_allowed,
)
from .ams_dep_pipeline import (
    DEVELOPMENT_END,
    DEVELOPMENT_START,
    CertifiedDataBundle,
    PipelineIntegrityError,
    verify_certified_bundle,
)
from .ams_dep_treatment_aware_normalization_v2 import (
    TreatmentAwareNormalizationResult,
    normalize_development_archives,
)
from .data_ingestion import (
    BINANCE_BASE_URL,
    NORMALIZATION_VERSION,
    TIMEFRAME,
    archive_url,
    download_archive,
    make_metadata,
)
from .data_quality import scan_archive
from .data_quality_treatment_v2 import (
    TREATMENT_PROTOCOL_VERSION,
    build_manifest,
)
from .source_identity import bind_source_identity, source_identity

PROJECTION_VERSION = "ams-dep-development-projection-v2"
NORMALIZATION_MODE = "TREATMENT_AWARE_RAW_ROW_V2"
EXPECTED_ARCHIVES_PER_SYMBOL = 53
REGISTRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "research/governance/ams_dep_development_execution_v2.json"
)
PARENT_MANIFEST_IDENTITIES = {
    "BTCUSDT": "1590cf8e69ed757eeb6701a218d561448beb2eb6ea09dcd0ae31d15a8f5197cf",
    "ETHUSDT": "d35bf21e309820abc88090bad29601adc1d1ea6b31dcddf0b80d510af4cf542f",
}
_ALLOWED_SYMBOLS = tuple(PARENT_MANIFEST_IDENTITIES)


class DevelopmentSourceV2Error(RuntimeError):
    """Raised when the frozen V2 Development source contract fails."""

    def __init__(
        self,
        message: str,
        *,
        partial_archive_evidence: tuple["ArchiveEvidenceV2", ...] = (),
        network_source_access_attempted: bool = False,
    ):
        super().__init__(message)
        self.partial_archive_evidence = partial_archive_evidence
        self.network_source_access_attempted = network_source_access_attempted


@dataclass(frozen=True)
class ArchiveEvidenceV2:
    symbol: str
    year: int
    month: int
    filename: str
    official_url: str
    official_checksum_sha256: str
    local_zip_sha256: str
    parent_v1_btc_checksum_sha256: str | None
    parent_v1_checksum_continuity_pass: bool | None


@dataclass(frozen=True)
class DevelopmentSourceV2Result:
    symbol: str
    bundle: CertifiedDataBundle
    archive_evidence: tuple[ArchiveEvidenceV2, ...]
    row_accounting: tuple[dict, ...]
    aggregate_row_accounting: dict
    projection_record: dict
    projection_sha256: str
    staging_root: str


def _load_registration() -> dict:
    try:
        value = json.loads(REGISTRATION_PATH.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise DevelopmentSourceV2Error(
            "cannot load V2 Development registration"
        ) from exc
    if value.get("registration_id") != (
        "AMS-DEP-DEVELOPMENT-EMPIRICAL-EXECUTION-V2"
    ):
        raise DevelopmentSourceV2Error(
            "unexpected V2 Development registration identity"
        )
    return value


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
        raise DevelopmentSourceV2Error(
            "unexpected frozen Development V2 month count"
        )
    return result


def expected_filenames(symbol: str) -> tuple[str, ...]:
    if symbol not in _ALLOWED_SYMBOLS:
        raise DevelopmentSourceV2Error(
            "unsupported AMS-DEP Development V2 symbol"
        )
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


def _fixed_official_url(symbol: str, year: int, month: int) -> str:
    url = archive_url(symbol, year, month)
    expected_host = urlparse(BINANCE_BASE_URL).netloc
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != expected_host:
        raise DevelopmentSourceV2Error(
            "unexpected Binance archive host"
        )
    expected_name = (
        f"{symbol}-{TIMEFRAME}-{year:04d}-{month:02d}.zip"
    )
    if Path(parsed.path).name != expected_name:
        raise DevelopmentSourceV2Error(
            "unexpected Binance archive filename"
        )
    return url


def _dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DevelopmentSourceV2Error(
            "manifest timestamp must be timezone-aware"
        )
    return parsed.astimezone(timezone.utc)


def _development_partition(bundle: CertifiedDataBundle):
    matches = [
        value
        for value in bundle.manifest.partitions
        if value.partition == "development"
    ]
    if len(matches) != 1:
        raise DevelopmentSourceV2Error(
            "exactly one Development partition certification required"
        )
    partition = matches[0]
    if (
        _dt(partition.start) != DEVELOPMENT_START
        or _dt(partition.end) != DEVELOPMENT_END
    ):
        raise DevelopmentSourceV2Error(
            "Development partition boundary mismatch"
        )
    return partition


def _development_breaks(bundle: CertifiedDataBundle) -> tuple[dict, ...]:
    values = []
    for value in bundle.manifest.continuity_breaks:
        start, end = _dt(value.start), _dt(value.end)
        if max(start, DEVELOPMENT_START) < min(end, DEVELOPMENT_END):
            values.append(asdict(value))
    values.sort(key=lambda item: (item["start"], item["end"]))
    return tuple(values)


def _build_treatment_aware_bundle(
    symbol: str,
    paths: tuple[Path, ...],
) -> tuple[CertifiedDataBundle, TreatmentAwareNormalizationResult]:
    ordered = tuple(sorted(paths, key=lambda path: path.name))
    reports = tuple(
        scan_archive(path, symbol, checksum_verified=True)
        for path in ordered
    )
    manifest = build_manifest(
        symbol,
        list(reports),
        research_start=DEVELOPMENT_START,
        research_end=DEVELOPMENT_END,
    )
    if manifest.source_integrity != "SOURCE VERIFIED":
        raise DevelopmentSourceV2Error(
            "V2 source integrity is not verified"
        )
    if manifest.research_certification not in {
        "VALID",
        "VALID WITH DOCUMENTED EXCLUSIONS",
    }:
        raise DevelopmentSourceV2Error(
            "V2 Development treatment manifest is unusable"
        )
    manifest = bind_source_identity(manifest, list(ordered))

    normalized = normalize_development_archives(
        symbol,
        ordered,
        reports,
        manifest,
    )
    raw_identity = source_identity(list(ordered))
    metadata = make_metadata(
        list(normalized.bars),
        symbol,
        normalized.timestamp_unit,
        source_identity=raw_identity,
    )
    bundle = CertifiedDataBundle(
        symbol=symbol,
        bars=normalized.bars,
        metadata=metadata,
        manifest=manifest,
        raw_archive_paths=ordered,
    )
    try:
        verify_certified_bundle(
            bundle,
            registered_identity=manifest.dataset_identity,
        )
    except PipelineIntegrityError as exc:
        raise DevelopmentSourceV2Error(
            f"V2 treatment-aware bundle failed canonical verification: {exc}"
        ) from exc
    return bundle, normalized


def build_development_projection_v2(
    bundle: CertifiedDataBundle,
    archive_evidence: tuple[ArchiveEvidenceV2, ...],
    normalized: TreatmentAwareNormalizationResult,
) -> tuple[dict, str]:
    if bundle.symbol not in _ALLOWED_SYMBOLS:
        raise DevelopmentSourceV2Error(
            "unsupported V2 Development symbol"
        )
    if len(archive_evidence) != EXPECTED_ARCHIVES_PER_SYMBOL:
        raise DevelopmentSourceV2Error(
            "V2 archive evidence must contain exactly 53 files"
        )
    expected = expected_filenames(bundle.symbol)
    if tuple(value.filename for value in archive_evidence) != expected:
        raise DevelopmentSourceV2Error(
            "V2 archive evidence inventory mismatch"
        )
    ordered_paths = tuple(
        sorted(bundle.raw_archive_paths, key=lambda path: path.name)
    )
    if tuple(path.name for path in ordered_paths) != expected:
        raise DevelopmentSourceV2Error(
            "V2 raw archive inventory mismatch"
        )

    for path, evidence in zip(ordered_paths, archive_evidence):
        local = _sha256_file(path)
        if (
            local != evidence.local_zip_sha256
            or local != evidence.official_checksum_sha256
        ):
            raise DevelopmentSourceV2Error(
                "V2 source archive checksum evidence mismatch"
            )
        if bundle.symbol == "BTCUSDT":
            if (
                evidence.parent_v1_btc_checksum_sha256 is None
                or evidence.parent_v1_checksum_continuity_pass is not True
                or evidence.parent_v1_btc_checksum_sha256 != local
            ):
                raise DevelopmentSourceV2Error(
                    "BTC V1/V2 checksum continuity failure"
                )

    partition = _development_partition(bundle)
    if partition.certification not in {
        "VALID",
        "VALID WITH DOCUMENTED EXCLUSIONS",
    }:
        raise DevelopmentSourceV2Error(
            "Development partition is not certified"
        )

    raw_identity = source_identity(list(ordered_paths))
    breaks = _development_breaks(bundle)
    referenced_ids = set()
    for value in partition.exclusions:
        referenced_ids.update(value.anomaly_ids)
    for value in breaks:
        referenced_ids.update(value["anomaly_ids"])

    accounting_records = [
        item.to_record(include_rejected_rows=False)
        for item in normalized.archive_accounting
    ]
    rejected_records = [
        rejected.to_record()
        for item in normalized.archive_accounting
        for rejected in item.rejected_raw_rows
    ]

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
        "normalization_mode": NORMALIZATION_MODE,
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
        "raw_row_accounting_per_archive": accounting_records,
        "raw_row_accounting_aggregate":
            dict(normalized.aggregate_accounting),
        "rejected_raw_row_record_count": len(rejected_records),
        "rejected_raw_row_records_sha256": _canonical_sha256(
            {"records": rejected_records}
        ),
        "btc_parent_incident_checksum_continuity_pass":
            (
                all(
                    value.parent_v1_checksum_continuity_pass is True
                    for value in archive_evidence
                )
                if bundle.symbol == "BTCUSDT"
                else None
            ),
        "timestamp_rounding_used": False,
        "interpolation_used": False,
        "synthetic_bar_used": False,
        "arbitrary_exception_skip_used": False,
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
        raise DevelopmentSourceV2Error(
            "protected/outcome field leaked into V2 projection"
        )
    return record, _canonical_sha256(record)


def acquire_registered_development_source_v2(
    symbol: str,
) -> DevelopmentSourceV2Result:
    if symbol not in _ALLOWED_SYMBOLS:
        raise DevelopmentSourceV2Error(
            "unsupported AMS-DEP Development V2 symbol"
        )

    assert_development_execution_allowed()
    assert_claim_environment()

    registration = _load_registration()
    btc_pins = registration.get(
        "btc_parent_incident_checksum_pins", {}
    )
    root = Path(tempfile.mkdtemp(prefix="ams-dep-development-v2-"))
    atexit.register(shutil.rmtree, root, ignore_errors=True)
    symbol_root = root / symbol

    evidence: list[ArchiveEvidenceV2] = []
    paths: list[Path] = []
    network_source_access_attempted = False
    try:
        for year, month in development_months():
            url = _fixed_official_url(symbol, year, month)
            filename = Path(urlparse(url).path).name
            destination = symbol_root / filename
            network_source_access_attempted = True
            checksum = download_archive(
                url,
                destination,
                verify_checksum=True,
            )
            if checksum is None:
                raise DevelopmentSourceV2Error(
                    "official checksum evidence is required"
                )
            local_sha = _sha256_file(destination)
            if local_sha != checksum:
                raise DevelopmentSourceV2Error(
                    "V2 local ZIP SHA-256 differs from official checksum"
                )

            parent = None
            continuity = None
            if symbol == "BTCUSDT":
                parent = btc_pins.get(filename)
                if parent is None:
                    raise DevelopmentSourceV2Error(
                        "missing frozen V1 BTC checksum continuity pin"
                    )
                continuity = (
                    checksum == parent == local_sha
                )
                if not continuity:
                    raise DevelopmentSourceV2Error(
                        "BTC provider-byte continuity mismatch"
                    )

            evidence.append(
                ArchiveEvidenceV2(
                    symbol=symbol,
                    year=year,
                    month=month,
                    filename=filename,
                    official_url=url,
                    official_checksum_sha256=checksum,
                    local_zip_sha256=local_sha,
                    parent_v1_btc_checksum_sha256=parent,
                    parent_v1_checksum_continuity_pass=continuity,
                )
            )
            paths.append(destination)

        if tuple(path.name for path in paths) != expected_filenames(symbol):
            raise DevelopmentSourceV2Error(
                "observed V2 archive set differs from frozen inventory"
            )

        bundle, normalized = _build_treatment_aware_bundle(
            symbol,
            tuple(paths),
        )
        projection, projection_sha = build_development_projection_v2(
            bundle,
            tuple(evidence),
            normalized,
        )
        return DevelopmentSourceV2Result(
            symbol=symbol,
            bundle=bundle,
            archive_evidence=tuple(evidence),
            row_accounting=tuple(
                item.to_record(include_rejected_rows=True)
                for item in normalized.archive_accounting
            ),
            aggregate_row_accounting=
                dict(normalized.aggregate_accounting),
            projection_record=projection,
            projection_sha256=projection_sha,
            staging_root=str(root),
        )
    except Exception as exc:
        partial = tuple(evidence)
        shutil.rmtree(root, ignore_errors=True)
        if isinstance(exc, DevelopmentSourceV2Error):
            if exc.partial_archive_evidence:
                raise
            raise DevelopmentSourceV2Error(
                str(exc),
                partial_archive_evidence=partial,
                network_source_access_attempted=
                    network_source_access_attempted,
            ) from exc
        raise DevelopmentSourceV2Error(
            f"Development V2 source acquisition failed: "
            f"{type(exc).__name__}: {exc}",
            partial_archive_evidence=partial,
            network_source_access_attempted=
                network_source_access_attempted,
        ) from exc
