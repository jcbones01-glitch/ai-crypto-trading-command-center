from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/ams-dep-development-empirical-v2.yml"


def test_v2_workflow_is_manual_only():
    text = WORKFLOW.read_text()
    assert "workflow_dispatch:" in text
    for forbidden in (
        "pull_request:",
        "push:",
        "schedule:",
        "repository_dispatch:",
        "workflow_run:",
    ):
        assert forbidden not in text


def test_v2_offline_review_is_default_and_execute_is_explicit():
    text = WORKFLOW.read_text()
    assert "default: offline_review" in text
    assert "- offline_review" in text
    assert "- execute" in text
    assert "if: inputs.mode == 'execute'" in text
    assert "if: inputs.mode == 'offline_review'" in text


def test_v2_confirmation_claim_and_concurrency_are_distinct():
    text = WORKFLOW.read_text()
    assert "AMS_DEP_DEVELOPMENT_EMPIRICAL_V2" in text
    assert "group: ams-dep-development-empirical-v2" in text
    assert "cancel-in-progress: false" in text
    assert "contents: write" in text
    assert "ams_dep_development_execution_lock_v2" in text


def test_v2_offline_suite_is_exact_and_state_agnostic():
    text = WORKFLOW.read_text()
    for name in (
        "test_ams_dep_development_v2_authorized_preflight.py",
        "test_ams_dep_development_v2_execution_lock.py",
        "test_ams_dep_development_v2_normalization.py",
        "test_ams_dep_development_v2_source.py",
        "test_ams_dep_development_v2_runner.py",
        "test_ams_dep_development_v2_workflow.py",
    ):
        assert name in text
    assert "tests/test_ams_dep_release_gate.py" not in text
    assert "tests/test_ams_dep_empirical_firewall.py" not in text


def test_v2_tests_precede_preflight_claim_and_runner():
    text = WORKFLOW.read_text()
    tests_pos = text.index("Run state-agnostic Development V2 tests")
    preflight_pos = text.index(
        "Verify V2 reviewed anchor, frozen authority, and absence of V2 claim"
    )
    claim_pos = text.index(
        "Atomically create durable Development V2 execution claim"
    )
    runner_pos = text.index("Run frozen Development empirical V2 execution")
    assert tests_pos < preflight_pos < claim_pos < runner_pos


def test_v2_claim_is_forwarded_and_reverified_before_source():
    text = WORKFLOW.read_text()
    assert "GITHUB_TOKEN: ${{ github.token }}" in text
    assert "AMS_DEP_DEVELOPMENT_V2_CLAIM_REF:" in text
    assert "AMS_DEP_DEVELOPMENT_V2_CLAIM_SHA:" in text
    assert "AMS_DEP_DEVELOPMENT_V2_CONFIRMATION_VERIFIED: 'true'" in text
    assert "assert_claim_environment" in text
    assert "assert_development_execution_allowed" in text


def test_v2_runtime_is_frozen_and_single_threaded():
    text = WORKFLOW.read_text()
    assert "python-version: '3.12.14'" in text
    assert "OPENBLAS_NUM_THREADS: '1'" in text
    assert "OMP_NUM_THREADS: '1'" in text
    assert "MKL_NUM_THREADS: '1'" in text
