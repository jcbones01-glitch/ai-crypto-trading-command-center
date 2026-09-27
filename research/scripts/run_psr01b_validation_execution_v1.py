#!/usr/bin/env python3
"""Future governed PSR-01B Validation V1 execution/rehearsal wrapper.

No authorization is granted by this file. The frozen governance gates in
psr01b_validation_execution must pass before any protected source request.
"""
from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import sys
import tempfile

from research_core.data_quality import scan_archive
from research_core import psr01b_validation as validation
from research_core import psr01b_validation_execution as control


def _incident(
    *,
    provenance,
    claim,
    stage,
    terminal,
    ledger,
    accepted,
    result_exists,
    error=None,
    source_access=False,
    first_protected=False,
    evidence_gap_status="NONE",
):
    record = validation.build_terminal_incident(
        execution_sha=provenance["executing_sha"],
        reviewed_candidate_sha=provenance["candidate"],
        run_id=claim.run_id,
        run_attempt=claim.run_attempt,
        actor=claim.actor,
        claim_ref=claim.ref,
        claim_tag_object_sha=claim.tag_object_sha,
        claim_target_sha=claim.target_sha,
        stage=stage,
        terminal_classification=terminal.classification,
        validation_result_token=terminal.validation_result_token,
        source_access_occurred=source_access,
        source_acquisition_ledger=ledger,
        source_hashes_obtained_before_failure=accepted,
        result_json_exists=result_exists,
        error_type=None if error is None else type(error).__name__,
        error_message=None if error is None else str(error),
        validation_boundary_status=(
            "PROTECTED_REQUEST_OCCURRED"
            if first_protected
            else "PROTECTED_REQUEST_NOT_REACHED"
        ),
        oos_boundary_status="OOS_NOT_ACCESSED",
        parent_h2_classification=terminal.parent_h2_classification,
        practical_benchmark_token=terminal.practical_benchmark_token,
        first_protected_request_occurred=first_protected,
        protected_validation_interval_consumed=first_protected,
        evidence_gap_status=evidence_gap_status,
    )
    record["attempt_consumed"] = True
    record["recorded_at_utc"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if error is not None and hasattr(error, "incident_evidence"):
        record["normalization_failure_evidence"] = error.incident_evidence()
    return record


def main() -> int:
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    executing_sha = os.environ.get("GITHUB_SHA", "")
    if not repository or not token or not executing_sha:
        raise control.ValidationExecutionControlError(
            "workflow repository/token/SHA provenance is incomplete",
            failure_code="VALIDATION_WORKFLOW_PROVENANCE_INCOMPLETE",
        )

    freeze = control.load_freeze()
    provenance, claim = control.assert_postclaim_environment(
        repository=repository,
        token=token,
        executing_sha=executing_sha,
        runner_label="ubuntu-24.04",
        freeze=freeze,
    )

    if control.execution_mode() == "rehearsal":
        control.write_rehearsal_evidence(claim, provenance)
        print("PSR01B_VALIDATION_REHEARSAL_V1_PRE_SOURCE_PASS")
        return 0

    ledger = []
    accepted = []
    state = {
        "source_access_occurred": False,
        "first_protected_request_occurred": False,
    }
    stage = "POST_CLAIM_PRE_SOURCE"
    result_exists = False
    try:
        with tempfile.TemporaryDirectory(
            prefix="psr01b-validation-v1-",
            dir=os.environ.get("RUNNER_TEMP"),
        ) as temporary:
            stage = "SOURCE_ACQUISITION"
            acquisition = control.acquire_registered_archives(
                claim,
                destination_root=control.RESULT_ROOT,
                opener=control.urlopen,
                ledger=ledger,
                accepted_records=accepted,
                state=state,
            )
            stage = "SCANNER_MANIFEST_NORMALIZATION"
            reports = [
                scan_archive(path, "BTCUSDT", checksum_verified=True)
                for path in acquisition.archive_paths
            ]
            spec = validation.load_validation_spec()
            manifest = validation.build_validation_manifest(reports, spec=spec)
            normalized = validation.normalize_registered_local_archives(
                acquisition.archive_paths,
                reports,
                manifest,
                spec=spec,
            )
            stage = "SCIENTIFIC_EXECUTION"
            result = validation.run_with_operator_log_suppression(
                validation.run_validation_from_normalized_bars,
                normalized.bars,
                spec=spec,
            )
            control.assert_result_finite_and_seeded(result)
            result["provenance"] = {
                **provenance,
                "claim": {
                    "ref": claim.ref,
                    "target_sha": claim.target_sha,
                    "tag_object_sha": claim.tag_object_sha,
                    "run_id": claim.run_id,
                    "run_attempt": claim.run_attempt,
                    "actor": claim.actor,
                },
                "source": {
                    "raw_source_manifest": control.RAW_SOURCE_MANIFEST_PATH.relative_to(control.ROOT).as_posix(),
                    "raw_source_package": control.RAW_SOURCE_PACKAGE_PATH.relative_to(control.ROOT).as_posix(),
                    "accepted_archives": accepted,
                },
            }
            validation.write_json_exclusive(control.RESULT_PATH, result)
            result_exists = True

        if result["parent_h2_classification"] == "BOUNDED_H2_REPLICATION":
            terminal = validation.TerminalDecision(
                "SCIENTIFIC_COMPLETED",
                result["validation_result_token"],
                result["parent_h2_classification"],
                result["practical_benchmark_token"],
            )
        else:
            terminal = validation.TerminalDecision(
                validation.SCIENTIFIC_NON_REPLICATION,
                result["validation_result_token"],
                result["parent_h2_classification"],
                result["practical_benchmark_token"],
            )
        stage = "COMPLETE"
        incident = _incident(
            provenance=provenance,
            claim=claim,
            stage=stage,
            terminal=terminal,
            ledger=ledger,
            accepted=accepted,
            result_exists=True,
            source_access=state["source_access_occurred"],
            first_protected=state["first_protected_request_occurred"],
        )
        validation.write_json_exclusive(control.INCIDENT_PATH, incident)
        print(result["validation_result_token"])
        return 0

    except Exception as exc:
        terminal = validation.classify_exception(exc)
        if terminal.classification == validation.SCIENTIFIC_NON_REPLICATION:
            scientific_result = {
                "registration_id": validation.REGISTRATION_ID,
                "parent_h2_classification": "BOUNDED_H2_NOT_REPLICATED",
                "validation_result_token": validation.VALIDATION_FAIL,
                "practical_benchmark_token": validation.PRACTICAL_FAIL,
                "terminal_reason_code": getattr(exc, "failure_code", type(exc).__name__),
                "provenance": {
                    **provenance,
                    "claim": {
                        "ref": claim.ref,
                        "target_sha": claim.target_sha,
                        "tag_object_sha": claim.tag_object_sha,
                        "run_id": claim.run_id,
                        "run_attempt": claim.run_attempt,
                        "actor": claim.actor,
                    },
                },
            }
            control.assert_result_finite_and_seeded(scientific_result) if "arms" in scientific_result else None
            if not control.RESULT_PATH.exists():
                validation.write_json_exclusive(control.RESULT_PATH, scientific_result)
                result_exists = True
        incident = _incident(
            provenance=provenance,
            claim=claim,
            stage=stage,
            terminal=terminal,
            ledger=ledger,
            accepted=accepted,
            result_exists=result_exists,
            error=exc,
            source_access=state["source_access_occurred"],
            first_protected=state["first_protected_request_occurred"],
        )
        if not control.INCIDENT_PATH.exists():
            validation.write_json_exclusive(control.INCIDENT_PATH, incident)
        if terminal.classification == validation.SCIENTIFIC_NON_REPLICATION:
            print(validation.VALIDATION_FAIL)
            return 0
        raise


if __name__ == "__main__":
    raise SystemExit(main())
