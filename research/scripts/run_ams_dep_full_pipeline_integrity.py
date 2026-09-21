"""Deterministic AMS-DEP full-pipeline synthetic integrity certification.

This runner is fail-closed until the independently reviewed implementation-freeze
manifest explicitly authorizes the first certification. It uses generated
fixtures only and never opens empirical market data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import numpy as np
import scipy

from research_core.ams_dep_pipeline import (
    DEVELOPMENT_END,
    DEVELOPMENT_START,
    CertifiedDataBundle,
    PrimaryRow,
    PrimarySample,
    assemble_primary_family,
    build_primary_sample,
    exact_timestamp_intersection,
    numerical_inputs,
    recompute_treatment_manifest_identity,
    rejection_reason_counts,
    support_report,
    verify_certified_bundle,
)
from research_core.data_ingestion import make_metadata
from research_core.data_interfaces import MarketBar
from research_core.data_quality_treatment_v2 import (
    CertifiedSegment,
    Exclusion,
    PartitionCertification,
    ResearchTreatmentManifest,
)
from research_core.dependent_wild_bootstrap_v2 import engineering_fixture
from research_core.source_identity import source_identity

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "docs/AMS_DEP_FULL_PIPELINE_SYNTHETIC_INTEGRITY_PLAN.md"
REGISTRATION = ROOT / "research/governance/ams_dep_full_pipeline_integrity_v1.json"
FREEZE = ROOT / "research/governance/ams_dep_full_pipeline_implementation_freeze_v1.json"
RELEASE_GATE = ROOT / "research/governance/ams_dep_release_gate_v1.json"

PASS_TOKEN = "FULL_PIPELINE_SYNTHETIC_INTEGRITY_PASS"
FAIL_TOKEN = "FULL_PIPELINE_SYNTHETIC_INTEGRITY_FAIL"

ORACLE_TESTS = {
    "FP-01_AMS_V1_WARMUP": [
        "tests/test_ams_dep_full_pipeline_integrity.py::test_ams_v1_warmup_and_row_timing_use_t_state_and_t_plus_one_year",
    ],
    "FP-02_CONTINUITY_AND_EXACT_HOUR_FAIL_CLOSED": [
        "tests/test_ams_dep_full_pipeline_integrity.py::test_missing_hour_inside_certified_segment_hard_fails",
        "tests/test_ams_dep_full_pipeline_integrity.py::test_documented_gap_is_allowed_only_between_clean_segments",
    ],
    "FP-03_ROW_TIMING_ENDPOINTS": [
        "tests/test_ams_dep_full_pipeline_integrity.py::test_ams_v1_warmup_and_row_timing_use_t_state_and_t_plus_one_year",
        "tests/test_ams_dep_full_pipeline_integrity.py::test_development_end_forward_endpoint_is_never_accepted",
    ],
    "FP-04_COMPLETE_STATE_AND_LABEL_TRANSLATION": [
        "tests/test_ams_dep_full_pipeline_integrity.py::test_ams_v1_warmup_and_row_timing_use_t_state_and_t_plus_one_year",
        "tests/test_ams_dep_full_pipeline_integrity.py::test_unknown_volatility_state_hard_fails_numerical_wiring",
    ],
    "FP-05_SUPPORT_ENFORCEMENT": [
        "tests/test_ams_dep_full_pipeline_integrity.py::test_support_report_enforces_all_fifteen_cells_and_total",
    ],
    "FP-06_SOURCE_SAMPLE_INVENTORY_AND_EXCLUSION_ACCOUNTING": [
        "tests/test_ams_dep_full_pipeline_integrity.py::test_documented_gap_is_allowed_only_between_clean_segments",
    ],
    "FP-07_EXACT_CROSS_ASSET_JOIN_AND_LAG_DEFERRAL": [
        "tests/test_ams_dep_full_pipeline_integrity.py::test_exact_timestamp_join_is_set_intersection_not_row_index",
    ],
    "FP-08_NUMERICAL_HOURS_SEGMENTS_RESTRICTIONS_DWB_HOLM_WIRING": [
        "tests/test_ams_dep_full_pipeline_integrity.py::test_numerical_wiring_preserves_epoch_hours_segments_and_engineering_only",
        "tests/test_ams_dep_full_pipeline_integrity.py::test_holm_family_keeps_exact_six_slots_and_unavailable_entries",
    ],
    "FP-09_TWO_STAGE_SOURCE_IDENTITY_CERTIFICATION": [
        "tests/test_ams_dep_full_pipeline_integrity.py::test_manifest_identity_is_recomputed_and_stale_content_fails",
        "tests/test_ams_dep_full_pipeline_integrity.py::test_altered_raw_archive_bytes_fail_before_pipeline",
        "tests/test_ams_dep_full_pipeline_integrity.py::test_private_archive_set_identity_cannot_substitute_authoritative_source_identity",
        "tests/test_ams_dep_full_pipeline_integrity.py::test_non_missing_whole_bundle_validation_issue_hard_fails",
    ],
    "FP-10_PROTECTED_READ_AND_PRODUCTION_INTERFACE_BLOCKING": [
        "tests/test_ams_dep_empirical_firewall.py",
    ],
}


class CertificationLockError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _git_blob(path: str) -> str:
    return _git("hash-object", "--", path)


def _verify_freeze() -> tuple[dict, dict, str]:
    try:
        freeze = json.loads(FREEZE.read_text())
        registration = json.loads(REGISTRATION.read_text())
        gate = json.loads(RELEASE_GATE.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise CertificationLockError("cannot load certification governance") from exc

    if freeze.get("freeze_id") != "AMS-DEP-FULL-PIPELINE-IMPLEMENTATION-FREEZE-V1":
        raise CertificationLockError("unexpected implementation freeze identity")
    if freeze.get("status") != "AUTHORIZED_FOR_FIRST_CERTIFICATION":
        raise CertificationLockError("implementation freeze is not authorized")
    if freeze.get("certification_execution_authorized") is not True:
        raise CertificationLockError("certification execution is not authorized")
    if freeze.get("reviewed_implementation_commit") in (None, ""):
        raise CertificationLockError("reviewed implementation commit is missing")

    if freeze.get("plan_sha256") != _sha256(PLAN):
        raise CertificationLockError("approved plan hash mismatch")
    if freeze.get("registration_sha256") != _sha256(REGISTRATION):
        raise CertificationLockError("approved registration hash mismatch")

    current_commit = _git("rev-parse", "HEAD")
    reviewed = str(freeze["reviewed_implementation_commit"])
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", reviewed, current_commit],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if ancestor.returncode != 0:
        raise CertificationLockError("reviewed implementation commit is not an ancestor")

    for path, expected in freeze.get("file_git_blob_sha1", {}).items():
        if _git_blob(path) != expected:
            raise CertificationLockError(f"implementation blob mismatch: {path}")

    for path, expected in registration["pinned_existing_production_git_blob_sha1"].items():
        if _git_blob(path) != expected:
            raise CertificationLockError(f"approved production blob changed: {path}")

    required_false = (
        "full_pipeline_synthetic_integrity_passed",
        "separate_empirical_release_approved",
        "development_market_data_execution_authorized",
        "validation_or_oos_access_authorized",
        "strategy_pnl_authorized",
        "paper_trading_authorized",
        "live_trading_authorized",
    )
    wrong = [field for field in required_false if gate.get(field) is not False]
    if wrong:
        raise CertificationLockError("protected gate unexpectedly open: " + ", ".join(wrong))
    if gate.get("v2_synthetic_holdout_passed") is not True:
        raise CertificationLockError("accepted V2 holdout PASS is not recorded")

    return freeze, registration, current_commit


def _run_pytest(nodeids: list[str]) -> dict:
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *nodeids],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={
            **os.environ,
            "OPENBLAS_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
        },
    )
    output = (completed.stdout + completed.stderr).strip()
    return {
        "pass": completed.returncode == 0,
        "returncode": completed.returncode,
        "tests": nodeids,
        "output_tail": output[-4000:],
    }


def _bars(start: datetime, count: int, symbol: str) -> tuple[MarketBar, ...]:
    canonical = "BTC/USDT" if symbol == "BTCUSDT" else "ETH/USDT"
    out = []
    for i in range(count):
        t = start + timedelta(hours=i)
        close = (
            Decimal("100")
            + Decimal(i) / Decimal("20")
            + Decimal((i % 17) - 8) / Decimal("50")
        )
        out.append(
            MarketBar(
                t,
                canonical,
                close - Decimal(".03"),
                close + Decimal(".10"),
                close - Decimal(".10"),
                close,
                Decimal("1000") + Decimal((i * 37) % 211),
            )
        )
    return tuple(out)


def _synthetic_manifest(
    raw_identity: str,
    symbol: str,
    segments: tuple[CertifiedSegment, ...],
    exclusions: tuple[Exclusion, ...],
) -> ResearchTreatmentManifest:
    certification = "VALID" if not exclusions else "VALID WITH DOCUMENTED EXCLUSIONS"
    partition = PartitionCertification(
        "development",
        DEVELOPMENT_START.isoformat(),
        DEVELOPMENT_END.isoformat(),
        certification,
        segments,
        exclusions,
    )
    manifest = ResearchTreatmentManifest(
        source_version=f"binance-public-data-spot-1h:{raw_identity}",
        treatment_protocol_version="gate1a-v1",
        normalization_version="gate1-v1",
        symbol=symbol,
        timeframe="1h",
        research_start=DEVELOPMENT_START.isoformat(),
        research_end=DEVELOPMENT_END.isoformat(),
        anomaly_ids=(),
        affected_regions=(),
        continuity_breaks=(),
        exclusions=exclusions,
        certified_segments=segments,
        partitions=(partition,),
        source_integrity="SOURCE VERIFIED",
        research_certification=certification,
        dataset_identity="",
    )
    return replace(
        manifest,
        dataset_identity=recompute_treatment_manifest_identity(manifest),
    )


def _representative_bundle(root: Path, symbol: str) -> CertifiedDataBundle:
    start = datetime(2019, 1, 1, tzinfo=timezone.utc)
    full = _bars(start, 1600, symbol)
    missing = start + timedelta(hours=800)
    bars = tuple(bar for bar in full if bar.timestamp != missing)

    raw = root / f"{symbol}-synthetic-source.zip"
    raw.write_bytes((symbol + "|full-pipeline-synthetic-fixture").encode())
    raw_identity = source_identity([raw])

    exclusion = Exclusion(
        missing.isoformat(),
        (missing + timedelta(hours=1)).isoformat(),
        ("full-pipeline-synthetic-gap",),
        "deterministic documented synthetic exclusion",
    )
    segments = (
        CertifiedSegment(start.isoformat(), missing.isoformat()),
        CertifiedSegment(
            (missing + timedelta(hours=1)).isoformat(),
            (start + timedelta(hours=1600)).isoformat(),
        ),
    )
    manifest = _synthetic_manifest(raw_identity, symbol, segments, (exclusion,))
    metadata = make_metadata(
        list(bars), symbol, "milliseconds", source_identity=raw_identity
    )
    return CertifiedDataBundle(symbol, bars, metadata, manifest, (raw,))


def _support_fixture(symbol: str) -> PrimarySample:
    rows = []
    i = 0
    for year in range(2017, 2022):
        for state in ("VOL_LOW", "VOL_NORMAL", "VOL_HIGH"):
            for j in range(334):
                t = datetime(year, 1, 1, tzinfo=timezone.utc) + timedelta(hours=j * 2)
                rows.append(
                    PrimaryRow(
                        t,
                        t + timedelta(hours=1),
                        0.001 + i * 1e-8,
                        0.002 + ((i % 13) - 6) * 1e-6,
                        year,
                        state,
                        "ACTIVITY_NORMAL",
                        "TREND_NEUTRAL",
                        int(t.timestamp() // 3600),
                        year - 2017,
                    )
                )
                i += 1
    timestamps = tuple(row.predictor_timestamp for row in rows)
    assignments = tuple((row.predictor_timestamp, row.segment_id) for row in rows)
    return PrimarySample(
        symbol=symbol,
        rows=tuple(rows),
        rejected=(),
        loaded_timestamps=timestamps,
        candidate_timestamps=timestamps,
        accepted_timestamps=timestamps,
        rejected_timestamps=(),
        segment_assignments=assignments,
        inventory_sha256={},
    )


def _numerical_fixture() -> PrimarySample:
    rows = []
    i = 0
    for year in range(2017, 2022):
        for state_index, state in enumerate(("VOL_LOW", "VOL_NORMAL", "VOL_HIGH")):
            for j in range(5):
                t = datetime(year, 2 + state_index, 1, tzinfo=timezone.utc) + timedelta(hours=j)
                x = 0.001 * (i + 1) + 0.00003 * ((i % 7) - 3)
                y = 0.0007 * ((i % 11) - 5) + 0.2 * x * x
                rows.append(
                    PrimaryRow(
                        t,
                        t + timedelta(hours=1),
                        x,
                        y,
                        year,
                        state,
                        "ACTIVITY_NORMAL",
                        "TREND_NEUTRAL",
                        int(t.timestamp() // 3600),
                        year - 2017,
                    )
                )
                i += 1
    timestamps = tuple(row.predictor_timestamp for row in rows)
    return PrimarySample(
        symbol="BTCUSDT",
        rows=tuple(rows),
        rejected=(),
        loaded_timestamps=timestamps,
        candidate_timestamps=timestamps,
        accepted_timestamps=timestamps,
        rejected_timestamps=(),
        segment_assignments=tuple((row.predictor_timestamp, row.segment_id) for row in rows),
        inventory_sha256={},
    )


def _digest_ints(values) -> str:
    return hashlib.sha256(
        ("\n".join(str(int(value)) for value in values) + "\n").encode()
    ).hexdigest()


def _digest_timestamps(values) -> str:
    return hashlib.sha256(
        ("\n".join(value.astimezone(timezone.utc).isoformat() for value in values) + "\n").encode()
    ).hexdigest()


def _fixture_evidence(root: Path) -> dict:
    bundles = {
        symbol: _representative_bundle(root, symbol)
        for symbol in ("BTCUSDT", "ETHUSDT")
    }
    samples = {}
    bundle_evidence = {}
    for symbol, bundle in bundles.items():
        synthetic_identity = bundle.manifest.dataset_identity
        bundle_evidence[symbol] = verify_certified_bundle(
            bundle, registered_identity=synthetic_identity
        )
        samples[symbol] = build_primary_sample(
            bundle, registered_identity=synthetic_identity
        )

    join = exact_timestamp_intersection(samples["BTCUSDT"], samples["ETHUSDT"])

    support = {
        symbol: support_report(_support_fixture(symbol))
        for symbol in ("BTCUSDT", "ETHUSDT")
    }

    numerical_sample = _numerical_fixture()
    wired = numerical_inputs(numerical_sample)
    dwb = engineering_fixture(
        wired["design"],
        wired["target"],
        wired["hours"],
        wired["segments"],
        "DEP",
        draws=2,
    )
    holm = assemble_primary_family(
        {
            "BTC_DEP": 0.01,
            "BTC_TIME": None,
            "BTC_STATE": 0.20,
            "ETH_DEP": 0.02,
            "ETH_TIME": 0.50,
            "ETH_STATE": 0.03,
        }
    )

    return {
        "bundle_verification": bundle_evidence,
        "primary_accounting": {
            symbol: {
                "loaded_rows": len(sample.loaded_timestamps),
                "candidate_rows": sample.candidate_count,
                "accepted_rows": sample.accepted_count,
                "rejected_rows": sample.rejected_count,
                "inventory_sha256": dict(sample.inventory_sha256),
                "exclusion_reason_counts": rejection_reason_counts(sample),
            }
            for symbol, sample in samples.items()
        },
        "support": support,
        "exact_cross_asset_join": {
            "count": len(join),
            "timestamp_sha256": _digest_timestamps(join),
        },
        "numerical_wiring": {
            "design_shape": list(wired["design"].shape),
            "hour_vector_sha256": _digest_ints(wired["hours"]),
            "segment_vector_sha256": _digest_ints(wired["segments"]),
            "engineering_fixture": dwb,
        },
        "six_slot_assembly": holm,
        "directed_cross_asset_lagged_diagnostics": {
            "status": "BLOCKED_PENDING_SEPARATE_CROSS_ASSET_LAG_INTEGRITY_SPEC",
            "authorized_by_v1_pass": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    freeze, registration, commit = _verify_freeze()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "classification": "AMS_DEP_FULL_PIPELINE_SYNTHETIC_INTEGRITY_V1",
        "version": 1,
        "executing_commit": commit,
        "plan_sha256": _sha256(PLAN),
        "registration_sha256": _sha256(REGISTRATION),
        "implementation_freeze_sha256": _sha256(FREEZE),
        "implementation_freeze_status": freeze["status"],
        "existing_production_blobs": {
            path: {
                "expected": expected,
                "observed": _git_blob(path),
            }
            for path, expected in registration[
                "pinned_existing_production_git_blob_sha1"
            ].items()
        },
        "implementation_blobs": {
            path: {
                "expected": expected,
                "observed": _git_blob(path),
            }
            for path, expected in freeze["file_git_blob_sha1"].items()
        },
        "python_version": sys.version.split()[0],
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "oracles": {},
        "market_data_accessed": False,
        "development_market_outcomes_accessed": False,
        "validation_or_oos_accessed": False,
        "strategy_pnl_calculated": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
        "calibration_or_holdout_seed_used": False,
    }

    for oracle, nodeids in ORACLE_TESTS.items():
        report["oracles"][oracle] = _run_pytest(nodeids)

    with tempfile.TemporaryDirectory(prefix="ams-dep-full-pipeline-") as directory:
        report["fixture_evidence"] = _fixture_evidence(Path(directory))

    required_fixture_keys = {
        "bundle_verification",
        "primary_accounting",
        "support",
        "exact_cross_asset_join",
        "numerical_wiring",
        "six_slot_assembly",
        "directed_cross_asset_lagged_diagnostics",
    }
    fp11_pass = required_fixture_keys.issubset(report["fixture_evidence"])
    report["oracles"]["FP-11_IMMUTABLE_PROVENANCE_OUTPUT_INVENTORY"] = {
        "pass": fp11_pass,
        "required_fixture_keys": sorted(required_fixture_keys),
    }

    all_pass = all(value.get("pass") is True for value in report["oracles"].values())
    report["decision"] = PASS_TOKEN if all_pass else FAIL_TOKEN

    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(report["decision"])
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
