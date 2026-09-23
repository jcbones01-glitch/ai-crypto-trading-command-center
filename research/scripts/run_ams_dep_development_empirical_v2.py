"""AMS-DEP Development empirical recovery runner V2.

V2 changes only the treatment-aware source-normalization seam. The primary
sample and statistical path remain identical to the approved V1 execution
contract. This runner is inert unless every V2 governance lock and durable ref
verifies for the exact executing commit.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import scipy

from research_core.ams_dep_development_execution_lock_v2 import (
    DEFAULT_CLAIM_REF,
    DEFAULT_EXECUTION_MANIFEST,
    DEFAULT_IMPLEMENTATION_FREEZE,
    DEFAULT_REVIEW_ANCHOR_REF,
    assert_claim_environment,
    assert_development_execution_allowed,
)
from research_core.ams_dep_empirical_access_v2 import load_development_source
from research_core.ams_dep_pipeline import (
    assemble_primary_family,
    build_primary_sample,
    exact_timestamp_intersection,
    numerical_inputs,
    recompute_treatment_manifest_identity,
    rejection_reason_counts,
    support_report,
)
from research_core.dependence_statistics import InferenceError, SLOTS
from research_core.dependent_wild_bootstrap_v2 import (
    BOOTSTRAP_DRAWS,
    FixedOLS,
    ParzenGeometry,
    bootstrap_p_value,
    restricted_components,
    wald,
)
from research_core.release_gate import DEFAULT_GATE, assert_ams_dep_empirical_release_allowed

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "docs/AMS_DEP_DEVELOPMENT_EMPIRICAL_EXECUTION_SPEC_V2.md"
REGISTRATION_PATH = ROOT / "research/governance/ams_dep_development_execution_v2.json"
OUTPUT_DIR = ROOT / "research/experiments/ams_dep_development_empirical_v2"
OUTPUT_PATH = OUTPUT_DIR / "result.json"
INCIDENT_PATH = OUTPUT_DIR / "incident.json"

EMPIRICAL_BOOTSTRAP_ROOT = 2026092201
EMPIRICAL_SENTINEL = 4294967295
ASSET_ORDER = ("BTCUSDT", "ETHUSDT")
HYPOTHESIS_ORDER = ("DEP", "TIME", "STATE")
INVALID_FRACTION_CEILING = 0.01

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

INCIDENT_STATE: dict = {}


def _ambient_execution_context() -> dict:
    return {
        "executing_commit": os.environ.get("GITHUB_SHA"),
        "workflow_event": os.environ.get("GITHUB_EVENT_NAME"),
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
        "workflow_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "workflow_job": os.environ.get("GITHUB_JOB"),
        "workflow_job_id_where_available": os.environ.get("GITHUB_JOB_ID"),
        "confirmation_token": "AMS_DEP_DEVELOPMENT_EMPIRICAL_V2",
        "confirmation_verified":
            os.environ.get("AMS_DEP_DEVELOPMENT_V2_CONFIRMATION_VERIFIED")
            == "true",
        "forwarded_claim_ref":
            os.environ.get("AMS_DEP_DEVELOPMENT_V2_CLAIM_REF"),
        "forwarded_claim_sha":
            os.environ.get("AMS_DEP_DEVELOPMENT_V2_CLAIM_SHA"),
        "durable_claim_verified_against_github": False,
    }


def _reset_incident_state() -> None:
    INCIDENT_STATE.clear()
    INCIDENT_STATE.update(
        {
            "stage": "PRE_AUTHORITY",
            "execution_provenance": _ambient_execution_context(),
            "source_provenance": {},
            "sample_provenance": {},
            "numerical_provenance": {},
            "inference_provenance": {"slot_results": {}},
            "market_data_accessed": False,
            "development_market_outcomes_accessed": False,
        }
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest_lines(values) -> str:
    lines = [str(value) for value in values]
    payload = ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _git_blob(relative: str) -> str:
    return subprocess.check_output(
        ["git", "hash-object", "--", relative],
        cwd=ROOT,
        text=True,
    ).strip()


def _run_slot(inputs: dict, hypothesis: str, asset_index: int, hypothesis_index: int) -> dict:
    design = inputs["design"]
    target = inputs["target"]
    hours = inputs["hours"]
    segments = inputs["segments"]
    geometry = ParzenGeometry(hours, segments)
    try:
        model = FixedOLS(design)
        observed = wald(model.fit(target, geometry), hypothesis)
        fitted, residual = restricted_components(design, target, geometry, hypothesis)
    except (InferenceError, np.linalg.LinAlgError, ValueError) as exc:
        return {
            "available": False,
            "raw_p": None,
            "observed_wald": None,
            "requested_draws": 0,
            "invalid_draws": 0,
            "invalid_fraction": None,
            "error": str(exc),
        }

    statistics = []
    for bootstrap_index in range(BOOTSTRAP_DRAWS):
        weights = geometry.multipliers(
            [
                EMPIRICAL_BOOTSTRAP_ROOT,
                2,
                EMPIRICAL_SENTINEL,
                EMPIRICAL_SENTINEL,
                asset_index,
                hypothesis_index,
                bootstrap_index,
            ]
        )
        pseudo_y = fitted + residual * weights
        try:
            value = wald(model.fit(pseudo_y, geometry), hypothesis)
        except (InferenceError, np.linalg.LinAlgError, ValueError):
            value = None
        statistics.append(value)

    p = bootstrap_p_value(observed, statistics)
    return {
        "available": True,
        "raw_p": float(p["raw_p"]),
        "observed_wald": float(observed),
        "requested_draws": int(p["requested_draws"]),
        "invalid_draws": int(p["invalid_draws"]),
        "invalid_fraction": float(p["invalid_fraction"]),
        "error": None,
    }


def _unavailable_support_slot() -> dict:
    return {
        "available": False,
        "raw_p": None,
        "observed_wald": None,
        "requested_draws": 0,
        "invalid_draws": 0,
        "invalid_fraction": None,
        "error": "INSUFFICIENT_REGISTERED_SUPPORT",
    }


def _inference_validity_fail(slot_results: dict) -> bool:
    return any(
        value["available"]
        and value["invalid_fraction"] is not None
        and value["invalid_fraction"] > INVALID_FRACTION_CEILING
        for value in slot_results.values()
    )


def _source_record(result) -> dict:
    bundle = result.bundle
    manifest = bundle.manifest
    prefix = "binance-public-data-spot-1h:"
    manifest_source_identity = (
        manifest.source_version[len(prefix):]
        if manifest.source_version.startswith(prefix)
        else None
    )
    return {
        "status": "COMPLETE",
        "historical_whole_research_parent_manifest_identity":
            result.projection_record[
                "historical_whole_research_parent_manifest_identity"
            ],
        "expected_archive_inventory": [
            value["filename"]
            for value in result.projection_record["ordered_archive_evidence_53"]
        ],
        "observed_archive_inventory": [
            value.filename for value in result.archive_evidence
        ],
        "archive_evidence": [asdict(value) for value in result.archive_evidence],
        "raw_row_accounting_per_archive": list(result.row_accounting),
        "raw_row_accounting_aggregate":
            dict(result.aggregate_row_accounting),
        "authoritative_development_raw_source_identity":
            result.projection_record[
                "authoritative_development_raw_source_identity"
            ],
        "helper_manifest_source_identity": manifest_source_identity,
        "metadata_source_identity": bundle.metadata.source_identity,
        "stored_helper_manifest_identity": manifest.dataset_identity,
        "recomputed_helper_manifest_identity":
            recompute_treatment_manifest_identity(manifest),
        "development_projection_record": result.projection_record,
        "development_projection_sha256": result.projection_sha256,
        "normalized_dataset_id": bundle.metadata.dataset_id,
        "normalized_content_hash": bundle.metadata.content_hash,
        "normalized_row_count": bundle.metadata.row_count,
        "normalized_start_timestamp": bundle.metadata.start_timestamp,
        "normalized_end_timestamp": bundle.metadata.end_timestamp,
        "development_certification":
            result.projection_record["development_certification"],
        "development_certified_segments":
            result.projection_record["development_certified_segments"],
        "development_exclusions":
            result.projection_record["development_exclusions"],
        "development_intersecting_continuity_breaks":
            result.projection_record[
                "development_intersecting_continuity_breaks"
            ],
        "timestamp_rounding_used": False,
        "interpolation_used": False,
        "synthetic_bar_used": False,
        "arbitrary_exception_skip_used": False,
        "future_partition_helper_objects":
            "NON_AUTHORITATIVE_HELPER_OUTPUT_NOT_EVIDENCE_OF_PROTECTED_PARTITION_CERTIFICATION",
    }


def _partial_source_record(symbol: str, exc: Exception) -> dict:
    evidence = tuple(getattr(exc, "partial_archive_evidence", ()))
    return {
        "status": "PARTIAL_SOURCE_FAILURE",
        "symbol": symbol,
        "completed_archive_count": len(evidence),
        "archive_evidence": [asdict(value) for value in evidence],
    }


def _sample_record(sample) -> dict:
    return {
        "loaded_rows": len(sample.loaded_timestamps),
        "candidate_rows": sample.candidate_count,
        "accepted_rows": sample.accepted_count,
        "rejected_rows": sample.rejected_count,
        "candidate_equals_accepted_plus_rejected":
            sample.candidate_count == sample.accepted_count + sample.rejected_count,
        "inventory_sha256": dict(sample.inventory_sha256),
        "rejection_reason_counts": rejection_reason_counts(sample),
        "support": support_report(sample),
    }


def _geometry_provenance(sample, numerical: dict | None) -> dict:
    hours = [row.hour for row in sample.rows]
    segments = [row.segment_id for row in sample.rows]
    return {
        "accepted_geometry_row_count": len(sample.rows),
        "hour_vector_sha256": _digest_lines(hours),
        "segment_vector_sha256": _digest_lines(segments),
        "design_shape": None if numerical is None else list(numerical["design"].shape),
    }


def _implementation_blob_evidence(freeze: dict) -> dict:
    expected = freeze["implementation_file_git_blob_sha1"]
    return {
        relative: {
            "expected_git_blob_sha1": blob,
            "observed_git_blob_sha1": _git_blob(relative),
        }
        for relative, blob in expected.items()
    }


def _provisional_execution_provenance(authority: dict) -> dict:
    manifest = authority["manifest"]
    anchor = authority["review_anchor"]
    value = _ambient_execution_context()
    value.update(
        {
            "executing_commit": authority["executing_sha"],
            "implementation_candidate_commit": manifest["implementation_candidate_commit"],
            "independently_reviewed_implementation_commit":
                manifest["reviewed_implementation_commit"],
            "reviewed_commit_equals_candidate":
                manifest["reviewed_implementation_commit"]
                == manifest["implementation_candidate_commit"],
            "review_anchor_ref": anchor["ref"],
            "review_anchor_sha": anchor["sha"],
            "review_anchor_matches_candidate":
                anchor["sha"] == manifest["implementation_candidate_commit"],
            "post_candidate_changed_paths":
                list(authority["post_candidate_changed_paths"]),
        }
    )
    return value


def _execution_provenance(authority: dict, claim: dict) -> dict:
    freeze = authority["freeze"]
    value = _provisional_execution_provenance(authority)
    value.update(
        {
            "release_gate_sha256": _sha256_file(Path(DEFAULT_GATE)),
            "development_execution_manifest_sha256":
                _sha256_file(Path(DEFAULT_EXECUTION_MANIFEST)),
            "development_execution_spec_sha256": _sha256_file(SPEC_PATH),
            "machine_registration_sha256": _sha256_file(REGISTRATION_PATH),
            "implementation_freeze_sha256":
                _sha256_file(Path(DEFAULT_IMPLEMENTATION_FREEZE)),
            "implementation_blob_evidence":
                _implementation_blob_evidence(freeze),
            "runtime": {
                "python": sys.version.split()[0],
                "numpy": np.__version__,
                "scipy": scipy.__version__,
                "dtype": "float64",
                "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS"),
                "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
                "mkl_num_threads": os.environ.get("MKL_NUM_THREADS"),
            },
            "one_shot_claim_ref": claim["ref"],
            "one_shot_claim_sha": claim["sha"],
            "durable_claim_verified_against_github": True,
            "claim_created_before_source_access": True,
            "parent_v1_incident": dict(PARENT_V1),
        }
    )
    return value


def _base_protected_access() -> dict:
    return {
        "market_data_accessed": bool(INCIDENT_STATE["market_data_accessed"]),
        "development_market_outcomes_accessed": bool(
            INCIDENT_STATE["development_market_outcomes_accessed"]
        ),
        "validation_or_oos_accessed": False,
        "strategy_pnl_calculated": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
        "directed_cross_asset_lagged_diagnostics_executed": False,
        "calibration_or_holdout_seed_used": False,
    }


def _failure_result(exc: Exception) -> dict:
    return {
        "classification": "AMS_DEP_DEVELOPMENT_EMPIRICAL_V2_INTEGRITY_FAIL",
        "version": 2,
        "parent_v1_incident": dict(PARENT_V1),
        "failure_stage": INCIDENT_STATE.get("stage"),
        "error": f"{type(exc).__name__}: {exc}",
        "execution_provenance": INCIDENT_STATE.get("execution_provenance"),
        "source_provenance": dict(INCIDENT_STATE.get("source_provenance", {})),
        "sample_provenance": dict(INCIDENT_STATE.get("sample_provenance", {})),
        "numerical_provenance": dict(INCIDENT_STATE.get("numerical_provenance", {})),
        "inference_provenance": dict(INCIDENT_STATE.get("inference_provenance", {})),
        "timestamp_rounding_used": False,
        "interpolation_used": False,
        "synthetic_bar_used": False,
        "arbitrary_exception_skip_used": False,
        "protected_access": _base_protected_access(),
    }


def run() -> dict:
    _reset_incident_state()
    assert_ams_dep_empirical_release_allowed()
    authority = assert_development_execution_allowed()
    INCIDENT_STATE["execution_provenance"] = _provisional_execution_provenance(authority)
    INCIDENT_STATE["stage"] = "DURABLE_V2_CLAIM_VERIFICATION"
    claim = assert_claim_environment(authority["executing_sha"])
    INCIDENT_STATE["execution_provenance"] = _execution_provenance(authority, claim)
    INCIDENT_STATE["stage"] = "POST_V2_CLAIM_PRE_SOURCE"

    source_results = {}
    samples = {}
    support = {}
    numerical = {}

    for symbol in ASSET_ORDER:
        INCIDENT_STATE["stage"] = f"SOURCE_{symbol}"
        try:
            source_results[symbol] = load_development_source(symbol)
        except Exception as exc:
            INCIDENT_STATE["market_data_accessed"] = bool(
                INCIDENT_STATE["market_data_accessed"]
                or getattr(exc, "network_source_access_attempted", False)
            )
            INCIDENT_STATE["source_provenance"][symbol] = _partial_source_record(symbol, exc)
            raise

        INCIDENT_STATE["market_data_accessed"] = True
        INCIDENT_STATE["development_market_outcomes_accessed"] = True
        INCIDENT_STATE["source_provenance"][symbol] = _source_record(source_results[symbol])

        INCIDENT_STATE["stage"] = f"SAMPLE_{symbol}"
        samples[symbol] = build_primary_sample(
            source_results[symbol].bundle,
            registered_identity=source_results[symbol].bundle.manifest.dataset_identity,
        )
        INCIDENT_STATE["sample_provenance"][symbol] = _sample_record(samples[symbol])

        support[symbol] = support_report(samples[symbol])
        INCIDENT_STATE["numerical_provenance"][symbol] = _geometry_provenance(
            samples[symbol], None
        )
        numerical[symbol] = (
            numerical_inputs(samples[symbol]) if support[symbol]["pass"] else None
        )
        INCIDENT_STATE["numerical_provenance"][symbol] = _geometry_provenance(
            samples[symbol], numerical[symbol]
        )

    slot_results = {}
    raw_p_by_slot = {}
    for asset_index, symbol in enumerate(ASSET_ORDER):
        for hypothesis_index, hypothesis in enumerate(HYPOTHESIS_ORDER):
            slot = f"{'BTC' if symbol == 'BTCUSDT' else 'ETH'}_{hypothesis}"
            INCIDENT_STATE["stage"] = f"PRIMARY_INFERENCE_{slot}"
            if not support[symbol]["pass"]:
                result = _unavailable_support_slot()
            else:
                result = _run_slot(
                    numerical[symbol],
                    hypothesis,
                    asset_index,
                    hypothesis_index,
                )
            slot_results[slot] = result
            INCIDENT_STATE["inference_provenance"]["slot_results"][slot] = result
            raw_p_by_slot[slot] = result["raw_p"]

    if tuple(raw_p_by_slot) != SLOTS:
        raise RuntimeError("V2 empirical primary family order changed")

    invalidity_fail = _inference_validity_fail(slot_results)
    holm = None if invalidity_fail else assemble_primary_family(raw_p_by_slot)
    INCIDENT_STATE["inference_provenance"].update(
        {
            "invalidity_fail": invalidity_fail,
            "holm": holm,
            "holm_interpretation_authorized": not invalidity_fail,
        }
    )

    INCIDENT_STATE["stage"] = "CROSS_ASSET_INTERSECTION"
    joined = exact_timestamp_intersection(
        samples["BTCUSDT"],
        samples["ETHUSDT"],
        btc_manifest=source_results["BTCUSDT"].bundle.manifest,
        eth_manifest=source_results["ETHUSDT"].bundle.manifest,
    )

    classification = (
        "EMPIRICAL_INFERENCE_VALIDITY_FAIL"
        if invalidity_fail
        else "AMS_DEP_DEVELOPMENT_EMPIRICAL_V2_EXECUTED"
    )
    INCIDENT_STATE["stage"] = "RESULT_ASSEMBLY"
    return {
        "classification": classification,
        "version": 2,
        "parent_v1_incident": dict(PARENT_V1),
        "execution_provenance": INCIDENT_STATE["execution_provenance"],
        "source_provenance": dict(INCIDENT_STATE["source_provenance"]),
        "sample_provenance": dict(INCIDENT_STATE["sample_provenance"]),
        "inference": {
            "slot_order": list(SLOTS),
            "slot_results": slot_results,
            "holm": holm,
            "holm_interpretation_authorized": not invalidity_fail,
            "invalid_fraction_ceiling": INVALID_FRACTION_CEILING,
            "empirical_bootstrap_root": EMPIRICAL_BOOTSTRAP_ROOT,
            "version_coordinate": 2,
            "dgp_sentinel": EMPIRICAL_SENTINEL,
            "outer_sentinel": EMPIRICAL_SENTINEL,
            "asset_order": list(ASSET_ORDER),
            "hypothesis_order": list(HYPOTHESIS_ORDER),
            "requested_draws": BOOTSTRAP_DRAWS,
            "seed_path_before_segment":
                "[2026092201,2,4294967295,4294967295,asset_index,hypothesis_index,bootstrap_index]",
            "numerical_provenance": dict(INCIDENT_STATE["numerical_provenance"]),
            "engineering_fixture_used_for_empirical_p_value": False,
            "wald_zero_used_for_empirical_p_value": False,
        },
        "cross_asset": {
            "exact_predictor_timestamp_intersection_count": len(joined),
            "exact_predictor_timestamp_intersection_sha256":
                _digest_lines(value.isoformat() for value in joined),
            "directed_cross_asset_lagged_diagnostics":
                "BLOCKED_PENDING_SEPARATE_CROSS_ASSET_LAG_INTEGRITY_SPEC",
            "directed_cross_asset_lagged_diagnostics_executed": False,
        },
        "timestamp_rounding_used": False,
        "interpolation_used": False,
        "synthetic_bar_used": False,
        "arbitrary_exception_skip_used": False,
        "protected_access": _base_protected_access(),
    }


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def main() -> None:
    _reset_incident_state()
    try:
        result = run()
        INCIDENT_STATE["stage"] = "RESULT_ARTIFACT_WRITE"
        _write_json(OUTPUT_PATH, result)
        print(result["classification"])
        if result["classification"] == "EMPIRICAL_INFERENCE_VALIDITY_FAIL":
            raise SystemExit(3)
    except Exception as exc:
        failure = _failure_result(exc)
        try:
            _write_json(OUTPUT_PATH, failure)
        except Exception as result_write_exc:
            failure["result_write_error"] = (
                f"{type(result_write_exc).__name__}: {result_write_exc}"
            )
            _write_json(INCIDENT_PATH, failure)
        print("AMS_DEP_DEVELOPMENT_EMPIRICAL_V2_INTEGRITY_FAIL")
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
