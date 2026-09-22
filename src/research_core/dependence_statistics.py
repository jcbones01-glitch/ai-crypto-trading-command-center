"""Offline numerical primitives, not an empirical runner or research approval.

Inputs are in-memory arrays; provenance/partition checks belong to the future
empirical loader. See docs/AMS_DEP_NUMERICAL_CONTRACT_V1.md.
"""
from dataclasses import dataclass

import numpy as np
from scipy.stats import chi2

SLOTS = ("BTC_DEP", "BTC_TIME", "BTC_STATE", "ETH_DEP", "ETH_TIME", "ETH_STATE")
RESTRICTIONS = {"DEP": tuple(range(7, 14)), "TIME": tuple(range(8, 12)), "STATE": (12, 13)}


class InferenceError(ValueError):
    """Invalid numeric input, unsupported sample or unidentified inference."""


def _vector(values, name):
    result = np.asarray(values, dtype=np.float64)
    if result.ndim != 1 or not np.isfinite(result).all():
        raise InferenceError(f"{name}: finite one-dimensional input required")
    return result


def _integer(value, name, minimum=0):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < minimum:
        raise InferenceError(f"{name}: integer >= {minimum} required")
    return int(value)


def _hour_grid(hours, n):
    raw = np.asarray(hours)
    if raw.ndim != 1 or len(raw) != n or raw.dtype.kind not in "iu":
        raise InferenceError("hours: integer hour coordinates required")
    # Avoid overflow on unsigned conversion and subtraction.
    if any(abs(int(v)) > 10**9 for v in raw):
        raise InferenceError("hours outside supported numeric range")
    out = raw.astype(np.int64)
    if len(out) > 1 and np.any(np.diff(out) <= 0):
        raise InferenceError("hours must be globally strictly increasing")
    return out


def primary_design(x, years, states):
    x = _vector(x, "x")
    years, states = np.asarray(years), np.asarray(states)
    if years.shape != x.shape or states.shape != x.shape:
        raise InferenceError("design inputs must have identical shapes")
    if not np.isin(years, [2017, 2018, 2019, 2020, 2021]).all():
        raise InferenceError("unknown year")
    if not np.isin(states, ["LOW", "NORMAL", "HIGH"]).all():
        raise InferenceError("unknown state")
    dummies = np.column_stack([np.ones(len(x)), *(years == y for y in range(2018, 2022)),
                               states == "LOW", states == "HIGH"]).astype(float)
    return np.column_stack([dummies, dummies * x[:, None]])


def bartlett_meat(scores, hours, segments, max_lag=168):
    """Exact-time HAC via the zero-padded moving-score-sum identity."""
    scores = np.asarray(scores, dtype=float)
    if scores.ndim != 2 or not np.isfinite(scores).all() or len(scores) == 0:
        raise InferenceError("finite nonempty score matrix required")
    hours = _hour_grid(hours, len(scores))
    segments = np.asarray(segments)
    if segments.ndim != 1 or len(segments) != len(scores) or segments.dtype.kind not in "iu":
        raise InferenceError("integer segment IDs required")
    max_lag = _integer(max_lag, "max_lag")
    if max_lag > 100000:
        raise InferenceError("HAC lag outside supported range")
    boundaries = np.r_[0, np.flatnonzero(segments[1:] != segments[:-1]) + 1, len(scores)]
    labels = segments[boundaries[:-1]]
    if len(np.unique(labels)) != len(labels):
        raise InferenceError("segment IDs may not recur after another segment")
    meat = np.zeros((scores.shape[1], scores.shape[1]))
    for start, end in zip(boundaries[:-1], boundaries[1:]):
        positions = hours[start:end] - hours[start]
        span = int(positions[-1]) + 1
        if span > 100000:
            raise InferenceError("segment grid span exceeds 100000 hours")
        grid = np.zeros((span, scores.shape[1]))
        grid[positions] = scores[start:end]
        padded = np.pad(grid, ((max_lag, max_lag), (0, 0)))
        cumulative = np.vstack([np.zeros((1, scores.shape[1])), np.cumsum(padded, axis=0)])
        width = max_lag + 1
        moving_sums = cumulative[width:] - cumulative[:-width]
        meat += moving_sums.T @ moving_sums / width
    if not np.isfinite(meat).all():
        raise InferenceError("nonfinite HAC meat")
    return (meat + meat.T) / 2


@dataclass(frozen=True)
class OLSHAC:
    coefficients: np.ndarray
    covariance: np.ndarray
    marginal_intervals_95: np.ndarray
    scaled_condition: float
    n: int
    p: int


