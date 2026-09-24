"""Synthetic/offline tests for the frozen PSR-01B XGBoost/Optuna contract."""
import numpy as np
import pytest

import optuna
import xgboost

import research_core.psr01b_model as modelmod
from research_core.psr01b_core import PSR01BError, seed_from_coordinates
from research_core.psr01b_model import (
    ARM_INDEX,
    MODEL_ROOT,
    SUGGESTION_ORDER,
    TRIALS_PER_FOLD,
    ModelSelectionResult,
    TargetScale,
    TrialOutcome,
    apply_target_scale,
    final_refit_and_forecast,
    final_seed,
    fit_target_scale,
    fit_tuning_trial,
    inverse_target_scale,
    optuna_seed,
    suggest_hyperparameters,
    trial_seed,
    tune_fold,
)


def test_pinned_model_library_versions_are_exact():
    assert xgboost.__version__ == "3.4.1"
    assert optuna.__version__ == "5.0.0"


def test_target_standardization_uses_population_std_and_inverse_is_exact():
    y = np.array([1.0, 2.0, 5.0, 8.0])
    scale = fit_target_scale(y)
    assert scale.mean == pytest.approx(np.mean(y))
    assert scale.std == pytest.approx(np.std(y, ddof=0))
    z = apply_target_scale(y, scale)
    np.testing.assert_allclose(inverse_target_scale(z, scale), y, atol=1e-15)
    assert np.mean(z) == pytest.approx(0.0, abs=1e-15)
    assert np.std(z, ddof=0) == pytest.approx(1.0)


def test_zero_target_std_hard_fails():
    with pytest.raises(PSR01BError, match="standard deviation"):
        fit_target_scale([1.0, 1.0, 1.0])


def test_registered_seed_paths_match_seedsequence_coordinates():
    assert optuna_seed("PAPER_FILL", 3) == seed_from_coordinates(
        MODEL_ROOT, 1, ARM_INDEX["PAPER_FILL"], 3
    )
    assert trial_seed("PROJECT_GAP_PRESERVING", 4, 7) == seed_from_coordinates(
        MODEL_ROOT, 2, ARM_INDEX["PROJECT_GAP_PRESERVING"], 4, 7
    )
    assert final_seed("PAPER_FILL", 2, 11) == seed_from_coordinates(
        MODEL_ROOT, 3, ARM_INDEX["PAPER_FILL"], 2, 11
    )


class RecordingTrial:
    def __init__(self):
        self.calls = []

    def suggest_int(self, name, low, high):
        self.calls.append(("int", name, low, high, False))
        return low

    def suggest_float(self, name, low, high, log=False):
        self.calls.append(("float", name, low, high, log))
        return low


def test_optuna_suggestion_call_order_names_and_ranges_are_exact():
    trial = RecordingTrial()
    params = suggest_hyperparameters(trial)
    assert tuple(params) == SUGGESTION_ORDER
    assert [call[1] for call in trial.calls] == list(SUGGESTION_ORDER)
    assert trial.calls == [
        ("int", "max_depth", 2, 4, False),
        ("float", "learning_rate", 0.005, 0.03, True),
        ("int", "n_estimators", 1000, 2500, False),
        ("float", "min_child_weight", 10.0, 40.0, False),
        ("float", "subsample", 0.6, 0.9, False),
        ("float", "colsample_bytree", 0.6, 0.9, False),
        ("float", "reg_alpha", 0.0001, 0.05, True),
        ("float", "reg_lambda", 1.0, 40.0, True),
    ]


def frozen_params(n_estimators=1000):
    return {
        "max_depth": 2,
        "learning_rate": 0.01,
        "n_estimators": n_estimators,
        "min_child_weight": 10.0,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "reg_alpha": 0.001,
        "reg_lambda": 2.0,
    }


class FakeBooster:
    def __init__(self, rounds):
        self.rounds = rounds

    def num_boosted_rounds(self):
        return self.rounds


