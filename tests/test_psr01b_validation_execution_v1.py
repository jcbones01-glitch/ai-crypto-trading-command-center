from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import math
import os
from pathlib import Path

import numpy as np
import pytest
import yaml

from research_core.data_interfaces import MarketBar
from research_core.psr01b_core import PSR01BError
from research_core import psr01b_egarch
from research_core import psr01b_model
from research_core import psr01b_validation as val
from research_core import psr01b_validation_execution as ctl

UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/psr01b-validation-execution-v1.yml"


def test_execution_workflow_manual_only_and_ordered():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    for forbidden in ("push:", "pull_request:", "schedule:", "repository_dispatch:", "workflow_run:"):
        assert forbidden not in text
    names = [
        "Reserve Validation result path and verify authority before claim",
        "Atomically create durable Validation claim",
        "Reverify durable Validation claim and run registered Validation path",
    ]
    positions = [text.index(name) for name in names]
    assert positions == sorted(positions)
    assert ctl.REAL_CLAIM_REF in text
    assert "contents: write" in text
    assert "--result-path" not in text


def test_result_reservation_canonicalizes_relative_absolute_and_writes_newline_fsync(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    relative = Path("nested/result.json")
    candidate = "a" * 40
    executing = "b" * 40
    record = ctl.reserve_result_path(relative, candidate=candidate, executing_sha=executing)
    absolute = (tmp_path / relative).resolve()
    assert record["result_path"] == str(absolute)
    assert ctl.assert_result_reservation(
        absolute, candidate=candidate, executing_sha=executing
    ) == record
    marker = ctl.reservation_path(absolute)
    assert marker.read_bytes().endswith(b"\n")
    with pytest.raises(val.ValidationContractError):
        val.write_json_exclusive(marker, {"overwrite": True})


def test_complete_import_closure_is_ast_derived_and_contains_control_science_and_source_modules():
    paths = set(ctl.discover_project_import_closure_paths())
    required = {
        "src/research_core/psr01b_validation_execution.py",
        "src/research_core/psr01b_validation.py",
        "src/research_core/psr01b_runner.py",
        "src/research_core/psr01b_execution_lock.py",
        "src/research_core/psr01b_preflight.py",
        "src/research_core/psr01b_core.py",
        "src/research_core/psr01b_model.py",
        "src/research_core/psr01b_egarch.py",
        "src/research_core/psr01b_ta.py",
        "src/research_core/data_ingestion.py",
        "src/research_core/data_quality.py",
        "src/research_core/data_quality_treatment_v2.py",
        "src/research_core/ams_dep_treatment_aware_normalization_v2.py",
        "research/scripts/run_psr01b_validation_execution_v1.py",
    }
    assert required <= paths
    blobs = ctl.project_import_closure_blobs()
    assert set(blobs) == paths
    assert all(len(value) == 40 for value in blobs.values())
    assert ctl.verify_inherited_development_control_pins() == ctl.INHERITED_DEVELOPMENT_CONTROL_PINS


def test_transport_rejects_unverified_and_rehearsal_claim_before_any_opener_call(tmp_path):
    calls = []
    def opener(*args, **kwargs):
        calls.append(args)
        raise AssertionError("transport must not be reached")

    with pytest.raises(ctl.ValidationExecutionControlError, match="verified Validation claim"):
        ctl.acquire_registered_archives(
            object(),
            destination_root=tmp_path,
            opener=opener,
            sleeper=lambda _: None,
        )
    assert calls == []

    rehearsal = ctl.VerifiedClaim(
        ref="refs/tags/psr01b-validation-rehearsal-1-1",
        target_sha="a" * 40,
        tag_object_sha="b" * 40,
        run_id="1",
        run_attempt="1",
        actor="synthetic",
        _marker=ctl._VERIFIED_CLAIM_SENTINEL,
    )
    with pytest.raises(ctl.ValidationExecutionControlError, match="rehearsal"):
        ctl.acquire_registered_archives(
            rehearsal,
            destination_root=tmp_path,
            opener=opener,
            sleeper=lambda _: None,
        )
    assert calls == []


def test_rehearsal_evidence_is_pre_source_and_cannot_use_real_claim(tmp_path, monkeypatch):
    env = {
        "PSR01B_VALIDATION_EXECUTION_MODE": "rehearsal",
        "GITHUB_RUN_ID": "123",
        "GITHUB_RUN_ATTEMPT": "1",
    }
    monkeypatch.setattr(
        ctl,
        "execution_result_path",
        lambda environ=None: tmp_path / "psr01b-validation-rehearsal-123-1" / "result.json",
    )
    claim = ctl.VerifiedClaim(
        ref="refs/tags/psr01b-validation-rehearsal-123-1",
        target_sha="a" * 40,
        tag_object_sha="b" * 40,
        run_id="123",
        run_attempt="1",
        actor="synthetic",
        _marker=ctl._VERIFIED_CLAIM_SENTINEL,
    )
    record = ctl.write_rehearsal_evidence(
        claim,
        {"executing_sha": "a" * 40, "candidate": "c" * 40},
        environ=env,
    )
    assert record["stage"] == "PRE_SOURCE"
    assert record["market_data_accessed"] is False
    assert record["protected_validation_accessed"] is False
    assert record["oos_accessed"] is False
    assert record["real_claim_created"] is False


def test_ta_failure_typing_uses_explicit_sample_state_not_exception_text(monkeypatch):
    monkeypatch.setattr(
        val.parent_runner,
        "select_four_block_features",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            PSR01BError("misleading: no common-four-block eligible candidate")
        ),
    )
    monkeypatch.setattr(val, "_ta_sample_state_unavailable", lambda *args, **kwargs: False)
    with pytest.raises(val.TechnicalIndeterminateError):
        val._select_validation_ta_features(
            object(), object(), train_start=datetime(2021,1,1,tzinfo=UTC),
            train_end=datetime(2022,1,1,tzinfo=UTC)
        )

    monkeypatch.setattr(val, "_ta_sample_state_unavailable", lambda *args, **kwargs: True)
    with pytest.raises(val.SampleScientificUnavailable):
        val._select_validation_ta_features(
            object(), object(), train_start=datetime(2021,1,1,tzinfo=UTC),
            train_end=datetime(2022,1,1,tzinfo=UTC)
        )


