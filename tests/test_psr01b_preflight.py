"""Synthetic/metadata-only tests for PSR-01B preflight."""
from datetime import datetime, timezone
from types import SimpleNamespace
import subprocess

import pytest

from research_core.psr01b_core import PSR01BError
from research_core.psr01b_preflight import (
    EXPECTED_DEVELOPMENT_END,
    EXPECTED_DEVELOPMENT_START,
    EXPECTED_RUNTIME,
    EXPECTED_THREAD_ENV,
    ROOT,
    load_registration,
    verify_archive_digest_metadata,
    verify_archive_inventory,
    verify_development_boundary_constants,
    verify_import_closure_and_development_boundaries,
    verify_import_closure_blob_metadata,
    verify_pre_source_read_contract,
    verify_upstream_registration_blob_metadata,
    verify_runtime_versions,
    verify_thread_environment,
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


def test_registered_thread_environment_is_exact_and_fail_closed():
    assert verify_thread_environment(EXPECTED_THREAD_ENV) == EXPECTED_THREAD_ENV
    broken = dict(EXPECTED_THREAD_ENV)
    broken["OMP_NUM_THREADS"] = "2"
    with pytest.raises(PSR01BError, match="thread environment mismatch"):
        verify_thread_environment(broken)


def test_ci_process_uses_registered_thread_environment():
    assert verify_thread_environment() == EXPECTED_THREAD_ENV


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



def test_development_boundary_constants_match_frozen_inherited_pipeline():
    start, end = verify_development_boundary_constants()
    assert start == EXPECTED_DEVELOPMENT_START
    assert end == EXPECTED_DEVELOPMENT_END


@pytest.mark.parametrize(
    "start,end",
    [
        (datetime(2017, 8, 18, tzinfo=timezone.utc), EXPECTED_DEVELOPMENT_END),
        (EXPECTED_DEVELOPMENT_START, datetime(2022, 1, 2, tzinfo=timezone.utc)),
    ],
)
def test_wrong_development_boundary_constant_hard_fails(start, end):
    fake = SimpleNamespace(DEVELOPMENT_START=start, DEVELOPMENT_END=end)
    with pytest.raises(PSR01BError, match="Development boundary constants"):
        verify_development_boundary_constants(fake)


def test_import_closure_then_boundary_assertion_is_combined_pre_source_gate():
    reg = load_registration()
    expected = reg["source"]["row_treatment_contract"]["required_blob_sha1"]
    observed = {}
    for path in expected:
        observed[path] = subprocess.check_output(
            ["git", "hash-object", "--", path],
            cwd=ROOT,
            text=True,
        ).strip()

    good = SimpleNamespace(
        DEVELOPMENT_START=EXPECTED_DEVELOPMENT_START,
        DEVELOPMENT_END=EXPECTED_DEVELOPMENT_END,
    )
    blobs, boundaries = verify_import_closure_and_development_boundaries(
        observed,
        reg,
        pipeline_module=good,
    )
    assert blobs == expected
    assert boundaries == (EXPECTED_DEVELOPMENT_START, EXPECTED_DEVELOPMENT_END)

    broken_blobs = dict(observed)
    first = next(iter(broken_blobs))
    broken_blobs[first] = "0" * 40
    bad_boundaries = SimpleNamespace(
        DEVELOPMENT_START=datetime(2000, 1, 1, tzinfo=timezone.utc),
        DEVELOPMENT_END=EXPECTED_DEVELOPMENT_END,
    )
    with pytest.raises(PSR01BError, match="pinned import blob mismatch"):
        verify_import_closure_and_development_boundaries(
            broken_blobs,
            reg,
            pipeline_module=bad_boundaries,
        )


def test_upstream_registration_blob_matches_registered_pin():
    reg = load_registration()
    row_contract = reg["source"]["row_treatment_contract"]
    path = row_contract["upstream_registration_path"]
    expected = row_contract["upstream_registration_blob_sha1"]
    observed = subprocess.check_output(
        ["git", "hash-object", "--", path],
        cwd=ROOT,
        text=True,
    ).strip()
    assert observed == expected
    assert verify_upstream_registration_blob_metadata(observed, reg) == expected


def test_upstream_registration_blob_drift_hard_fails():
    reg = load_registration()
    with pytest.raises(PSR01BError, match="upstream registration blob mismatch"):
        verify_upstream_registration_blob_metadata("0" * 40, reg)


def test_complete_pre_source_contract_checks_closure_upstream_then_boundaries():
    reg = load_registration()
    row_contract = reg["source"]["row_treatment_contract"]
    observed = {
        path: subprocess.check_output(
            ["git", "hash-object", "--", path],
            cwd=ROOT,
            text=True,
        ).strip()
        for path in row_contract["required_blob_sha1"]
    }
    upstream = subprocess.check_output(
        ["git", "hash-object", "--", row_contract["upstream_registration_path"]],
        cwd=ROOT,
        text=True,
    ).strip()
    good = SimpleNamespace(
        DEVELOPMENT_START=EXPECTED_DEVELOPMENT_START,
        DEVELOPMENT_END=EXPECTED_DEVELOPMENT_END,
    )
    blobs, verified_upstream, boundaries = verify_pre_source_read_contract(
        observed,
        upstream,
        reg,
        pipeline_module=good,
    )
    assert blobs == row_contract["required_blob_sha1"]
    assert verified_upstream == row_contract["upstream_registration_blob_sha1"]
    assert boundaries == (EXPECTED_DEVELOPMENT_START, EXPECTED_DEVELOPMENT_END)

    bad_boundaries = SimpleNamespace(
        DEVELOPMENT_START=datetime(2000, 1, 1, tzinfo=timezone.utc),
        DEVELOPMENT_END=EXPECTED_DEVELOPMENT_END,
    )
    with pytest.raises(PSR01BError, match="upstream registration blob mismatch"):
        verify_pre_source_read_contract(
            observed,
            "0" * 40,
            reg,
            pipeline_module=bad_boundaries,
        )
