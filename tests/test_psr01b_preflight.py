"""Synthetic/metadata-only tests for PSR-01B preflight."""
from datetime import datetime, timezone
import subprocess

import pytest

from research_core.psr01b_core import PSR01BError
from research_core.psr01b_preflight import (
    EXPECTED_RUNTIME,
    ROOT,
    load_registration,
    verify_archive_digest_metadata,
    verify_archive_inventory,
    verify_import_closure_blob_metadata,
    verify_runtime_versions,
    verify_timestamp_boundary_metadata,
)


def test_registration_identity_revision_runtime_and_49_archive_inventory_are_frozen():
    reg = load_registration()
    expected = reg["source"]["archive_sha256"]
    assert len(expected) == 49
    observed = verify_archive_inventory(list(reversed(expected)), reg)
    assert observed == tuple(sorted(expected))


def test_archive_inventory_rejects_missing_extra_and_duplicate_names():
    reg = load_registration()
    names = list(reg["source"]["archive_sha256"])
    with pytest.raises(PSR01BError, match="inventory mismatch"):
        verify_archive_inventory(names[:-1], reg)
    with pytest.raises(PSR01BError):
        verify_archive_inventory(names + [names[0]], reg)


def test_archive_digest_metadata_requires_exact_registered_map_without_opening_bytes():
    reg = load_registration()
    expected = dict(reg["source"]["archive_sha256"])
    assert verify_archive_digest_metadata(expected, reg) == expected
    broken = dict(expected)
    first = next(iter(broken))
    broken[first] = "0" * 64
    with pytest.raises(PSR01BError, match="SHA-256 mismatch"):
        verify_archive_digest_metadata(broken, reg)


def test_pinned_normalization_import_closure_matches_current_git_blobs():
    reg = load_registration()
    expected = reg["source"]["row_treatment_contract"]["required_blob_sha1"]
    observed = {}
    for path in expected:
        observed[path] = subprocess.check_output(
            ["git", "hash-object", "--", path],
            cwd=ROOT,
            text=True,
        ).strip()
    assert observed == expected
    assert verify_import_closure_blob_metadata(observed, reg) == expected


def test_import_closure_fails_on_any_blob_or_path_drift():
    reg = load_registration()
    expected = dict(reg["source"]["row_treatment_contract"]["required_blob_sha1"])
    first = next(iter(expected))
    bad = dict(expected)
    bad[first] = "0" * 40
    with pytest.raises(PSR01BError, match="pinned import blob mismatch"):
        verify_import_closure_blob_metadata(bad, reg)
    missing = dict(expected)
    missing.pop(first)
    with pytest.raises(PSR01BError, match="path set mismatch"):
        verify_import_closure_blob_metadata(missing, reg)


def test_exact_pinned_runtime_versions_are_installed_on_registered_runner():
    observed = verify_runtime_versions(runner_label="ubuntu-24.04")
    assert observed == EXPECTED_RUNTIME


def test_timestamp_boundary_fixture_rejects_post_2022_and_non_hour_rows():
    reg = load_registration()
    good = [
        int(datetime(2017, 12, 1, tzinfo=timezone.utc).timestamp()),
        int(datetime(2021, 12, 31, 23, tzinfo=timezone.utc).timestamp()),
    ]
    verify_timestamp_boundary_metadata(good, reg)

    with pytest.raises(PSR01BError, match="outside registered source boundary"):
        verify_timestamp_boundary_metadata(
            [int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp())],
            reg,
        )
    with pytest.raises(PSR01BError, match="exact UTC hour"):
        verify_timestamp_boundary_metadata(
            [int(datetime(2021, 1, 1, 0, 30, tzinfo=timezone.utc).timestamp())],
            reg,
        )
