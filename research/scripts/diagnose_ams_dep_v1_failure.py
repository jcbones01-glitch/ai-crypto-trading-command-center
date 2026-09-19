"""Synthetic-only diagnosis of AMS-DEP V1 false-rejection inflation.

This is not a V2 inference method and cannot access market data.
See docs/AMS_DEP_V1_FAILURE_DIAGNOSTIC_PLAN.md.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import platform
import runpy
import subprocess
from pathlib import Path

for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

import numpy as np
import scipy
from scipy.stats import chi2

from research_core.dependence_statistics import (
    InferenceError,
    RESTRICTIONS,
    holm_six,
    ols_hac,
    primary_design,
    wald_zero,
)

ROOT = Path(__file__).resolve().parents[2]
PLAN = Path("docs/AMS_DEP_V1_FAILURE_DIAGNOSTIC_PLAN.md")
DIAG_CONFIG = Path("research/experiments/ams_dep_v1_failure_diagnostic_v1.json")
V1_CONFIG = Path("research/experiments/ams_dep_synthetic_core_v1.json")
V1_RUNNER = Path("research/scripts/run_ams_dep_synthetic_core_v1.py")
STATS_SOURCE = Path("src/research_core/dependence_statistics.py")
SPEC_COMMIT = "e490b1fb5a8da8cbfaaceebf96ea1979896932a7"
SLOPE_NAMES = (
    "x",
    "x_year_2018",
    "x_year_2019",
    "x_year_2020",
    "x_year_2021",
    "x_vol_low",
    "x_vol_high",
)
TEST_NAMES = ("DEP", "TIME", "STATE")
SLOT_NAMES = ("BTC_DEP", "BTC_TIME", "BTC_STATE", "ETH_DEP", "ETH_TIME", "ETH_STATE")


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def provenance() -> dict:
    executing = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    subprocess.run(
        ["git", "diff", "--exit-code", "HEAD", "--"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    for path in (PLAN, DIAG_CONFIG):
        frozen = subprocess.check_output(["git", "show", f"{SPEC_COMMIT}:{path.as_posix()}"], cwd=ROOT)
        if frozen != (ROOT / path).read_bytes():
            raise RuntimeError(f"diagnostic specification changed: {path}")
    sources = (Path(__file__).relative_to(ROOT), PLAN, DIAG_CONFIG, V1_CONFIG, V1_RUNNER, STATS_SOURCE)
    for path in sources:
        committed = subprocess.check_output(["git", "show", f"{executing}:{path.as_posix()}"], cwd=ROOT)
        if committed != (ROOT / path).read_bytes():
            raise RuntimeError(f"uncommitted diagnostic source: {path}")
    if np.__version__ != "2.2.6" or scipy.__version__ != "1.15.3":
        raise RuntimeError("unregistered numerical dependency versions")
    return {
        "executing_commit": executing,
        "diagnostic_specification_commit": SPEC_COMMIT,
        "file_sha256": {str(path): sha256((ROOT / path).read_bytes()) for path in sources},
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "platform": platform.platform(),
        "blas_threads": 1,
    }


def direct_bartlett_meat(scores: np.ndarray, hours: np.ndarray, segments: np.ndarray, lag: int) -> np.ndarray:
    """Independent direct lag-sum oracle for contiguous declared segments."""
    scores = np.asarray(scores, dtype=np.float64)
    hours = np.asarray(hours, dtype=np.int64)
    segments = np.asarray(segments, dtype=np.int64)
    p = scores.shape[1]
    meat = np.zeros((p, p), dtype=np.float64)
    labels = []
    boundaries = np.r_[0, np.flatnonzero(segments[1:] != segments[:-1]) + 1, len(scores)]
    for start, end in zip(boundaries[:-1], boundaries[1:]):
        label = int(segments[start])
        if label in labels:
            raise RuntimeError("oracle segment labels recur")
        labels.append(label)
        g = scores[start:end]
        h = hours[start:end]
        if len(h) > 1 and np.any(np.diff(h) != 1):
            raise RuntimeError("oracle requires contiguous synthetic segment")
        meat += g.T @ g
        for ell in range(1, lag + 1):
            if ell >= len(g):
                break
            weight = 1.0 - ell / (lag + 1.0)
            cross = g[ell:].T @ g[:-ell]
            meat += weight * (cross + cross.T)
    return (meat + meat.T) / 2.0


def oracle_fit(design: np.ndarray, target: np.ndarray, hours: np.ndarray, segments: np.ndarray, lag: int):
    """Unscaled normal-equation OLS plus direct Bartlett HAC."""
    x = np.asarray(design, dtype=np.float64)
    y = np.asarray(target, dtype=np.float64)
    n, p = x.shape
    xtx = x.T @ x
    beta = np.linalg.solve(xtx, x.T @ y)
    residual = y - x @ beta
    scores = x * residual[:, None]
    meat = direct_bartlett_meat(scores, hours, segments, lag)
    bread = np.linalg.inv(xtx)
    cov = (bread @ meat @ bread) * n / (n - p)
    return beta, (cov + cov.T) / 2.0


def quantile_record(values: list[float], df: int) -> dict:
    arr = np.asarray(values, dtype=np.float64)
    qs = np.quantile(arr, [0.50, 0.90, 0.95, 0.99], method="linear")
    theory95 = float(chi2.ppf(0.95, df))
    return {
        "n": int(len(arr)),
        "empirical_q50": float(qs[0]),
        "empirical_q90": float(qs[1]),
        "empirical_q95": float(qs[2]),
        "empirical_q99": float(qs[3]),
        "chi_square_df": int(df),
        "theoretical_q95": theory95,
        "empirical_to_theoretical_q95_ratio": float(qs[2] / theory95),
    }


def rate(count: int, denominator: int) -> dict:
    return {"count": int(count), "denominator": int(denominator), "rate": float(count / denominator)}


def main() -> None:
    meta = provenance()
    diag = json.loads((ROOT / DIAG_CONFIG).read_text())
    v1 = json.loads((ROOT / V1_CONFIG).read_text())
    if diag["replications"] != v1["replications"]:
        raise RuntimeError("diagnostic must retain V1 replication count")
    runner = runpy.run_path(str(ROOT / V1_RUNNER))
    years, states, hours, segments = runner["calendar"](v1)

    oracle_checks = []
    summaries = {}
    ledger = []

    for case in diag["cases"]:
        summaries[case] = {}
        by_lag = {}
        for lag in diag["hac_lags"]:
            by_lag[lag] = {
                "family_reject": 0,
                "adjusted_reject": np.zeros(6, dtype=int),
                "raw_reject": np.zeros(6, dtype=int),
                "invalid": 0,
                "wald": [[] for _ in range(6)],
                "coef": [[[] for _ in range(7)] for _ in range(2)],
                "est_var": [[[] for _ in range(7)] for _ in range(2)],
            }

        for replication in range(diag["replications"]):
            x_returns, y_returns = runner["simulate"](case, replication, v1)
            design = primary_design(x_returns[:, 0], years, states)
            # Both assets have the same categorical design, but x differs by asset.
            for lag in diag["hac_lags"]:
                raw_ps = []
                raw_stats = []
                fits = []
                errors = []
                for asset in range(2):
                    try:
                        asset_design = primary_design(x_returns[:, asset], years, states)
                        fit = ols_hac(
                            asset_design,
                            y_returns[:, asset],
                            hours,
                            segments,
                            max_lag=lag,
                        )
                        tests = [wald_zero(fit, RESTRICTIONS[name]) for name in TEST_NAMES]
                        raw_ps.extend(t["p_value"] for t in tests)
                        raw_stats.extend(t["statistic"] for t in tests)
                        fits.append(fit)
                        errors.append(None)
                    except (InferenceError, np.linalg.LinAlgError) as exc:
                        raw_ps.extend([None] * 3)
                        raw_stats.extend([None] * 3)
                        fits.append(None)
                        errors.append(str(exc))

                adjusted = holm_six(raw_ps)
                slot = by_lag[lag]
                any_invalid = any(p is None for p in raw_ps)
                if any_invalid:
                    slot["invalid"] += 1
                if any(t["reject"] for t in adjusted):
                    slot["family_reject"] += 1
                for i in range(6):
                    if adjusted[i]["reject"]:
                        slot["adjusted_reject"][i] += 1
                    if raw_ps[i] is not None and raw_ps[i] <= diag["raw_alpha"]:
                        slot["raw_reject"][i] += 1
                    if raw_stats[i] is not None:
                        slot["wald"][i].append(float(raw_stats[i]))

                for asset, fit in enumerate(fits):
                    if fit is not None:
                        for j, idx in enumerate(range(7, 14)):
                            slot["coef"][asset][j].append(float(fit.coefficients[idx]))
                            slot["est_var"][asset][j].append(float(fit.covariance[idx, idx]))

                ledger.append({
                    "case": case,
                    "replication": replication,
                    "lag": lag,
                    "raw_p": raw_ps,
                    "adjusted": adjusted,
                    "errors": errors,
                })

            if replication in diag["oracle_replications"]:
                lag = diag["oracle_lag"]
                for asset in range(2):
                    asset_design = primary_design(x_returns[:, asset], years, states)
                    production = ols_hac(
                        asset_design, y_returns[:, asset], hours, segments, max_lag=lag
                    )
                    beta, cov = oracle_fit(
                        asset_design, y_returns[:, asset], hours, segments, lag
                    )
                    beta_diff = float(np.max(np.abs(production.coefficients - beta)))
                    cov_diff = float(np.max(np.abs(production.covariance - cov)))
                    oracle_checks.append({
                        "case": case,
                        "replication": replication,
                        "asset": ("BTC", "ETH")[asset],
                        "lag": lag,
                        "max_abs_coefficient_difference": beta_diff,
                        "max_abs_covariance_difference": cov_diff,
                        "coefficient_within_tolerance": beta_diff <= diag["coefficient_tolerance"],
                        "covariance_within_tolerance": cov_diff <= diag["covariance_tolerance"],
                    })

            if (replication + 1) % 100 == 0:
                print(f"{case}: {replication + 1}/{diag['replications']}", flush=True)

        for lag in diag["hac_lags"]:
            slot = by_lag[lag]
            restriction_df = [7, 4, 2, 7, 4, 2]
            wald_summary = {}
            for i, name in enumerate(SLOT_NAMES):
                wald_summary[name] = (
                    quantile_record(slot["wald"][i], restriction_df[i])
                    if slot["wald"][i]
                    else None
                )

            variance_calibration = {}
            for asset in range(2):
                asset_name = ("BTC", "ETH")[asset]
                variance_calibration[asset_name] = {}
                for j, name in enumerate(SLOPE_NAMES):
                    coefs = np.asarray(slot["coef"][asset][j], dtype=np.float64)
                    est = np.asarray(slot["est_var"][asset][j], dtype=np.float64)
                    empirical = float(np.var(coefs, ddof=1)) if len(coefs) > 1 else None
                    mean_est = float(np.mean(est)) if len(est) else None
                    ratio_value = (
                        float(empirical / mean_est)
                        if empirical is not None and mean_est is not None and mean_est > 0
                        else None
                    )
                    variance_calibration[asset_name][name] = {
                        "empirical_coefficient_variance": empirical,
                        "mean_estimated_marginal_variance": mean_est,
                        "empirical_to_estimated_ratio": ratio_value,
                    }

            summaries[case][str(lag)] = {
                "family_wise_adjusted_rejection": rate(
                    slot["family_reject"], diag["replications"]
                ),
                "adjusted_rejection_by_slot": {
                    name: rate(int(slot["adjusted_reject"][i]), diag["replications"])
                    for i, name in enumerate(SLOT_NAMES)
                },
                "raw_p_le_0_05_by_slot": {
                    name: rate(int(slot["raw_reject"][i]), diag["replications"])
                    for i, name in enumerate(SLOT_NAMES)
                },
                "invalid_replicates": rate(slot["invalid"], diag["replications"]),
                "wald_quantiles": wald_summary,
                "coefficient_variance_calibration": variance_calibration,
            }

    oracle_pass = all(
        row["coefficient_within_tolerance"] and row["covariance_within_tolerance"]
        for row in oracle_checks
    )
    result = {
        "classification": "SYNTHETIC_DIAGNOSTIC_ONLY",
        "market_data_accessed": False,
        "validation_or_oos_accessed": False,
        "strategy_pnl_calculated": False,
        "strategy_signals_generated": False,
        "empirical_release_authorized": False,
        "v1_failure_preserved": True,
        "provenance": meta,
        "diagnostic_config": diag,
        "oracle": {
            "all_checks_within_frozen_tolerance": oracle_pass,
            "checks": oracle_checks,
        },
        "cases": summaries,
        "interpretation_status": (
            "NO_ORACLE_MISMATCH_OBSERVED" if oracle_pass else "IMPLEMENTATION_ORACLE_MISMATCH"
        ),
    }

    out = ROOT / "research/experiments/ams_dep_v1_failure_diagnostic_v1_results"
    out.mkdir(exist_ok=True)
    raw_ledger = b"".join(
        (json.dumps(row, sort_keys=True, allow_nan=False) + "\n").encode()
        for row in ledger
    )
    compressed = gzip.compress(raw_ledger, mtime=0)
    (out / "replicates.jsonl.gz").write_bytes(compressed)
    result["replicate_ledger_sha256"] = sha256(compressed)
    result["replicate_ledger_uncompressed_sha256"] = sha256(raw_ledger)
    (out / "summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(json.dumps({
        "oracle_pass": oracle_pass,
        "family_rejection": {
            case: {
                lag: summaries[case][str(lag)]["family_wise_adjusted_rejection"]["rate"]
                for lag in diag["hac_lags"]
            }
            for case in diag["cases"]
        },
    }, sort_keys=True), flush=True)
    print("AMS_DEP_V1_FAILURE_DIAGNOSTIC_COMPLETE", flush=True)


if __name__ == "__main__":
    main()
