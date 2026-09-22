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
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile, ZipInfo

import numpy as np
import scipy

from research_core.ams_dep_pipeline import (
    DEVELOPMENT_END,
    DEVELOPMENT_START,
    CertifiedDataBundle,
    PrimaryRow,
    PrimarySample,
    assemble_primary_family,
    build_certified_bundle_from_archives,
    build_primary_sample,
    exact_timestamp_intersection,
    numerical_inputs,
    recompute_treatment_manifest_identity,
    rejection_reason_counts,
    support_report,
    verify_certified_bundle,
)
from research_core.dependence_statistics import SLOTS
from research_core.dependent_wild_bootstrap_v2 import engineering_fixture

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
        "tests/test_ams_dep_full_pipeline_integrity.py::test_future_bar_mutation_cannot_change_past_ams_v1_state",
    ],
    "FP-02_CONTINUITY_AND_EXACT_HOUR_FAIL_CLOSED": [
        "tests/test_ams_dep_full_pipeline_integrity.py::test_missing_hour_inside_certified_segment_hard_fails",
        "tests/test_ams_dep_full_pipeline_integrity.py::test_documented_gap_is_allowed_only_between_clean_segments",
        "tests/test_ams_dep_full_pipeline_integrity.py::test_continuity_break_restarts_744_bar_warmup_and_is_never_bridged",
    ],
    "FP-03_ROW_TIMING_ENDPOINTS": [
        "tests/test_ams_dep_full_pipeline_integrity.py::test_ams_v1_warmup_and_row_timing_use_t_state_and_t_plus_one_year",
        "tests/test_ams_dep_full_pipeline_integrity.py::test_primary_return_values_use_exact_t_minus_one_t_and_t_plus_one",
        "tests/test_ams_dep_full_pipeline_integrity.py::test_development_end_forward_endpoint_is_never_accepted",
    ],
    "FP-04_COMPLETE_STATE_AND_LABEL_TRANSLATION": [
        "tests/test_ams_dep_full_pipeline_integrity.py::test_ams_v1_warmup_and_row_timing_use_t_state_and_t_plus_one_year",
        "tests/test_ams_dep_full_pipeline_integrity.py::test_unknown_volatility_state_hard_fails_numerical_wiring",
    ],
    "FP-05_SUPPORT_ENFORCEMENT": [
        "tests/test_ams_dep_full_pipeline_integrity.py::test_support_report_enforces_all_fifteen_cells_and_total",
        "tests/test_ams_dep_full_pipeline_integrity.py::test_support_fails_one_cell_below_200_even_when_total_exceeds_5000",
        "tests/test_ams_dep_full_pipeline_integrity.py::test_support_fails_cell_with_fewer_than_ten_dates_at_adequate_row_count",
    ],
    "FP-06_SOURCE_SAMPLE_INVENTORY_AND_EXCLUSION_ACCOUNTING": [
        "tests/test_ams_dep_full_pipeline_integrity.py::test_documented_gap_is_allowed_only_between_clean_segments",
        "tests/test_ams_dep_full_pipeline_integrity.py::test_loaded_bar_outside_certified_or_excluded_inventory_hard_fails",
    ],
    "FP-07_EXACT_CROSS_ASSET_JOIN_AND_LAG_DEFERRAL": [
        "tests/test_ams_dep_full_pipeline_integrity.py::test_exact_timestamp_join_is_set_intersection_not_row_index",
        "tests/test_ams_dep_full_pipeline_integrity.py::test_registered_asynchronous_cross_asset_pattern_uses_exact_intersection",
    ],
    "FP-08_NUMERICAL_HOURS_SEGMENTS_RESTRICTIONS_DWB_HOLM_WIRING": [
        "tests/test_ams_dep_full_pipeline_integrity.py::test_numerical_wiring_preserves_epoch_hours_segments_and_engineering_only",
        "tests/test_ams_dep_full_pipeline_integrity.py::test_same_numerical_arrays_feed_all_three_registered_hypotheses",
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

EXPECTED_FROZEN_PATHS = frozenset(
    {
        "docs/AMS_DEP_FULL_PIPELINE_SYNTHETIC_INTEGRITY_PLAN.md",
        "research/governance/ams_dep_full_pipeline_integrity_v1.json",
        "src/research_core/ams_dep_pipeline.py",
        "src/research_core/ams_dep_empirical_access.py",
        "research/scripts/run_ams_dep_empirical.py",
        "research/scripts/run_ams_dep_full_pipeline_integrity.py",
        "tests/test_ams_dep_full_pipeline_integrity.py",
        "tests/test_ams_dep_empirical_firewall.py",
        "tests/test_ams_dep_full_pipeline_runner.py",
        ".github/workflows/ams-dep-full-pipeline-integrity.yml",
        "research/governance/ams_dep_release_gate_v1.json",
        "pyproject.toml",
    }
)

INVENTORY_KEYS = frozenset(
    {
        "loaded_normalized_source_timestamps",
        "candidate_predictor_timestamps",
        "accepted_predictor_timestamps",
        "rejected_predictor_timestamps",
        "accepted_segment_assignments",
    }
)

ACCESS_FALSE_FIELDS = (
    "market_data_accessed",
    "development_market_outcomes_accessed",
    "validation_or_oos_accessed",
    "strategy_pnl_calculated",
    "paper_trading_authorized",
    "live_trading_authorized",
    "calibration_or_holdout_seed_used",
)



class CertificationLockError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def _git_blob(path: str) -> str:
    return _git("hash-object", "--", path)


def _git_tree_blob(commit: str, path: str) -> str:
    return _git("rev-parse", f"{commit}:{path}")


def _is_ancestor(ancestor: str, descendant: str) -> bool:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=ROOT,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return completed.returncode == 0


def _validate_freeze_contract(
    freeze: dict,
    registration: dict,
    gate: dict,
    current_commit: str,
    *,
    current_blob,
    candidate_blob,
    is_ancestor,
) -> None:
    if freeze.get("freeze_id") != "AMS-DEP-FULL-PIPELINE-IMPLEMENTATION-FREEZE-V1":
        raise CertificationLockError("unexpected implementation freeze identity")
    if freeze.get("status") != "AUTHORIZED_FOR_FIRST_CERTIFICATION":
        raise CertificationLockError("implementation freeze is not authorized")
    if freeze.get("independent_implementation_reviewed") is not True:
        raise CertificationLockError("independent implementation review is not recorded")
    if freeze.get("certification_execution_authorized") is not True:
        raise CertificationLockError("certification execution is not authorized")

    candidate = freeze.get("implementation_candidate_commit")
    reviewed = freeze.get("reviewed_implementation_commit")
    if not candidate:
        raise CertificationLockError("implementation candidate commit is missing")
    if not reviewed:
        raise CertificationLockError("reviewed implementation commit is missing")
    if reviewed != candidate:
        raise CertificationLockError(
            "reviewed implementation commit does not equal frozen candidate"
        )

    frozen_map = freeze.get("file_git_blob_sha1")
    if not isinstance(frozen_map, dict):
        raise CertificationLockError("implementation blob map is missing")
    if set(frozen_map) != EXPECTED_FROZEN_PATHS:
        raise CertificationLockError("implementation blob path set is incomplete or altered")

    approved_existing = registration.get("pinned_existing_production_git_blob_sha1")
    frozen_existing = freeze.get("pinned_existing_production_git_blob_sha1")
    if not isinstance(approved_existing, dict) or frozen_existing != approved_existing:
        raise CertificationLockError(
            "existing-production pin map differs from approved registration"
        )

    try:
        for path, expected in frozen_map.items():
            if candidate_blob(path) != expected:
                raise CertificationLockError(
                    f"candidate implementation blob mismatch: {path}"
                )
            if current_blob(path) != expected:
                raise CertificationLockError(
                    f"executing implementation blob mismatch: {path}"
                )

        for path, expected in approved_existing.items():
            if candidate_blob(path) != expected:
                raise CertificationLockError(
                    f"candidate approved-production blob mismatch: {path}"
                )
            if current_blob(path) != expected:
                raise CertificationLockError(
                    f"executing approved-production blob mismatch: {path}"
                )
    except (KeyError, subprocess.CalledProcessError) as exc:
        raise CertificationLockError("unable to verify frozen Git blobs") from exc

    if not is_ancestor(reviewed, current_commit):
        raise CertificationLockError("reviewed implementation commit is not an ancestor")

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
        raise CertificationLockError(
            "protected gate unexpectedly open: " + ", ".join(wrong)
        )
    if gate.get("v2_synthetic_holdout_passed") is not True:
        raise CertificationLockError("accepted V2 holdout PASS is not recorded")


def _verify_freeze() -> tuple[dict, dict, str]:
    try:
        freeze = json.loads(FREEZE.read_text())
        registration = json.loads(REGISTRATION.read_text())
        gate = json.loads(RELEASE_GATE.read_text())
        current_commit = _git("rev-parse", "HEAD")
        candidate = str(freeze.get("implementation_candidate_commit") or "")
        _validate_freeze_contract(
            freeze,
            registration,
            gate,
            current_commit,
            current_blob=_git_blob,
            candidate_blob=lambda path: _git_tree_blob(candidate, path),
            is_ancestor=_is_ancestor,
        )
    except CertificationLockError:
        raise
    except (OSError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        raise CertificationLockError("cannot verify certification governance") from exc

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


def _write_synthetic_archive(root: Path, symbol: str) -> Path:
    """Write a deterministic Binance-format ZIP for the frozen Development span."""

    missing = datetime(2019, 1, 1, tzinfo=timezone.utc)
    rows: list[str] = []
    cursor = DEVELOPMENT_START
    i = 0
    while cursor < DEVELOPMENT_END:
        if cursor != missing:
            close = (
                Decimal("100")
                + Decimal(i) / Decimal("20")
                + Decimal((i % 17) - 8) / Decimal("50")
            )
            open_ = close - Decimal(".03")
            high = close + Decimal(".10")
            low = close - Decimal(".10")
            volume = Decimal("1000") + Decimal((i * 37) % 211)
            timestamp_ms = int(cursor.timestamp()) * 1000
            rows.append(
                f"{timestamp_ms},{open_},{high},{low},{close},{volume}"
            )
        cursor += timedelta(hours=1)
        i += 1

    path = root / f"{symbol}-1h-synthetic.zip"
    member = f"{symbol}-1h-synthetic.csv"
    info = ZipInfo(member, date_time=(2020, 1, 1, 0, 0, 0))
    info.compress_type = ZIP_STORED
    info.create_system = 3
    info.external_attr = 0o600 << 16
    payload = ("\n".join(rows) + "\n").encode("utf-8")
    with ZipFile(path, "w", compression=ZIP_STORED) as archive:
        archive.writestr(info, payload)
    return path


def _representative_bundle(root: Path, symbol: str) -> CertifiedDataBundle:
    raw = _write_synthetic_archive(root, symbol)
    return build_certified_bundle_from_archives(
        symbol,
        [raw],
        checksum_verified=True,
    )

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


def _stable_json_sha256(value) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()
    return hashlib.sha256(payload).hexdigest()


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

    join = exact_timestamp_intersection(
        samples["BTCUSDT"],
        samples["ETHUSDT"],
        btc_manifest=bundles["BTCUSDT"].manifest,
        eth_manifest=bundles["ETHUSDT"].manifest,
    )

    support = {
        symbol: support_report(_support_fixture(symbol))
        for symbol in ("BTCUSDT", "ETHUSDT")
    }

    numerical_sample = _numerical_fixture()
    wired = numerical_inputs(numerical_sample)
    dwb = {
        hypothesis: engineering_fixture(
            wired["design"],
            wired["target"],
            wired["hours"],
            wired["segments"],
            hypothesis,
            draws=2,
        )
        for hypothesis in ("DEP", "TIME", "STATE")
    }
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

    primary_accounting = {
        symbol: {
            "loaded_rows": len(sample.loaded_timestamps),
            "candidate_rows": sample.candidate_count,
            "accepted_rows": sample.accepted_count,
            "rejected_rows": sample.rejected_count,
            "inventory_sha256": dict(sample.inventory_sha256),
            "exclusion_reason_counts": rejection_reason_counts(sample),
        }
        for symbol, sample in samples.items()
    }
    fixture_identities = {
        symbol: _stable_json_sha256(
            {
                "symbol": symbol,
                "bundle_verification": bundle_evidence[symbol],
                "loaded_timestamp_sha256": primary_accounting[symbol][
                    "inventory_sha256"
                ]["loaded_normalized_source_timestamps"],
                "candidate_timestamp_sha256": primary_accounting[symbol][
                    "inventory_sha256"
                ]["candidate_predictor_timestamps"],
            }
        )
        for symbol in ("BTCUSDT", "ETHUSDT")
    }

    return {
        "fixture_identities": fixture_identities,
        "bundle_verification": bundle_evidence,
        "primary_accounting": primary_accounting,
        "support": support,
        "exact_cross_asset_join": {
            "count": len(join),
            "timestamp_sha256": _digest_timestamps(join),
        },
        "numerical_wiring": {
            "design_shape": list(wired["design"].shape),
            "hour_vector_sha256": _digest_ints(wired["hours"]),
            "segment_vector_sha256": _digest_ints(wired["segments"]),
            "engineering_fixtures": dwb,
        },
        "six_slot_assembly": holm,
        "directed_cross_asset_lagged_diagnostics": {
            "status": "BLOCKED_PENDING_SEPARATE_CROSS_ASSET_LAG_INTEGRITY_SPEC",
            "authorized_by_v1_pass": False,
        },
    }


def _is_hex64(value) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def _evaluate_fp11(report: dict, evidence: dict, freeze: dict, registration: dict) -> dict:
    checks: dict[str, bool] = {}

    checks["top_level_hashes"] = all(
        _is_hex64(report.get(field))
        for field in (
            "plan_sha256",
            "registration_sha256",
            "implementation_freeze_sha256",
        )
    )

    expected_existing = registration["pinned_existing_production_git_blob_sha1"]
    reported_existing = report.get("existing_production_blobs", {})
    checks["existing_blob_path_set"] = set(reported_existing) == set(expected_existing)
    checks["existing_blob_equality"] = checks["existing_blob_path_set"] and all(
        reported_existing[path].get("expected") == expected
        and reported_existing[path].get("observed") == expected
        for path, expected in expected_existing.items()
    )

    expected_impl = freeze["file_git_blob_sha1"]
    reported_impl = report.get("implementation_blobs", {})
    checks["implementation_blob_path_set"] = set(reported_impl) == set(expected_impl)
    checks["implementation_blob_equality"] = checks["implementation_blob_path_set"] and all(
        reported_impl[path].get("expected") == expected
        and reported_impl[path].get("observed") == expected
        for path, expected in expected_impl.items()
    )

    fixture_ids = evidence.get("fixture_identities", {})
    bundle = evidence.get("bundle_verification", {})
    accounting = evidence.get("primary_accounting", {})
    support = evidence.get("support", {})
    symbols = ("BTCUSDT", "ETHUSDT")
    checks["exact_symbol_sets"] = all(
        set(section) == set(symbols)
        for section in (fixture_ids, bundle, accounting, support)
    )

    bundle_checks = []
    fixture_checks = []
    accounting_checks = []
    support_checks = []
    expected_cells = {
        f"{year}|{state}"
        for year in (2017, 2018, 2019, 2020, 2021)
        for state in ("VOL_LOW", "VOL_NORMAL", "VOL_HIGH")
    }
    for symbol in symbols:
        if symbol not in bundle or symbol not in accounting or symbol not in support:
            bundle_checks.append(False)
            fixture_checks.append(False)
            accounting_checks.append(False)
            support_checks.append(False)
            continue

        b = bundle[symbol]
        source_ids = (
            b.get("raw_source_identity"),
            b.get("manifest_source_identity"),
            b.get("metadata_source_identity"),
        )
        manifest_ids = (
            b.get("stored_manifest_identity"),
            b.get("recomputed_manifest_identity"),
        )
        bundle_checks.append(
            all(_is_hex64(value) for value in source_ids + manifest_ids)
            and len(set(source_ids)) == 1
            and len(set(manifest_ids)) == 1
            and _is_hex64(b.get("normalized_dataset_id"))
            and _is_hex64(b.get("normalized_content_hash"))
            and _is_hex64(b.get("whole_bundle_missing_interval_sha256"))
            and isinstance(b.get("whole_bundle_missing_intervals"), int)
            and b["whole_bundle_missing_intervals"] >= 1
            and isinstance(b.get("documented_exclusion_count"), int)
            and b["documented_exclusion_count"] >= 1
            and isinstance(b.get("certified_segment_count"), int)
            and b["certified_segment_count"] >= 1
        )

        a = accounting[symbol]
        inventory = a.get("inventory_sha256", {})
        accounting_checks.append(
            isinstance(a.get("loaded_rows"), int)
            and a["loaded_rows"] > 0
            and isinstance(a.get("candidate_rows"), int)
            and a["candidate_rows"] > 0
            and a["candidate_rows"] == a.get("accepted_rows", -1) + a.get("rejected_rows", -1)
            and set(inventory) == INVENTORY_KEYS
            and all(_is_hex64(value) for value in inventory.values())
        )

        expected_fixture = _stable_json_sha256(
            {
                "symbol": symbol,
                "bundle_verification": b,
                "loaded_timestamp_sha256": inventory.get(
                    "loaded_normalized_source_timestamps"
                ),
                "candidate_timestamp_sha256": inventory.get(
                    "candidate_predictor_timestamps"
                ),
            }
        )
        fixture_checks.append(
            _is_hex64(fixture_ids.get(symbol))
            and fixture_ids.get(symbol) == expected_fixture
        )

        s = support[symbol]
        cells = s.get("cells", {})
        support_checks.append(
            s.get("pass") is True
            and s.get("total_rows_pass") is True
            and isinstance(s.get("total_rows"), int)
            and s["total_rows"] >= 5000
            and set(cells) == expected_cells
            and len(cells) == 15
            and all(
                isinstance(cell.get("rows"), int)
                and cell["rows"] >= 200
                and isinstance(cell.get("distinct_utc_dates"), int)
                and cell["distinct_utc_dates"] >= 10
                and cell.get("pass") is True
                for cell in cells.values()
            )
        )

    checks["bundle_identity_semantics"] = all(bundle_checks)
    checks["fixture_identity_semantics"] = all(fixture_checks)
    checks["inventory_accounting_semantics"] = all(accounting_checks)
    checks["support_semantics"] = all(support_checks)

    join = evidence.get("exact_cross_asset_join", {})
    checks["join_semantics"] = (
        isinstance(join.get("count"), int)
        and join["count"] > 0
        and _is_hex64(join.get("timestamp_sha256"))
    )

    numerical = evidence.get("numerical_wiring", {})
    engineering = numerical.get("engineering_fixtures", {})
    checks["numerical_digest_semantics"] = (
        numerical.get("design_shape") == [75, 14]
        and _is_hex64(numerical.get("hour_vector_sha256"))
        and _is_hex64(numerical.get("segment_vector_sha256"))
        and set(engineering) == {"DEP", "TIME", "STATE"}
        and all(
            item.get("classification") == "ENGINEERING_ONLY_NOT_CALIBRATION"
            and item.get("p_value") is None
            for item in engineering.values()
        )
    )

    family = evidence.get("six_slot_assembly", [])
    exact_slots = [item.get("slot") for item in family] == list(SLOTS)
    unavailable_semantics = all(
        (
            item.get("available") is False
            and item.get("calculation_p") == 1.0
            and item.get("adjusted_p") is None
            and item.get("reject") is False
        )
        if item.get("raw_p") is None
        else (
            item.get("available") is True
            and isinstance(item.get("calculation_p"), float)
            and 0.0 <= item["calculation_p"] <= 1.0
            and item.get("adjusted_p") is not None
        )
        for item in family
    )
    checks["six_slot_holm_semantics"] = (
        len(family) == 6 and exact_slots and unavailable_semantics
    )

    deferred = evidence.get("directed_cross_asset_lagged_diagnostics", {})
    checks["deferred_lag_semantics"] = (
        deferred.get("status")
        == "BLOCKED_PENDING_SEPARATE_CROSS_ASSET_LAG_INTEGRITY_SPEC"
        and deferred.get("authorized_by_v1_pass") is False
    )

    checks["protected_access_flags"] = all(
        report.get(field) is False for field in ACCESS_FALSE_FIELDS
    )

    return {"pass": all(checks.values()), "checks": checks}


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

    report["oracles"]["FP-11_IMMUTABLE_PROVENANCE_OUTPUT_INVENTORY"] = (
        _evaluate_fp11(report, report["fixture_evidence"], freeze, registration)
    )


    all_pass = all(value.get("pass") is True for value in report["oracles"].values())
    report["decision"] = PASS_TOKEN if all_pass else FAIL_TOKEN

    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(report["decision"])
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