class FakeTuningRegressor:
    created = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.fit_args = None
        self._rounds = 120
        type(self).created.append(self)

    def fit(self, X, y, eval_set=None, verbose=None):
        self.fit_args = (np.array(X), np.array(y), eval_set, verbose)
        return self

    def evals_result(self):
        # exact tie at iterations 1 and 2 -> smallest iteration 1 must win
        return {"validation_0": {"rmse": [1.0, 0.5, 0.5, 0.7]}}

    def get_booster(self):
        return FakeBooster(self._rounds)

    def predict(self, X, iteration_range=None):
        assert iteration_range == (0, 2)
        return np.zeros(len(X))


def test_tuning_trial_fixed_params_eval_set_tie_rule_and_early_stop(monkeypatch):
    FakeTuningRegressor.created.clear()
    monkeypatch.setattr(modelmod, "XGBRegressor", FakeTuningRegressor)
    Xtr = np.arange(40.0).reshape(20, 2)
    Xva = np.arange(12.0).reshape(6, 2)
    ytr = np.linspace(-1, 1, 20)
    yva = np.linspace(-0.5, 0.5, 6)

    out = fit_tuning_trial(
        X_train=Xtr,
        y_train_standardized=ytr,
        X_validation=Xva,
        y_validation_standardized=yva,
        arm="PAPER_FILL",
        fold_index=2,
        trial_number=7,
        hyperparameters=frozen_params(1000),
    )
    reg = FakeTuningRegressor.created[-1]
    assert reg.kwargs["objective"] == "reg:squarederror"
    assert reg.kwargs["tree_method"] == "hist"
    assert reg.kwargs["n_jobs"] == 1
    assert reg.kwargs["eval_metric"] == "rmse"
    assert reg.kwargs["early_stopping_rounds"] == 50
    assert reg.kwargs["random_state"] == trial_seed("PAPER_FILL", 2, 7)
    assert len(reg.fit_args[2]) == 1
    np.testing.assert_array_equal(reg.fit_args[2][0][0], Xva)
    np.testing.assert_array_equal(reg.fit_args[2][0][1], yva)
    assert out.best_iteration == 1
    assert out.early_stopped
    assert out.final_n_estimators == 2
    assert out.validation_mse == pytest.approx(np.mean(yva ** 2))


def test_no_early_stop_final_estimator_count_is_sampled_count(monkeypatch):
    class NoStop(FakeTuningRegressor):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self._rounds = kwargs["n_estimators"]

    monkeypatch.setattr(modelmod, "XGBRegressor", NoStop)
    out = fit_tuning_trial(
        X_train=np.arange(20.0).reshape(10, 2),
        y_train_standardized=np.linspace(-1, 1, 10),
        X_validation=np.arange(8.0).reshape(4, 2),
        y_validation_standardized=np.linspace(-0.5, 0.5, 4),
        arm="PAPER_FILL",
        fold_index=0,
        trial_number=0,
        hyperparameters=frozen_params(1000),
    )
    assert not out.early_stopped
    assert out.final_n_estimators == 1000


def test_trial_selector_breaks_exact_objective_tie_by_smallest_trial_number():
    outcomes = []
    for i in range(TRIALS_PER_FOLD):
        outcomes.append(
            TrialOutcome(
                i,
                frozen_params(),
                0.1 if i in (3, 7) else 1.0 + i,
                10,
                1000,
                True,
                11,
            )
        )
    selected = modelmod._select_trial(outcomes)
    assert selected.trial_number == 3


def test_tune_fold_executes_exactly_50_sequential_seeded_trials(monkeypatch):
    calls = []

    def fake_fit(**kwargs):
        trial_number = kwargs["trial_number"]
        hp = kwargs["hyperparameters"]
        calls.append(trial_number)
        # deterministic finite objective based on sampled settings
        mse = (
            (float(hp["max_depth"]) - 3.0) ** 2
            + float(hp["learning_rate"])
            + float(hp["reg_alpha"])
            + trial_number * 1e-12
        )
        return TrialOutcome(
            trial_number,
            dict(hp),
            mse,
            4,
            int(hp["n_estimators"]),
            True,
            5,
        )

    monkeypatch.setattr(modelmod, "fit_tuning_trial", fake_fit)
    Xtr = np.arange(80.0).reshape(40, 2)
    Xva = np.arange(24.0).reshape(12, 2)
    ytr = np.linspace(-0.02, 0.03, 40) ** 3 + np.linspace(-0.01, 0.01, 40)
    yva = np.linspace(-0.015, 0.025, 12)

    a = tune_fold(
        X_train=Xtr,
        y_train_raw=ytr,
        X_validation=Xva,
        y_validation_raw=yva,
        arm="PAPER_FILL",
        fold_index=1,
    )
    assert calls == list(range(50))
    assert len(a.trial_outcomes) == 50
    assert a.selected.trial_number in range(50)

    calls.clear()
    b = tune_fold(
        X_train=Xtr,
        y_train_raw=ytr,
        X_validation=Xva,
        y_validation_raw=yva,
        arm="PAPER_FILL",
        fold_index=1,
    )
    assert calls == list(range(50))
    assert a.selected.trial_number == b.selected.trial_number
    assert a.selected.params == b.selected.params