def test_egarch_failure_typing_uses_returned_fit_state_not_message(monkeypatch):
    unavailable = psr01b_egarch.EGARCHFit((1,1,1), False, None, None, None, "ABI runtime corruption")
    monkeypatch.setattr(psr01b_egarch, "fit_order", lambda *args, **kwargs: unavailable)
    with pytest.raises(val.EGARCHScientificUnavailable):
        val._select_validation_egarch_fit(([0.1, -0.1, 0.2],))

    monkeypatch.setattr(
        psr01b_egarch,
        "fit_order",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            RuntimeError("all four EGARCH orders unavailable")
        ),
    )
    with pytest.raises(val.TechnicalIndeterminateError):
        val._select_validation_egarch_fit(([0.1, -0.1, 0.2],))


@pytest.mark.skipif(
    os.environ.get("PSR01B_VALIDATION_REAL_LIBRARY_LOG_PROBE") != "1",
    reason="real-library log-suppression probe runs in dedicated CI",
)
def test_operator_log_suppression_through_real_libraries(capsys):
    sentinel = "FORBIDDEN_VALIDATION_OUTCOME_987654321"

    def noisy_real_library_path():
        import optuna
        import xgboost as xgb
        from arch import arch_model
        import statsmodels.api as sm

        study = optuna.create_study(direction="minimize")
        def objective(trial):
            print(sentinel + "_OPTUNA")
            return 1.23456789
        study.optimize(objective, n_trials=1)

        X = np.arange(40, dtype=np.float64).reshape(20, 2)
        y = np.linspace(-1.0, 1.0, 20)
        dtrain = xgb.DMatrix(X, label=y)
        xgb.train(
            {"objective":"reg:squarederror","max_depth":1,"eta":0.1,"seed":1,"nthread":1},
            dtrain,
            num_boost_round=2,
            evals=[(dtrain, sentinel + "_XGB")],
            verbose_eval=True,
        )

        returns = np.sin(np.arange(200) / 7.0) * 0.5
        fit = arch_model(returns, mean="Zero", vol="GARCH", p=1, q=1).fit(
            disp="final", show_warning=False
        )
        print(sentinel + "_ARCH", fit.aic)
        sm_fit = sm.OLS(y, sm.add_constant(X[:, 0])).fit()
        print(sentinel + "_STATSMODELS", sm_fit.rsquared)
        return "done"

    assert val.run_with_operator_log_suppression(noisy_real_library_path) == "done"
    captured = capsys.readouterr()
    assert sentinel not in captured.out
    assert sentinel not in captured.err


