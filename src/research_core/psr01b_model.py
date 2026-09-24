"""PSR-01B frozen XGBoost + Optuna model-selection contract.

This module is source-agnostic and intended for synthetic/offline validation before
any empirical authorization.  It contains no archive readers or protected-data I/O.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np
import optuna
import xgboost as xgb

from .psr01b_core import PSR01BError, seed_from_coordinates


MODEL_ROOT = 2026092401
ARM_INDEX = {"PAPER_FILL": 0, "PROJECT_GAP_PRESERVING": 1}
TRIALS_PER_FOLD = 50
EARLY_STOPPING_ROUNDS = 50
SUGGESTION_ORDER = (
    "max_depth",
    "learning_rate",
    "n_estimators",
    "min_child_weight",
    "subsample",
    "colsample_bytree",
    "reg_alpha",
    "reg_lambda",
)


@dataclass(frozen=True)
class TargetScale:
    mean: float
    std: float


@dataclass(frozen=True)
class TrialOutcome:
    trial_number: int
    params: dict[str, float | int]
    validation_mse: float
    best_iteration: int
    sampled_n_estimators: int
    early_stopped: bool
    final_n_estimators: int


@dataclass(frozen=True)
class ModelSelectionResult:
    arm: str
    fold_index: int
    training_scale: TargetScale
    selected: TrialOutcome
    trial_outcomes: tuple[TrialOutcome, ...]


@dataclass(frozen=True)
class FinalForecastResult:
    forecasts_raw: np.ndarray
    combined_scale: TargetScale
    n_estimators: int
    random_state: int


def _finite_matrix(values: Sequence[Sequence[float]], name: str) -> np.ndarray:
    out = np.asarray(values, dtype=np.float64)
    if out.ndim != 2 or out.shape[0] == 0 or out.shape[1] == 0:
        raise PSR01BError(f"{name} must be a non-empty 2-D matrix")
    if not np.isfinite(out).all():
        raise PSR01BError(f"{name} must be finite")
    return out


def _finite_vector(values: Sequence[float], name: str) -> np.ndarray:
    out = np.asarray(values, dtype=np.float64)
    if out.ndim != 1 or len(out) == 0:
        raise PSR01BError(f"{name} must be a non-empty 1-D vector")
    if not np.isfinite(out).all():
        raise PSR01BError(f"{name} must be finite")
    return out


def fit_target_scale(values: Sequence[float]) -> TargetScale:
    y = _finite_vector(values, "target")
    mean = float(np.mean(y))
    std = float(np.std(y, ddof=0))
    if not np.isfinite(mean) or not np.isfinite(std) or std <= 0.0:
        raise PSR01BError("target standard deviation must be positive and finite")
    return TargetScale(mean, std)


def apply_target_scale(values: Sequence[float], scale: TargetScale) -> np.ndarray:
    y = _finite_vector(values, "target")
    if not np.isfinite(scale.mean) or not np.isfinite(scale.std) or scale.std <= 0.0:
        raise PSR01BError("invalid target scale")
    out = (y - scale.mean) / scale.std
    if not np.isfinite(out).all():
        raise PSR01BError("nonfinite standardized target")
    return out


def inverse_target_scale(values: Sequence[float], scale: TargetScale) -> np.ndarray:
    y = _finite_vector(values, "standardized forecast")
    out = y * scale.std + scale.mean
    if not np.isfinite(out).all():
        raise PSR01BError("nonfinite inverse-transformed forecast")
    return out


def optuna_seed(arm: str, fold_index: int) -> int:
    if arm not in ARM_INDEX:
        raise PSR01BError("unregistered arm")
    if not isinstance(fold_index, int) or isinstance(fold_index, bool) or fold_index < 0:
        raise PSR01BError("fold_index must be a nonnegative integer")
    return seed_from_coordinates(MODEL_ROOT, 1, ARM_INDEX[arm], fold_index)


def trial_seed(arm: str, fold_index: int, trial_index: int) -> int:
    if arm not in ARM_INDEX:
        raise PSR01BError("unregistered arm")
    if any(
        not isinstance(v, int) or isinstance(v, bool) or v < 0
        for v in (fold_index, trial_index)
    ):
        raise PSR01BError("fold/trial indices must be nonnegative integers")
    return seed_from_coordinates(
        MODEL_ROOT, 2, ARM_INDEX[arm], fold_index, trial_index
    )


def final_seed(arm: str, fold_index: int, selected_trial_index: int) -> int:
    if arm not in ARM_INDEX:
        raise PSR01BError("unregistered arm")
    if any(
        not isinstance(v, int) or isinstance(v, bool) or v < 0
        for v in (fold_index, selected_trial_index)
    ):
        raise PSR01BError("fold/trial indices must be nonnegative integers")
    return seed_from_coordinates(
        MODEL_ROOT, 3, ARM_INDEX[arm], fold_index, selected_trial_index
    )


def suggest_hyperparameters(trial) -> dict[str, float | int]:
    """Issue Optuna suggestions in the exact frozen call/name order."""
    return {
        "max_depth": trial.suggest_int("max_depth", 2, 4),
        "learning_rate": trial.suggest_float(
            "learning_rate", 0.005, 0.03, log=True
        ),
        "n_estimators": trial.suggest_int("n_estimators", 1000, 2500),
        "min_child_weight": trial.suggest_float(
            "min_child_weight", 10.0, 40.0
        ),
        "subsample": trial.suggest_float("subsample", 0.6, 0.9),
        "colsample_bytree": trial.suggest_float(
            "colsample_bytree", 0.6, 0.9
        ),
        "reg_alpha": trial.suggest_float(
            "reg_alpha", 0.0001, 0.05, log=True
        ),
        "reg_lambda": trial.suggest_float(
            "reg_lambda", 1.0, 40.0, log=True
        ),
    }


def _xgb_params(
    hyperparameters: Mapping[str, float | int],
    *,
    random_state: int,
    n_estimators_override: int | None = None,
) -> tuple[dict[str, float | int | str], int]:
    required = set(SUGGESTION_ORDER)
    if set(hyperparameters) != required:
        raise PSR01BError("hyperparameter mapping must match frozen search fields exactly")
    n_estimators = (
        int(n_estimators_override)
        if n_estimators_override is not None
        else int(hyperparameters["n_estimators"])
    )
    if n_estimators <= 0:
        raise PSR01BError("n_estimators must be positive")
    # The frozen contract names sklearn-style controls n_jobs/random_state.
    # Native XGBoost uses their engine equivalents nthread/seed.  This keeps
    # the exact single-thread and registered SeedSequence value without adding
    # an unregistered scikit-learn runtime dependency.
    params: dict[str, float | int | str] = {
        "objective": "reg:squarederror",
        "tree_method": "hist",
        "nthread": 1,
        "seed": int(random_state),
        "eval_metric": "rmse",
        "max_depth": int(hyperparameters["max_depth"]),
        "learning_rate": float(hyperparameters["learning_rate"]),
        "n_estimators": n_estimators,
        "min_child_weight": float(hyperparameters["min_child_weight"]),
        "subsample": float(hyperparameters["subsample"]),
        "colsample_bytree": float(hyperparameters["colsample_bytree"]),
        "reg_alpha": float(hyperparameters["reg_alpha"]),
        "reg_lambda": float(hyperparameters["reg_lambda"]),
    }
    return params, n_estimators


def _smallest_min_rmse_iteration(result: Mapping[str, Mapping[str, Sequence[float]]]) -> int:
    try:
        history = np.asarray(result["validation_0"]["rmse"], dtype=np.float64)
    except Exception as exc:
        raise PSR01BError("missing validation rmse history") from exc
    if history.ndim != 1 or len(history) == 0 or not np.isfinite(history).all():
        raise PSR01BError("invalid validation rmse history")
    minimum = float(np.min(history))
    matches = np.flatnonzero(history == minimum)
    if len(matches) == 0:
        raise PSR01BError("validation rmse minimum not found")
    return int(matches[0])


def fit_tuning_trial(
    *,
    X_train: Sequence[Sequence[float]],
    y_train_standardized: Sequence[float],
    X_validation: Sequence[Sequence[float]],
    y_validation_standardized: Sequence[float],
    arm: str,
    fold_index: int,
    trial_number: int,
    hyperparameters: Mapping[str, float | int],
) -> TrialOutcome:
    Xtr = _finite_matrix(X_train, "X_train")
    Xva = _finite_matrix(X_validation, "X_validation")
    ytr = _finite_vector(y_train_standardized, "y_train_standardized")
    yva = _finite_vector(y_validation_standardized, "y_validation_standardized")
    if len(Xtr) != len(ytr) or len(Xva) != len(yva):
        raise PSR01BError("feature/target row mismatch")
    if Xtr.shape[1] != Xva.shape[1]:
        raise PSR01BError("train/validation feature-width mismatch")

    seed = trial_seed(arm, fold_index, trial_number)
    params, sampled_n_estimators = _xgb_params(
        hyperparameters,
        random_state=seed,
    )
    dtrain = xgb.DMatrix(Xtr, label=ytr)
    dvalidation = xgb.DMatrix(Xva, label=yva)
    evals_result: dict[str, dict[str, list[float]]] = {}
    booster = xgb.train(
        params,
        dtrain,
        num_boost_round=sampled_n_estimators,
        evals=[(dvalidation, "validation_0")],
        evals_result=evals_result,
        early_stopping_rounds=EARLY_STOPPING_ROUNDS,
        verbose_eval=False,
    )

    best_iteration = _smallest_min_rmse_iteration(evals_result)
    boosted_rounds = int(booster.num_boosted_rounds())
    early_stopped = boosted_rounds < sampled_n_estimators
    final_n_estimators = (
        best_iteration + 1 if early_stopped else sampled_n_estimators
    )

    pred = np.asarray(
        booster.predict(dvalidation, iteration_range=(0, best_iteration + 1)),
        dtype=np.float64,
    )
    if pred.shape != yva.shape or not np.isfinite(pred).all():
        raise PSR01BError("invalid validation prediction")
    mse = float(np.mean((pred - yva) ** 2))
    if not np.isfinite(mse):
        raise PSR01BError("nonfinite validation MSE")

    return TrialOutcome(
        int(trial_number),
        {name: hyperparameters[name] for name in SUGGESTION_ORDER},
        mse,
        best_iteration,
        sampled_n_estimators,
        bool(early_stopped),
        int(final_n_estimators),
    )


def _select_trial(outcomes: Sequence[TrialOutcome]) -> TrialOutcome:
    if len(outcomes) != TRIALS_PER_FOLD:
        raise PSR01BError("exactly 50 trial outcomes are required")
    if any(not np.isfinite(o.validation_mse) for o in outcomes):
        raise PSR01BError("all trial validation MSE values must be finite")
    return min(outcomes, key=lambda o: (o.validation_mse, o.trial_number))


def tune_fold(
    *,
    X_train: Sequence[Sequence[float]],
    y_train_raw: Sequence[float],
    X_validation: Sequence[Sequence[float]],
    y_validation_raw: Sequence[float],
    arm: str,
    fold_index: int,
) -> ModelSelectionResult:
    Xtr = _finite_matrix(X_train, "X_train")
    Xva = _finite_matrix(X_validation, "X_validation")
    ytr_raw = _finite_vector(y_train_raw, "y_train_raw")
    yva_raw = _finite_vector(y_validation_raw, "y_validation_raw")
    if len(Xtr) != len(ytr_raw) or len(Xva) != len(yva_raw):
        raise PSR01BError("feature/target row mismatch")
    if Xtr.shape[1] != Xva.shape[1]:
        raise PSR01BError("train/validation feature-width mismatch")

    scale = fit_target_scale(ytr_raw)
    ytr = apply_target_scale(ytr_raw, scale)
    yva = apply_target_scale(yva_raw, scale)

    sampler = optuna.samplers.TPESampler(
        seed=optuna_seed(arm, fold_index),
        multivariate=False,
        group=False,
        constant_liar=False,
    )
    study = optuna.create_study(
        direction="minimize",
        sampler=sampler,
        pruner=optuna.pruners.NopPruner(),
    )
    outcomes: list[TrialOutcome] = []

    def objective(trial):
        hyperparameters = suggest_hyperparameters(trial)
        outcome = fit_tuning_trial(
            X_train=Xtr,
            y_train_standardized=ytr,
            X_validation=Xva,
            y_validation_standardized=yva,
            arm=arm,
            fold_index=fold_index,
            trial_number=int(trial.number),
            hyperparameters=hyperparameters,
        )
        outcomes.append(outcome)
        return outcome.validation_mse

    study.optimize(objective, n_trials=TRIALS_PER_FOLD, n_jobs=1)
    if len(outcomes) != TRIALS_PER_FOLD:
        raise PSR01BError("Optuna did not produce exactly 50 completed outcomes")
    selected = _select_trial(outcomes)
    return ModelSelectionResult(
        arm,
        int(fold_index),
        scale,
        selected,
        tuple(sorted(outcomes, key=lambda o: o.trial_number)),
    )


def final_refit_and_forecast(
    *,
    X_train_eligible: Sequence[Sequence[float]],
    y_train_raw_eligible: Sequence[float],
    X_validation_eligible: Sequence[Sequence[float]],
    y_validation_raw_eligible: Sequence[float],
    X_test: Sequence[Sequence[float]],
    selection: ModelSelectionResult,
) -> FinalForecastResult:
    Xtr = _finite_matrix(X_train_eligible, "X_train_eligible")
    Xva = _finite_matrix(X_validation_eligible, "X_validation_eligible")
    Xte = _finite_matrix(X_test, "X_test")
    ytr = _finite_vector(y_train_raw_eligible, "y_train_raw_eligible")
    yva = _finite_vector(y_validation_raw_eligible, "y_validation_raw_eligible")
    if len(Xtr) != len(ytr) or len(Xva) != len(yva):
        raise PSR01BError("final-refit feature/target row mismatch")
    if Xtr.shape[1] != Xva.shape[1] or Xtr.shape[1] != Xte.shape[1]:
        raise PSR01BError("final-refit feature-width mismatch")

    X_combined = np.vstack((Xtr, Xva))
    y_combined_raw = np.concatenate((ytr, yva))
    combined_scale = fit_target_scale(y_combined_raw)
    y_combined = apply_target_scale(y_combined_raw, combined_scale)

    selected = selection.selected
    seed = final_seed(
        selection.arm,
        selection.fold_index,
        selected.trial_number,
    )
    params, final_rounds = _xgb_params(
        selected.params,
        random_state=seed,
        n_estimators_override=selected.final_n_estimators,
    )
    dcombined = xgb.DMatrix(X_combined, label=y_combined)
    dtest = xgb.DMatrix(Xte)
    booster = xgb.train(
        params,
        dcombined,
        num_boost_round=final_rounds,
        evals=[],
        verbose_eval=False,
    )

    standardized = np.asarray(booster.predict(dtest), dtype=np.float64)
    if standardized.ndim != 1 or len(standardized) != len(Xte):
        raise PSR01BError("invalid final forecast shape")
    forecasts_raw = inverse_target_scale(standardized, combined_scale)
    return FinalForecastResult(
        forecasts_raw,
        combined_scale,
        int(selected.final_n_estimators),
        int(seed),
    )
