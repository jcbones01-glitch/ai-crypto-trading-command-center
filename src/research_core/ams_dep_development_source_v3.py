"""Fixed Development-only source adapter for AMS-DEP empirical recovery V3."""
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

from .ams_dep_development_execution_lock_v3 import (
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
from .ams_dep_source_coverage_v3 import (
    CoverageAuditV3,
    SourceCoverageV3Error,
    audit_development_source_coverage_v3,
)
from .ams_dep_treatment_aware_normalization_v2 import (
    TreatmentAwareNormalizationError,
    TreatmentAwareNormalizationResult,
    complete_normalization_evidence,
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

PROJECTION_VERSION = "ams-dep-development-projection-v3"
COVERAGE_AUDIT_VERSION = "AMS_DEP_DEVELOPMENT_SOURCE_COVERAGE_V3"
NORMALIZATION_MODE = "TREATMENT_AWARE_RAW_ROW_V2"
EXPECTED_ARCHIVES_PER_SYMBOL = 53
REGISTRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "research/governance/ams_dep_development_execution_v3.json"
)
PARENT_MANIFEST_IDENTITIES = {
    "BTCUSDT": "1590cf8e69ed757eeb6701a218d561448beb2eb6ea09dcd0ae31d15a8f5197cf",
    "ETHUSDT": "d35bf21e309820abc88090bad29601adc1d1ea6b31dcddf0b80d510af4cf542f",
}
_ALLOWED_SYMBOLS = tuple(PARENT_MANIFEST_IDENTITIES)

PARENT_V1 = {
    "run_id": 35834431025,
    "artifact_id": 10738551310,
    "claim_ref": "refs/tags/ams-dep-development-execution-claimed-v1",
    "claim_target": "969f6aeadda4143b0882b8e9169e3f6dd9c177ed",
    "artifact_zip_sha256":
        "b947d8a9d73dd05da0455ad8c1fb7ab845f4a187ff56ec99856b385fc0e403c7",
    "result_json_sha256":
        "19f53015e725526b8baa8da89fec5cdbf58d7e6f9a1985fcc626309ab0e2cca7",
}
PARENT_V2 = {
    "run_id": 35909778426,
    "artifact_id": 10772389334,
    "claim_ref": "refs/tags/ams-dep-development-execution-claimed-v2",
    "claim_target": "f925897a5ef5ab1e34ecaa087b87ee07f779eb56",
    "review_anchor_ref":
        "refs/heads/ams-dep-development-implementation-reviewed-v2",
    "reviewed_candidate":
        "8538332bb20cbd47a0250c86686d367c4aa0aa2d",
    "artifact_zip_sha256":
        "a37dbd7b2a6e31ba69a51c4f43c911aa844044b3852c07fb94151dd600390979",
    "result_json_sha256":
        "251c84d2090f510c80d91932e720648fa19fe26812741cc5018042c763fde144",
}


class DevelopmentSourceV3Error(RuntimeError):
    """Raised when the frozen V3 Development source contract fails."""

    def __init__(
        self,
        message: str,
        *,
        partial_archive_evidence: tuple["ArchiveEvidenceV3", ...] = (),
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


@dataclass(frozen=True)
class ArchiveEvidenceV3:
    symbol: str
    year: int
    month: int
    filename: str
    official_url: str
    official_checksum_sha256: str
    local_zip_sha256: str
    parent_btc_checksum_sha256: str | None
    parent_checksum_continuity_pass: bool | None


@dataclass(frozen=True)
class DevelopmentSourceV3Result:
    symbol: str
    bundle: CertifiedDataBundle
    archive_evidence: tuple[ArchiveEvidenceV3, ...]
    row_accounting: tuple[dict, ...]
    aggregate_row_accounting: dict
    coverage_evidence: dict
    projection_record: dict
    projection_sha256: str
    staging_root: str


def _load_registration() -> dict:
    try:
        value = json.loads(REGISTRATION_PATH.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise DevelopmentSourceV3Error(
            "cannot load V3 Development registration"
        ) from exc
    if value.get("registration_id") != "AMS-DEP-DEVELOPMENT-EXECUTION-V3":
        raise DevelopmentSourceV3Error(
            "unexpected V3 Development registration identity"
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
        raise DevelopmentSourceV3Error(
            "unexpected frozen Development V3 month count"
        )
    return result


def expected_filenames(symbol: str) -> tuple[str, ...]:
    if symbol not in _ALLOWED_SYMBOLS:
        raise DevelopmentSourceV3Error(
            "unsupported AMS-DEP Development V3 symbol"
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
    return hashlib.sha256(
        json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("ascii")
    ).hexdigest()


def _fixed_official_url(symbol: str, year: int, month: int) -> str:
    url = archive_url(symbol, year, month)
    expected_host = urlparse(BINANCE_BASE_URL).netloc
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != expected_host:
        raise DevelopmentSourceV3Error("unexpected Binance archive host")
    expected_name = f"{symbol}-{TIMEFRAME}-{year:04d}-{month:02d}.zip"
    if Path(parsed.path).name != expected_name:
        raise DevelopmentSourceV3Error("unexpected Binance archive filename")
    return url


def _dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DevelopmentSourceV3Error(
            "manifest timestamp must be timezone-aware"
        )
    return parsed.astimezone(timezone.utc)


def _development_partition(bundle: CertifiedDataBundle):
    matches = [
        item for item in bundle.manifest.partitions
        if item.partition == "development"
    ]
    if len(matches) != 1:
        raise DevelopmentSourceV3Error(
            "exactly one Development partition certification required"
        )
    partition = matches[0]
    if (
        _dt(partition.start) != DEVELOPMENT_START
        or _dt(partition.end) != DEVELOPMENT_END
    ):
        raise DevelopmentSourceV3Error(
            "Development partition boundary mismatch"
        )
    return partition


def _development_breaks(bundle: CertifiedDataBundle) -> tuple[dict, ...]:
    values = []
    for item in bundle.manifest.continuity_breaks:
        start, end = _dt(item.start), _dt(item.end)
        if max(start, DEVELOPMENT_START) < min(end, DEVELOPMENT_END):
            values.append(asdict(item))
    values.sort(
        key=lambda item: (
            item["start"],
            item["end"],
            item["reason"],
            tuple(item["anomaly_ids"]),
        )
    )
    return tuple(values)


def _build_coverage_aware_bundle(
    symbol: str,
    paths: tuple[Path, ...],
) -> tuple[
    CertifiedDataBundle,
    TreatmentAwareNormalizationResult,
    CoverageAuditV3,
]:
    ordered = tuple(sorted(paths, key=lambda path: path.name))
    reports = tuple(
        scan_archive(path, symbol, checksum_verified=True)
        for path in ordered
    )
    base_manifest = build_manifest(
        symbol,
        list(reports),
        research_start=DEVELOPMENT_START,
        research_end=DEVELOPMENT_END,
    )
    if base_manifest.source_integrity != "SOURCE VERIFIED":
        raise DevelopmentSourceV3Error(
            "V3 source integrity is not verified"
        )
    if base_manifest.research_certification not in {
        "VALID",
        "VALID WITH DOCUMENTED EXCLUSIONS",
    }:
        raise DevelopmentSourceV3Error(
            "V3 base Development treatment manifest is unusable"
        )
    base_manifest = bind_source_identity(base_manifest, list(ordered))

    try:
        normalized = normalize_development_archives(
            symbol,
            ordered,
            reports,
            base_manifest,
        )
    except TreatmentAwareNormalizationError as exc:
        raise DevelopmentSourceV3Error(
            f"V3 inherited treatment-aware normalization failed: {exc}",
            progressive_normalization_evidence=exc.incident_evidence(),
        ) from exc

    try:
        coverage = audit_development_source_coverage_v3(
            symbol,
            base_manifest,
            (bar.timestamp for bar in normalized.bars),
            tuple(path.name for path in ordered),
        )
    except SourceCoverageV3Error as exc:
        raise DevelopmentSourceV3Error(
            f"V3 source coverage audit failed: {exc}",
            progressive_normalization_evidence=
                complete_normalization_evidence(normalized),
            progressive_coverage_evidence=exc.coverage_evidence or {
                "evidence_status": "PARTIAL_COVERAGE_AUDIT",
                "failure_code": exc.failure_code,
            },
        ) from exc

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
        manifest=coverage.final_manifest,
        raw_archive_paths=ordered,
    )
    try:
        verify_certified_bundle(
            bundle,
            registered_identity=coverage.final_manifest.dataset_identity,
        )
    except PipelineIntegrityError as exc:
        raise DevelopmentSourceV3Error(
            f"V3 coverage-aware bundle failed canonical verification: {exc}",
            progressive_normalization_evidence=
                complete_normalization_evidence(normalized),
            progressive_coverage_evidence={
                **coverage.evidence,
                "failure_code": "CANONICAL_BUNDLE_VERIFICATION_FAIL",
                "failure_stage": "CANONICAL_BUNDLE_VERIFICATION",
            },
        ) from exc
    return bundle, normalized, coverage


def build_development_projection_v3(
    bundle: CertifiedDataBundle,
    archive_evidence: tuple[ArchiveEvidenceV3, ...],
    normalized: TreatmentAwareNormalizationResult,
    coverage: CoverageAuditV3,
) -> tuple[dict, str]:
    if bundle.symbol not in _ALLOWED_SYMBOLS:
        raise DevelopmentSourceV3Error(
            "unsupported V3 Development symbol"
        )
    if len(archive_evidence) != EXPECTED_ARCHIVES_PER_SYMBOL:
        raise DevelopmentSourceV3Error(
            "V3 archive evidence must contain exactly 53 files"
        )
    expected = expected_filenames(bundle.symbol)
    if tuple(item.filename for item in archive_evidence) != expected:
        raise DevelopmentSourceV3Error(
            "V3 archive evidence inventory mismatch"
        )
    ordered_paths = tuple(
        sorted(bundle.raw_archive_paths, key=lambda path: path.name)
    )
    if tuple(path.name for path in ordered_paths) != expected:
        raise DevelopmentSourceV3Error("V3 raw archive inventory mismatch")

    for path, evidence in zip(ordered_paths, archive_evidence):
        local = _sha256_file(path)
        if (
            local != evidence.local_zip_sha256
            or local != evidence.official_checksum_sha256
        ):
            raise DevelopmentSourceV3Error(
                "V3 source archive checksum evidence mismatch"
            )
        if bundle.symbol == "BTCUSDT":
            if (
                evidence.parent_btc_checksum_sha256 is None
                or evidence.parent_checksum_continuity_pass is not True
                or evidence.parent_btc_checksum_sha256 != local
            ):
                raise DevelopmentSourceV3Error(
                    "BTC parent/V3 checksum continuity failure"
                )

    partition = _development_partition(bundle)
    if partition.certification not in {
        "VALID",
        "VALID WITH DOCUMENTED EXCLUSIONS",
    }:
        raise DevelopmentSourceV3Error(
            "V3 Development partition is not certified"
        )

    raw_identity = source_identity(list(ordered_paths))
    breaks = _development_breaks(bundle)
    referenced_ids = set()
    for item in partition.exclusions:
        referenced_ids.update(item.anomaly_ids)
    for item in breaks:
        referenced_ids.update(item["anomaly_ids"])

    accounting_records = [
        item.to_record(include_rejected_rows=False)
        for item in normalized.archive_accounting
    ]
    rejected_record_count = sum(
        item.explicitly_rejected_raw_rows
        for item in normalized.archive_accounting
    )

    record = {
        "projection_version": PROJECTION_VERSION,
        "coverage_audit_version": COVERAGE_AUDIT_VERSION,
        "historical_whole_research_parent_manifest_identity":
            PARENT_MANIFEST_IDENTITIES[bundle.symbol],
        "parent_v1_incident": dict(PARENT_V1),
        "parent_v2_incident": dict(PARENT_V2),
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
            asdict(item) for item in archive_evidence
        ],
        "development_certification": partition.certification,
        "development_certified_segments": [
            asdict(item) for item in partition.certified_segments
        ],
        "development_exclusions": [
            asdict(item) for item in partition.exclusions
        ],
        "development_intersecting_continuity_breaks": list(breaks),
        "development_referenced_interval_ids": sorted(referenced_ids),
        "raw_row_accounting_per_archive": accounting_records,
        "raw_row_accounting_aggregate":
            dict(normalized.aggregate_accounting),
        "rejected_raw_row_record_count": rejected_record_count,
        "rejected_raw_row_records_sha256":
            normalized.aggregate_accounting[
                "rejected_raw_row_records_sha256"
            ],
        "coverage_evidence": dict(coverage.evidence),
        "base_treatment_manifest_identity":
            coverage.evidence["base_treatment_manifest_identity"],
        "final_coverage_aware_manifest_identity":
            coverage.evidence[
                "final_coverage_aware_manifest_identity"
            ],
        "coverage_overlay_only_removes_base_certification": True,
        "no_market_bar_created_or_modified": True,
        "btc_parent_checksum_continuity_pass":
            (
                all(
                    item.parent_checksum_continuity_pass is True
                    for item in archive_evidence
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
        raise DevelopmentSourceV3Error(
            "protected/outcome field leaked into V3 projection"
        )
    return record, _canonical_sha256(record)


def acquire_registered_development_source_v3(
    symbol: str,
) -> DevelopmentSourceV3Result:
    if symbol not in _ALLOWED_SYMBOLS:
        raise DevelopmentSourceV3Error(
            "unsupported AMS-DEP Development V3 symbol"
        )

    # These checks intentionally precede even temporary staging creation.
    assert_development_execution_allowed()
    assert_claim_environment()

    registration = _load_registration()
    btc_pins = registration.get("btc_parent_checksum_pins", {})
    root = Path(tempfile.mkdtemp(prefix="ams-dep-development-v3-"))
    atexit.register(shutil.rmtree, root, ignore_errors=True)
    symbol_root = root / symbol

    evidence: list[ArchiveEvidenceV3] = []
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
                raise DevelopmentSourceV3Error(
                    "official checksum evidence is required"
                )
            local_sha = _sha256_file(destination)
            if local_sha != checksum:
                raise DevelopmentSourceV3Error(
                    "V3 local ZIP SHA-256 differs from official checksum"
                )

            parent = None
            continuity = None
            if symbol == "BTCUSDT":
                parent = btc_pins.get(filename)
                if parent is None:
                    raise DevelopmentSourceV3Error(
                        "missing frozen BTC parent checksum continuity pin"
                    )
                continuity = checksum == parent == local_sha
                if not continuity:
                    raise DevelopmentSourceV3Error(
                        "BTC provider-byte continuity mismatch"
                    )

            evidence.append(
                ArchiveEvidenceV3(
                    symbol=symbol,
                    year=year,
                    month=month,
                    filename=filename,
                    official_url=url,
                    official_checksum_sha256=checksum,
                    local_zip_sha256=local_sha,
                    parent_btc_checksum_sha256=parent,
                    parent_checksum_continuity_pass=continuity,
                )
            )
            paths.append(destination)

        if tuple(path.name for path in paths) != expected_filenames(symbol):
            raise DevelopmentSourceV3Error(
                "observed V3 archive set differs from frozen inventory"
            )

        bundle, normalized, coverage = _build_coverage_aware_bundle(
            symbol, tuple(paths)
        )
        try:
            projection, projection_sha = build_development_projection_v3(
                bundle,
                tuple(evidence),
                normalized,
                coverage,
            )
        except DevelopmentSourceV3Error as exc:
            raise DevelopmentSourceV3Error(
                str(exc),
                partial_archive_evidence=tuple(evidence),
                network_source_access_attempted=
                    network_source_access_attempted,
                progressive_normalization_evidence=
                    exc.progressive_normalization_evidence
                    or complete_normalization_evidence(normalized),
                progressive_coverage_evidence=
                    exc.progressive_coverage_evidence
                    or {
                        **coverage.evidence,
                        "failure_code": "DEVELOPMENT_PROJECTION_V3_FAIL",
                        "failure_stage": "DEVELOPMENT_PROJECTION_V3",
                    },
            ) from exc

        return DevelopmentSourceV3Result(
            symbol=symbol,
            bundle=bundle,
            archive_evidence=tuple(evidence),
            row_accounting=tuple(
                item.to_record(include_rejected_rows=True)
                for item in normalized.archive_accounting
            ),
            aggregate_row_accounting=
                dict(normalized.aggregate_accounting),
            coverage_evidence=dict(coverage.evidence),
            projection_record=projection,
            projection_sha256=projection_sha,
            staging_root=str(root),
        )
    except Exception as exc:
        partial = tuple(evidence)
        shutil.rmtree(root, ignore_errors=True)
        if isinstance(exc, DevelopmentSourceV3Error):
            if (
                exc.partial_archive_evidence
                and exc.network_source_access_attempted
            ):
                raise
            raise DevelopmentSourceV3Error(
                str(exc),
                partial_archive_evidence=(
                    exc.partial_archive_evidence or partial
                ),
                network_source_access_attempted=bool(
                    exc.network_source_access_attempted
                    or network_source_access_attempted
                ),
                progressive_normalization_evidence=
                    exc.progressive_normalization_evidence,
                progressive_coverage_evidence=
                    exc.progressive_coverage_evidence,
            ) from exc
        raise DevelopmentSourceV3Error(
            f"Development V3 source acquisition failed: "
            f"{type(exc).__name__}: {exc}",
            partial_archive_evidence=partial,
            network_source_access_attempted=
                network_source_access_attempted,
            progressive_normalization_evidence=getattr(
                exc, "progressive_normalization_evidence", None
            ),
            progressive_coverage_evidence=getattr(
                exc, "progressive_coverage_evidence", None
            ),
        ) from exc
