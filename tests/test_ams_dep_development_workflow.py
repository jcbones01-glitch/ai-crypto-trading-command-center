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


def test_workflow_has_fixed_confirmation_and_one_shot_concurrency():
    text = WORKFLOW.read_text()
    assert "AMS_DEP_DEVELOPMENT_EMPIRICAL_V1" in text
    assert "group: ams-dep-development-empirical-v1" in text
    assert "cancel-in-progress: false" in text
    assert "contents: write" in text


def test_offline_tests_and_preflight_precede_atomic_claim_and_execution():
    text = WORKFLOW.read_text()
    tests_pos = text.index("Run offline Development implementation/firewall tests")
    preflight_pos = text.index("Verify frozen execution authority and absence of claim")
    claim_pos = text.index("Atomically create durable Development execution claim")
    execute_job_pos = text.index("\n  execute:")
    runner_pos = text.index("Run first frozen Development empirical execution")
    assert tests_pos < preflight_pos < claim_pos < execute_job_pos < runner_pos
    assert "ams_dep_development_execution_lock preflight" in text
    assert "ams_dep_development_execution_lock claim" in text
    assert "run_ams_dep_development_empirical_v1.py" in text


def test_claim_is_forwarded_to_execution_job_before_source_runner():
    text = WORKFLOW.read_text()
    assert "AMS_DEP_DEVELOPMENT_CLAIM_REF:" in text
    assert "AMS_DEP_DEVELOPMENT_CLAIM_SHA:" in text
    assert "AMS_DEP_DEVELOPMENT_CONFIRMATION_VERIFIED: 'true'" in text
    assert "Reverify execution lock and durable claim before source access" in text


def test_runtime_is_frozen_and_blas_is_single_threaded():
    text = WORKFLOW.read_text()
    assert "python-version: '3.12.14'" in text
    assert "OPENBLAS_NUM_THREADS: '1'" in text
    assert "OMP_NUM_THREADS: '1'" in text
    assert "MKL_NUM_THREADS: '1'" in text