def _full_validation_bars():
    start = val.SOURCE_START
    end = val.HARD_END
    gap_start = datetime(2022, 5, 1, tzinfo=UTC)
    gap_end = gap_start + timedelta(hours=2)
    rng = np.random.Generator(np.random.PCG64(2026092502))
    out = []
    previous_close = 10_000.0
    stamp = start
    i = 0
    while stamp < end:
        cyclical = 0.00032 * math.sin(i / 17.0) + 0.00018 * math.cos(i / 73.0)
        close = previous_close * math.exp(cyclical + float(rng.normal(0.0, 0.0022)))
        open_ = previous_close
        high = max(open_, close) * (1.0 + 0.001 + abs(float(rng.normal(0.0, 0.0004))))
        low = min(open_, close) * (1.0 - 0.001 - abs(float(rng.normal(0.0, 0.0004))))
        volume = 100.0 + 10.0 * math.sin(i / 31.0) + abs(float(rng.normal(0.0, 3.0)))
        if not (gap_start <= stamp < gap_end):
            out.append(
                MarketBar(
                    timestamp=stamp,
                    symbol="BTCUSDT",
                    open=Decimal(f"{open_:.12f}"),
                    high=Decimal(f"{high:.12f}"),
                    low=Decimal(f"{low:.12f}"),
                    close=Decimal(f"{close:.12f}"),
                    volume=Decimal(f"{volume:.12f}"),
                )
            )
        previous_close = close
        stamp += timedelta(hours=1)
        i += 1
    return tuple(out)


@pytest.mark.skipif(
    os.environ.get("PSR01B_VALIDATION_FULL_SYNTHETIC_DRY_RUN") != "1",
    reason="full Validation 8x2 dry run executes only in dedicated CI",
)
def test_full_unmocked_validation_8x2_synthetic_dry_run():
    result = val.run_validation_from_normalized_bars(_full_validation_bars())
    assert result["execution_order"]["arms"] == ["PAPER_FILL", "PROJECT_GAP_PRESERVING"]
    assert result["execution_order"]["folds"] == list(range(12, 20))
    assert result["execution_order"]["fold_indices"] == list(range(11, 19))
    assert result["execution_order"]["bootstrap_hours"] == [168, 24, 72]
    for arm in result["execution_order"]["arms"]:
        folds = result["arms"][arm]["folds"]
        assert len(folds) == 8
        for fold in folds:
            expected = psr01b_model.final_seed(
                arm,
                int(fold["fold_index"]),
                int(fold["selected_trial_index"]),
            )
            assert fold["final_model_seed"] == expected
            assert 0 <= fold["selected_trial_index"] < 50
            assert len(fold["selected_features"]) == 10
            assert math.isfinite(float(fold["egarch_aic"]))
    assert ctl.assert_result_finite_and_seeded(result) == {
        "verified_fold_seeds": 16,
        "json_finite": True,
    }
    json.dumps(result, allow_nan=False)
    print("PSR01B_VALIDATION_FULL_8X2_SYNTHETIC_DRY_RUN_PASS")
