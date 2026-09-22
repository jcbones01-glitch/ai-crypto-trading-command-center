from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/ams-dep-development-empirical-v1.yml"


def test_outcome_workflow_is_manual_only():
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


def test_workflow_has_non_outcome_offline_review_and_explicit_execute_mode():
    text = WORKFLOW.read_text()
    assert "default: offline_review" in text
    assert "- offline_review" in text
    assert "- execute" in text
    assert "if: inputs.mode == 'execute'" in text
    assert "if: inputs.mode == 'offline_review'" in text


def test_execution_has_fixed_confirmation_and_one_shot_concurrency():
    text = WORKFLOW.read_text()
    assert "AMS_DEP_DEVELOPMENT_EMPIRICAL_V1" in text
    assert "group: ams-dep-development-empirical-v1" in text
    assert "cancel-in-progress: false" in text
    assert "contents: write" in text


def test_exact_workflow_test_set_is_state_agnostic_and_authorized_state_aware():
    text = WORKFLOW.read_text()
    assert "tests/test_ams_dep_development_authorized_preflight.py" in text
    assert "tests/test_ams_dep_development_source.py" in text
    assert "tests/test_ams_dep_development_execution_lock.py" in text
    assert "tests/test_ams_dep_development_runner.py" in text
    assert "tests/test_ams_dep_development_workflow.py" in text
    assert "tests/test_ams_dep_release_gate.py" not in text
    assert "tests/test_ams_dep_empirical_firewall.py" not in text


def test_offline_review_cannot_reach_preflight_claim_or_source_job():
    text = WORKFLOW.read_text()
    preflight = text.index("\n  preflight:")
    execute = text.index("\n  execute:")
    assert "if: inputs.mode == 'execute'" in text[preflight:execute]
    assert "if: inputs.mode == 'execute'" in text[execute:]
    assert "Confirm offline-review mode cannot consume claim or source" in text


def test_tests_precede_authority_preflight_claim_and_execution():
    text = WORKFLOW.read_text()
    tests_pos = text.index("Run state-agnostic Development implementation tests")
    preflight_pos = text.index(
        "Verify reviewed anchor, frozen authority, and absence of claim"
    )
    claim_pos = text.index(
        "Atomically create durable Development execution claim"
    )
    execute_job_pos = text.index("\n  execute:")
    runner_pos = text.index("Run first frozen Development empirical execution")
    assert tests_pos < preflight_pos < claim_pos < execute_job_pos < runner_pos
    assert "ams_dep_development_execution_lock preflight" in text
    assert "ams_dep_development_execution_lock claim" in text
    assert "run_ams_dep_development_empirical_v1.py" in text


def test_claim_and_token_are_forwarded_for_durable_reverification():
    text = WORKFLOW.read_text()
    assert "GITHUB_TOKEN: ${{ github.token }}" in text
    assert "AMS_DEP_DEVELOPMENT_CLAIM_REF:" in text
    assert "AMS_DEP_DEVELOPMENT_CLAIM_SHA:" in text
    assert "AMS_DEP_DEVELOPMENT_CONFIRMATION_VERIFIED: 'true'" in text
    assert (
        "Reverify review anchor, execution lock, and durable GitHub claim"
        in text
    )
    assert "assert_claim_environment" in text
    assert "authority['review_anchor']" in text


def test_runtime_is_frozen_and_blas_is_single_threaded():
    text = WORKFLOW.read_text()
    assert "python-version: '3.12.14'" in text
    assert "OPENBLAS_NUM_THREADS: '1'" in text
    assert "OMP_NUM_THREADS: '1'" in text
    assert "MKL_NUM_THREADS: '1'" in text