class FakeFinalRegressor:
    created = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.train_y = None
        type(self).created.append(self)

    def fit(self, X, y, verbose=None):
        self.train_y = np.asarray(y, dtype=float)
        self.train_X = np.asarray(X, dtype=float)
        return self

    def predict(self, X):
        # deterministic standardized forecasts
        return np.array([-1.0, 0.0, 1.0], dtype=float)[: len(X)]


def test_final_refit_combines_original_eligible_rows_restandardizes_and_inverts(monkeypatch):
    FakeFinalRegressor.created.clear()
    monkeypatch.setattr(modelmod, "XGBRegressor", FakeFinalRegressor)
    selected = TrialOutcome(
        7,
        frozen_params(),
        0.1,
        12,
        1000,
        True,
        13,
    )
    selection = ModelSelectionResult(
        "PROJECT_GAP_PRESERVING",
        4,
        TargetScale(0.0, 1.0),
        selected,
        tuple([selected] * 50),
    )
    Xtr = np.arange(12.0).reshape(6, 2)
    Xva = np.arange(8.0).reshape(4, 2)
    Xte = np.arange(6.0).reshape(3, 2)
    ytr = np.array([-3, -2, -1, 0, 1, 2], dtype=float)
    yva = np.array([3, 4, 5, 6], dtype=float)

    out = final_refit_and_forecast(
        X_train_eligible=Xtr,
        y_train_raw_eligible=ytr,
        X_validation_eligible=Xva,
        y_validation_raw_eligible=yva,
        X_test=Xte,
        selection=selection,
    )
    reg = FakeFinalRegressor.created[-1]
    assert "early_stopping_rounds" not in reg.kwargs
    assert reg.kwargs["n_estimators"] == 13
    assert reg.kwargs["random_state"] == final_seed(
        "PROJECT_GAP_PRESERVING", 4, 7
    )
    combined = np.r_[ytr, yva]
    mean = np.mean(combined)
    std = np.std(combined, ddof=0)
    np.testing.assert_allclose(reg.train_y, (combined - mean) / std)
    np.testing.assert_allclose(out.forecasts_raw, np.array([-1.0, 0.0, 1.0]) * std + mean)
    assert out.combined_scale.mean == pytest.approx(mean)
    assert out.combined_scale.std == pytest.approx(std)


def test_real_pinned_xgboost_synthetic_smoke():
    # One real-library smoke test verifies the integration surface.  Data are
    # entirely synthetic and tiny; no market observations are used.
    rng = np.random.default_rng(12345)
    Xtr = rng.normal(size=(80, 4))
    beta = np.array([0.3, -0.2, 0.1, 0.05])
    ytr = Xtr @ beta + rng.normal(scale=0.05, size=80)
    Xva = rng.normal(size=(20, 4))
    yva = Xva @ beta + rng.normal(scale=0.05, size=20)

    out = fit_tuning_trial(
        X_train=Xtr,
        y_train_standardized=ytr,
        X_validation=Xva,
        y_validation_standardized=yva,
        arm="PAPER_FILL",
        fold_index=0,
        trial_number=0,
        hyperparameters=frozen_params(1000),
    )
    assert np.isfinite(out.validation_mse)
    assert 0 <= out.best_iteration < 1000
    assert 1 <= out.final_n_estimators <= 1000
