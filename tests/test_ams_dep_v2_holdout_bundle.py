import json
from pathlib import Path

import pytest

from research_core.ams_dep_v2_holdout_bundle import (
    HoldoutBundleError,
    REQUIRED_SAFETY_PATHS,
    load_execution_manifest,
)


def test_draft_execution_manifest_is_fail_closed():
    manifest = load_execution_manifest()
    assert manifest["status"] == "DRAFT_LOCKED"
    assert manifest["main_gate_sha256"] is None
    assert manifest["safety_file_git_blob_sha1"] == {}


def test_required_safety_boundary_includes_transitive_main_gate_dependencies():
    assert "src/research_core/release_gate.py" in REQUIRED_SAFETY_PATHS
    assert "tests/test_ams_dep_release_gate.py" in REQUIRED_SAFETY_PATHS
    assert ".github/workflows/ams-dep-v2-frozen-holdout.yml" in REQUIRED_SAFETY_PATHS
    assert "research/scripts/claim_ams_dep_v2_holdout.py" in REQUIRED_SAFETY_PATHS
