"""First outcome-producing AMS-DEP Development empirical runner V1.

The runner is inert unless both the canonical release gate and the separately
reviewed Development execution manifest are authorized and the durable one-shot
claim has already been created for this exact commit.
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

from research_core.ams_dep_development_execution_lock import (
    DEFAULT_EXECUTION_MANIFEST,
    DEFAULT_IMPLEMENTATION_FREEZE,
    assert_claim_environment,
    assert_development_execution_allowed,
)
from research_core.ams_dep_empirical_access import load_development_source
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
SPEC_PATH = ROOT / "docs/AMS_DEP_DEVELOPMENT_EMPIRICAL_EXECUTION_SPEC_V1.md"
REGISTRATION_PATH = ROOT / "research/governance/ams_dep_development_execution_v1.json"
OUTPUT_PATH = ROOT / "research/experiments/ams_dep_development_empirical_v1/result.json"
EMPIRICAL_BOOTSTRAP_ROOT = 2026092201
EMPIRICAL_SENTINEL = 4294967295
ASSET_ORDER = ("BTCUSDT", "ETHUSDT")
HYPOTHESIS_ORDER = ("DEP", "TIME", "STATE")
INVALID_FRACTION_CEILING = 0.01
ACCESS_STATE = {
    "market_data_accessed": False,
    "development_market_outcomes_accessed": False,
}


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
        fitted, residual = restricted_components(
            design,
            target,
            geometry,
            hypothesis,
        )
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
        "future_partition_helper_objects":
            "NON_AUTHORITATIVE_HELPER_OUTPUT_NOT_EVIDENCE_OF_PROTECTED_PARTITION_CERTIFICATION",
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


def _implementation_blob_evidence(freeze: dict) -> dict:
    expected = freeze["implementation_file_git_blob_sha1"]
    return {
        relative: {
            "expected_git_blob_sha1": blob,
            "observed_git_blob_sha1": _git_blob(relative),
        }
        for relative, blob in expected.items()
    }


def _execution_provenance(authority: dict, claim: dict) -> dict:
    manifest = authority["manifest"]
    freeze = authority["freeze"]
    return {
        "executing_commit": authority["executing_sha"],
        "implementation_candidate_commit":
            manifest["implementation_candidate_commit"],
        "independently_reviewed_implementation_commit":
            manifest["reviewed_implementation_commit"],
        "reviewed_commit_equals_candidate":
            manifest["reviewed_implementation_commit"]
            == manifest["implementation_candidate_commit"],
        "release_gate_sha256": _sha256_file(Path(DEFAULT_GATE)),
        "development_execution_manifest_sha256":
            _sha256_file(Path(DEFAULT_EXECUTION_MANIFEST)),
        "development_execution_spec_sha256": _sha256_file(SPEC_PATH),
        "machine_registration_sha256": _sha256_file(REGISTRATION_PATH),
        "implementation_freeze_sha256":
            _sha256_file(Path(DEFAULT_IMPLEMENTATION_FREEZE)),
        "implementation_blob_evidence":
            _implementation_blob_evidence(freeze),
        "workflow_event": os.environ.get("GITHUB_EVENT_NAME"),
        "workflow_run_id": os.environ.get("GITHUB_RUN_ID"),
        "workflow_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "workflow_job": os.environ.get("GITHUB_JOB"),
        "confirmation_token": "AMS_DEP_DEVELOPMENT_EMPIRICAL_V1",
        "confirmation_verified":
            os.environ.get("AMS_DEP_DEVELOPMENT_CONFIRMATION_VERIFIED") == "true",
        "one_shot_claim_ref": claim["ref"],
        "one_shot_claim_sha": claim["sha"],
        "claim_created_before_source_access": True,
    }


def run() -> dict:
    # Defense in depth. No source adapter is touched before all gates and claim
    # provenance are validated.
    assert_ams_dep_empirical_release_allowed()
    authority = assert_development_execution_allowed()
    claim = assert_claim_environment(authority["executing_sha"])

    source_results = {}
    samples = {}
    support = {}
    numerical = {}

    ACCESS_STATE["market_data_accessed"] = False
    ACCESS_STATE["development_market_outcomes_accessed"] = False
    for symbol in ASSET_ORDER:
        ACCESS_STATE["market_data_accessed"] = True
        source_results[symbol] = load_development_source(symbol)
        ACCESS_STATE["development_market_outcomes_accessed"] = True
        samples[symbol] = build_primary_sample(
            source_results[symbol].bundle,
            registered_identity=
                source_results[symbol].bundle.manifest.dataset_identity,
        )
        support[symbol] = support_report(samples[symbol])
        numerical[symbol] = (
            numerical_inputs(samples[symbol])
            if support[symbol]["pass"]
            else None
        )

    slot_results = {}
    raw_p_by_slot = {}
    for asset_index, symbol in enumerate(ASSET_ORDER):
        for hypothesis_index, hypothesis in enumerate(HYPOTHESIS_ORDER):
            slot = f"{'BTC' if symbol == 'BTCUSDT' else 'ETH'}_{hypothesis}"
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
            raw_p_by_slot[slot] = result["raw_p"]

    if tuple(raw_p_by_slot) != SLOTS:
        raise RuntimeError("empirical primary family order changed")

    invalidity_fail = _inference_validity_fail(slot_results)

    holm = None
    if not invalidity_fail:
        holm = assemble_primary_family(raw_p_by_slot)

    joined = exact_timestamp_intersection(
        samples["BTCUSDT"],
        samples["ETHUSDT"],
        btc_manifest=source_results["BTCUSDT"].bundle.manifest,
        eth_manifest=source_results["ETHUSDT"].bundle.manifest,
    )

    numerical_provenance = {}
    for symbol in ASSET_ORDER:
        values = numerical[symbol]
        numerical_provenance[symbol] = {
            "hour_vector_sha256":
                _digest_lines([] if values is None else values["hours"]),
            "segment_vector_sha256":
                _digest_lines([] if values is None else values["segments"]),
            "design_shape":
                None if values is None else list(values["design"].shape),
        }

    classification = (
        "EMPIRICAL_INFERENCE_VALIDITY_FAIL"
        if invalidity_fail
        else "AMS_DEP_DEVELOPMENT_EMPIRICAL_V1_EXECUTED"
    )

    return {
        "classification": classification,
        "version": 1,
        "execution_provenance": _execution_provenance(authority, claim),
        "source_provenance": {
            symbol: _source_record(source_results[symbol])
            for symbol in ASSET_ORDER
        },
        "sample_provenance": {
            symbol: _sample_record(samples[symbol])
            for symbol in ASSET_ORDER
        },
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
            "numerical_provenance": numerical_provenance,
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
        "protected_access": {
            "market_data_accessed": True,
            "development_market_outcomes_accessed": True,
            "validation_or_oos_accessed": False,
            "strategy_pnl_calculated": False,
            "paper_trading_authorized": False,
            "live_trading_authorized": False,
            "directed_cross_asset_lagged_diagnostics_executed": False,
            "calibration_or_holdout_seed_used": False,
        },
    }


def _write_result(value: dict) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(value, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    try:
        result = run()
        _write_result(result)
        print(result["classification"])
        if result["classification"] == "EMPIRICAL_INFERENCE_VALIDITY_FAIL":
            raise SystemExit(3)
    except Exception as exc:
        failure = {
            "classification": "AMS_DEP_DEVELOPMENT_EMPIRICAL_V1_INTEGRITY_FAIL",
            "version": 1,
            "error": f"{type(exc).__name__}: {exc}",
            "executing_commit": os.environ.get("GITHUB_SHA"),
            "one_shot_claim_ref":
                os.environ.get("AMS_DEP_DEVELOPMENT_CLAIM_REF"),
            "one_shot_claim_sha":
                os.environ.get("AMS_DEP_DEVELOPMENT_CLAIM_SHA"),
            "protected_access": {
                "market_data_accessed": ACCESS_STATE["market_data_accessed"],
                "development_market_outcomes_accessed":
                    ACCESS_STATE["development_market_outcomes_accessed"],
                "validation_or_oos_accessed": False,
                "strategy_pnl_calculated": False,
                "paper_trading_authorized": False,
                "live_trading_authorized": False,
                "directed_cross_asset_lagged_diagnostics_executed": False,
                "calibration_or_holdout_seed_used": False,
            },
        }
        _write_result(failure)
        print("AMS_DEP_DEVELOPMENT_EMPIRICAL_V1_INTEGRITY_FAIL")
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