def ols_hac(design, target, hours, segments, max_lag=168):
    design = np.asarray(design, dtype=float)
    target = _vector(target, "target")
    if design.ndim != 2 or len(design) != len(target) or not np.isfinite(design).all():
        raise InferenceError("finite aligned design matrix required")
    n, p = design.shape
    if n <= p or p == 0:
        raise InferenceError("OLS needs more rows than columns")
    scales = np.linalg.norm(design, axis=0)
    if np.any(scales <= 0) or not np.isfinite(scales).all():
        raise InferenceError("zero/nonfinite design-column norm")
    scaled = design / scales
    u, singular, vt = np.linalg.svd(scaled, full_matrices=False)
    condition = singular[0] / singular[-1] if singular[-1] > 0 else np.inf
    if singular[-1] <= 1e-12 * singular[0] or condition > 1e8:
        raise InferenceError("unidentified or ill-conditioned design")
    b_scaled = vt.T @ ((u.T @ target) / singular)
    residuals = target - scaled @ b_scaled
    bread = (vt.T / singular**2) @ vt
    meat = bartlett_meat(scaled * residuals[:, None], hours, segments, max_lag)
    covariance = (bread @ meat @ bread) * n / (n - p)
    covariance /= scales[:, None] * scales[None, :]
    covariance = (covariance + covariance.T) / 2
    b = b_scaled / scales
    if not np.isfinite(covariance).all() or not np.isfinite(b).all():
        raise InferenceError("nonfinite OLS output")
    eigenvalues = np.linalg.eigvalsh(covariance)
    bound = np.max(np.abs(eigenvalues))
    if eigenvalues[0] < -1e-12 * bound or np.any(np.diag(covariance) < 0):
        raise InferenceError("invalid covariance")
    half_width = 1.959963984540054 * np.sqrt(np.diag(covariance))
    return OLSHAC(b, covariance, np.column_stack([b-half_width, b+half_width]), float(condition), n, p)


def wald_zero(fit, indices):
    indices = tuple(_integer(i, "restriction index") for i in indices)
    if not indices or len(set(indices)) != len(indices) or max(indices) >= fit.p:
        raise InferenceError("invalid restriction indices")
    cov = fit.covariance[np.ix_(indices, indices)]
    b = fit.coefficients[list(indices)]
    eig = np.linalg.eigvalsh(cov)
    if eig[0] <= 0 or eig[-1] / eig[0] > 1e12:
        raise InferenceError("singular or ill-conditioned restriction covariance")
    statistic = float(b @ np.linalg.solve(cov, b))
    if not np.isfinite(statistic) or statistic < 0:
        raise InferenceError("invalid Wald statistic")
    return {"statistic": statistic, "df": len(indices), "p_value": float(chi2.sf(statistic, len(indices)))}


def holm_six(raw_values):
    """Keep all six slots, including unavailable tests, in the family."""
    raw_values = list(raw_values)
    if len(raw_values) != 6:
        raise InferenceError("exactly six primary slots required")
    for p in raw_values:
        if p is not None and (isinstance(p, bool) or not np.isfinite(p) or p < 0 or p > 1):
            raise InferenceError("invalid p-value")
    calculation = [1.0 if p is None else float(p) for p in raw_values]
    order = sorted(range(6), key=lambda i: (calculation[i], i))
    adjusted = [None] * 6
    running = 0.0
    for rank, i in enumerate(order):
        running = min(1.0, max(running, (6-rank) * calculation[i]))
        if raw_values[i] is not None:
            adjusted[i] = running
    return [{"slot": slot, "raw_p": raw_values[i], "calculation_p": calculation[i],
             "adjusted_p": adjusted[i], "available": raw_values[i] is not None,
             "reject": adjusted[i] is not None and adjusted[i] <= 0.05}
            for i, slot in enumerate(SLOTS)]


def variance_ratio(returns, hours, q):
    """Finite-sample-corrected overlapping VR point estimate, no inference."""
    returns = _vector(returns, "returns")
    hours = _hour_grid(hours, len(returns))
    q = _integer(q, "q", 2)
    if q not in (2, 6, 24):
        raise InferenceError("unregistered variance-ratio horizon")
    n = len(returns)
    if n < max(720, 20*q):
        raise InferenceError("insufficient VR support")
    if np.any(np.diff(hours) != 1):
        raise InferenceError("variance ratio requires one contiguous hourly segment")
    centered = returns - np.mean(returns)
    one_variance = float(centered @ centered / (n-1))
    if one_variance <= 0:
        raise InferenceError("zero return variance")
    sums = np.convolve(centered, np.ones(q), mode="valid")
    denominator = q * (n-q+1) * (1-q/n)
    q_variance = float(sums @ sums / denominator)
    vr = q_variance / one_variance
    if not np.isfinite(vr):
        raise InferenceError("nonfinite variance ratio")
    return {"vr": vr, "vr_minus_one": vr-1, "n": n, "q": q,
            "overlapping_sums": n-q+1, "p_value": None, "inference": "NOT_PERFORMED"}
