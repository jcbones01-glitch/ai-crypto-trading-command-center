"""Metadata-only rehearsal authority checks; no ingestion/runner imports.

Rehearsal requires the same approved execution scope, frozen blobs, runtime,
review and anchor prerequisites as execution. It cannot read source archives.
"""
from __future__ import annotations
import json
from .psr01b_core import PSR01BError
from .psr01b_preflight import (
    ROOT, load_registration, verify_execution_authorization_scope,
    verify_import_closure_blob_metadata, verify_upstream_registration_blob_metadata,
    verify_runtime_versions, verify_thread_environment,
)
from .psr01b_execution_lock import verify_candidate_blob_contract, _git_blob


def load_implementation_freeze():
    freeze = json.loads((ROOT / "research/governance/psr01b_implementation_freeze_v1.json").read_text())
    if freeze.get("freeze_id") != "PSR01B-IMPLEMENTATION-FREEZE-V1":
        raise PSR01BError("unexpected PSR-01B implementation freeze identity")
    return freeze


def verify_frozen_execution_identity(*, runner_label):
    freeze = load_implementation_freeze()
    registration = load_registration()
    expected = {
        "issue": 90,
        "approval_decision": "APPROVE_PSR01B_BOUNDED_SPEC_FOR_IMPLEMENTATION",
        "approval_comment_id": 5821484000,
        "exact_approved_head": "16d5193f0c80b5899f5084e76a42917e824e0936",
        "specification_path": "research/governance/psr01b_bounded_spec_v1.json",
        "specification_git_blob_sha1": "47c5379eeb4eae8c5890814c92e29b86bfddb23e",
        "revision": 4,
    }
    if freeze.get("approved_specification") != expected or _git_blob(expected["specification_path"]) != expected["specification_git_blob_sha1"]:
        raise PSR01BError("approved revision-4 specification identity drift")
    implementation = freeze["implementation"]
    candidate = implementation.get("implementation_candidate_commit")
    if (implementation.get("independent_implementation_reviewed") is not True
            or implementation.get("reviewed_implementation_commit") != candidate):
        raise PSR01BError("independent implementation review is not approved")
    verify_execution_authorization_scope(freeze)
    verify_candidate_blob_contract(candidate, freeze["implementation_file_git_blob_sha1"])
    contract = registration["source"]["row_treatment_contract"]
    expected_upstream = freeze["pinned_upstream_git_blob_sha1"]
    if expected_upstream != contract["required_blob_sha1"]:
        raise PSR01BError("freeze/upstream normalization blob contract mismatch")
    # Hash the exact registered import closure without importing it. The real
    # runner additionally checks imported boundary constants before source access.
    verify_import_closure_blob_metadata(
        {path: _git_blob(path) for path in expected_upstream}, registration,
    )
    verify_upstream_registration_blob_metadata(
        _git_blob(contract["upstream_registration_path"]), registration,
    )
    verify_runtime_versions(runner_label=runner_label)
    verify_thread_environment()
    if freeze["future_governance"].get("reviewed_candidate_anchor_created") is not True:
        raise PSR01BError("reviewed candidate anchor prerequisite not satisfied")
    return {"implementation_candidate_commit": candidate}
