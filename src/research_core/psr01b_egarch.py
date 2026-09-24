"""PSR-01B exact segmented EGARCH implementation.

This module is numerical and source-agnostic.  It fits/replays only caller-
supplied synthetic or already-authorized return segments; it performs no data
acquisition or protected-data access.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln

from .psr01b_core import PSR01BError


ORDERS = ((1, 1, 1), (2, 1, 1), (1, 1, 2), (2, 1, 2))


@dataclass(frozen=True)
class EGARCHFit:
    order: tuple[int, int, int]
    available: bool
    params: np.ndarray | None
    log_likelihood: float | None
    aic: float | None
    message: str | None


@dataclass(frozen=True)
class EGARCHReplay:
    h_current: np.ndarray
    z_current: np.ndarray
    sigma_next: np.ndarray
    log_sigma_next: np.ndarray


def standardized_t_abs_mean(nu: float) -> float:
    nu = float(nu)
    if not np.isfinite(nu) or nu <= 2.0:
        raise PSR01BError("Student-t nu must exceed 2")
    log_num = math.log(2.0) + 0.5 * math.log(nu - 2.0) + gammaln((nu + 1.0) / 2.0)
    log_den = math.log(nu - 1.0) + 0.5 * math.log(math.pi) + gammaln(nu / 2.0)
    value = math.exp(log_num - log_den)
    if not np.isfinite(value):
        raise PSR01BError("nonfinite Student-t absolute moment")
    return float(value)


def standardized_t_log_density(z: float, nu: float) -> float:
    z = float(z)
    nu = float(nu)
    if not np.isfinite(z) or not np.isfinite(nu) or nu <= 2.0:
        raise PSR01BError("invalid standardized Student-t input")
    value = (
        gammaln((nu + 1.0) / 2.0)
        - gammaln(nu / 2.0)
        - 0.5 * math.log(math.pi * (nu - 2.0))
        - ((nu + 1.0) / 2.0) * math.log1p((z * z) / (nu - 2.0))
    )
    if not np.isfinite(value):
        raise PSR01BError("nonfinite standardized Student-t density")
    return float(value)


def _param_slices(order: tuple[int, int, int]):
    p, o, q = order
    if order not in ORDERS:
        raise PSR01BError("unregistered EGARCH order")
    alpha = slice(2, 2 + p)
    gamma = slice(alpha.stop, alpha.stop + o)
    beta = slice(gamma.stop, gamma.stop + q)
    nu_index = beta.stop
    return alpha, gamma, beta, nu_index


def unpack_params(params: Sequence[float], order: tuple[int, int, int]):
    p, o, q = order
    alpha_s, gamma_s, beta_s, nu_i = _param_slices(order)
    x = np.asarray(params, dtype=np.float64)
    expected = 3 + p + o + q
    if x.ndim != 1 or len(x) != expected or not np.isfinite(x).all():
        raise PSR01BError("invalid EGARCH parameter vector")
    mu = float(x[0])
    omega = float(x[1])
    alpha = x[alpha_s].copy()
    gamma = x[gamma_s].copy()
    beta = x[beta_s].copy()
    nu = float(x[nu_i])
    return mu, omega, alpha, gamma, beta, nu


def _reset_state(params: Sequence[float], order: tuple[int, int, int]):
    _, omega, alpha, gamma, beta, nu = unpack_params(params, order)
    if (
        np.any(beta < 0.0)
        or np.any(beta > 0.999)
        or float(np.sum(beta)) > 0.999
        or nu <= 2.0
    ):
        raise PSR01BError("invalid EGARCH reset constraints")
    denominator = 1.0 - float(np.sum(beta))
    if denominator <= 0.0:
        raise PSR01BError("nonpositive EGARCH reset denominator")
    h_bar = omega / denominator
    if not np.isfinite(h_bar):
        raise PSR01BError("nonfinite EGARCH reset")
    try:
        variance_proxy = math.exp(h_bar)
    except OverflowError as exc:
        raise PSR01BError("EGARCH reset variance overflow") from exc
    if not np.isfinite(variance_proxy):
        raise PSR01BError("EGARCH reset variance overflow")
    h_hist = [float(h_bar)] * len(beta)
    a_hist = [0.0] * len(alpha)
    z_hist = [0.0] * len(gamma)
    return h_hist, a_hist, z_hist, standardized_t_abs_mean(nu)


def _next_h(
    omega: float,
    alpha: np.ndarray,
    gamma: np.ndarray,
    beta: np.ndarray,
    a_hist: list[float],
    z_hist: list[float],
    h_hist: list[float],
) -> float:
    value = float(omega)
    value += float(np.dot(alpha, np.asarray(a_hist[: len(alpha)], dtype=np.float64)))
    value += float(np.dot(gamma, np.asarray(z_hist[: len(gamma)], dtype=np.float64)))
    value += float(np.dot(beta, np.asarray(h_hist[: len(beta)], dtype=np.float64)))
    if not np.isfinite(value):
        raise PSR01BError("nonfinite EGARCH recursion")
    return value


def replay_segment(
    returns_y: Sequence[float],
    params: Sequence[float],
    order: tuple[int, int, int],
) -> EGARCHReplay:
    """Replay one contiguous y_t segment from the registered reset state."""
    y = np.asarray(returns_y, dtype=np.float64)
    if y.ndim != 1 or len(y) == 0 or not np.isfinite(y).all():
        raise PSR01BError("EGARCH segment must be a finite non-empty 1-D vector")
    mu, omega, alpha, gamma, beta, nu = unpack_params(params, order)
    h_hist, a_hist, z_hist, m_nu = _reset_state(params, order)

    h_values = np.empty(len(y), dtype=np.float64)
    z_values = np.empty(len(y), dtype=np.float64)
    sigma_next = np.empty(len(y), dtype=np.float64)
    log_sigma_next = np.empty(len(y), dtype=np.float64)

    for t, obs in enumerate(y):
        h_t = _next_h(omega, alpha, gamma, beta, a_hist, z_hist, h_hist)
        try:
            sigma_t = math.exp(h_t / 2.0)
        except OverflowError as exc:
            raise PSR01BError("EGARCH sigma overflow") from exc
        if not np.isfinite(sigma_t) or sigma_t <= 0.0:
            raise PSR01BError("invalid EGARCH sigma")
        z_t = (float(obs) - mu) / sigma_t
        if not np.isfinite(z_t):
            raise PSR01BError("nonfinite EGARCH standardized residual")
        a_t = abs(z_t) - m_nu

        h_hist = [h_t] + h_hist[:-1]
        a_hist = [a_t] + a_hist[:-1]
        z_hist = [z_t] + z_hist[:-1]
        h_next = _next_h(omega, alpha, gamma, beta, a_hist, z_hist, h_hist)
        try:
            sigma_n = math.exp(h_next / 2.0)
        except OverflowError as exc:
            raise PSR01BError("EGARCH next sigma overflow") from exc
        if not np.isfinite(sigma_n) or sigma_n <= 0.0:
            raise PSR01BError("invalid EGARCH next sigma")

        h_values[t] = h_t
        z_values[t] = z_t
        sigma_next[t] = sigma_n
        log_sigma_next[t] = h_next / 2.0

    return EGARCHReplay(h_values, z_values, sigma_next, log_sigma_next)


def segment_log_likelihood(
    returns_y: Sequence[float],
    params: Sequence[float],
    order: tuple[int, int, int],
) -> float:
    y = np.asarray(returns_y, dtype=np.float64)
    if y.ndim != 1 or len(y) == 0 or not np.isfinite(y).all():
        raise PSR01BError("invalid EGARCH likelihood segment")
    mu, omega, alpha, gamma, beta, nu = unpack_params(params, order)
    h_hist, a_hist, z_hist, m_nu = _reset_state(params, order)
    total = 0.0
    for obs in y:
        h_t = _next_h(omega, alpha, gamma, beta, a_hist, z_hist, h_hist)
        try:
            sigma_t = math.exp(h_t / 2.0)
        except OverflowError as exc:
            raise PSR01BError("EGARCH sigma overflow") from exc
        if not np.isfinite(sigma_t) or sigma_t <= 0.0:
            raise PSR01BError("invalid EGARCH sigma")
        z_t = (float(obs) - mu) / sigma_t
        if not np.isfinite(z_t):
            raise PSR01BError("nonfinite EGARCH residual")
        total += standardized_t_log_density(z_t, nu) - 0.5 * h_t
        a_t = abs(z_t) - m_nu
        h_hist = [h_t] + h_hist[:-1]
        a_hist = [a_t] + a_hist[:-1]
        z_hist = [z_t] + z_hist[:-1]
    if not np.isfinite(total):
        raise PSR01BError("nonfinite EGARCH log likelihood")
    return float(total)


def joint_log_likelihood(
    segments: Sequence[Sequence[float]],
    params: Sequence[float],
    order: tuple[int, int, int],
) -> float:
    if not segments:
        raise PSR01BError("at least one EGARCH segment is required")
    return float(sum(segment_log_likelihood(segment, params, order) for segment in segments))


def initial_params(
    segments: Sequence[Sequence[float]],
    order: tuple[int, int, int],
) -> np.ndarray:
    p, o, q = order
    _param_slices(order)
    arrays = [np.asarray(s, dtype=np.float64) for s in segments]
    if not arrays or any(a.ndim != 1 or len(a) == 0 or not np.isfinite(a).all() for a in arrays):
        raise PSR01BError("invalid EGARCH training segments")
    pooled = np.concatenate(arrays)
    variance = float(np.var(pooled, ddof=0))
    if not np.isfinite(variance) or variance <= 0.0:
        raise PSR01BError("EGARCH initial variance must be positive")
    x = np.array(
        [
            float(np.mean(pooled)),
            math.log(variance) * 0.10,
            *([0.05 / p] * p),
            *([0.0] * o),
            *([0.90 / q] * q),
            8.0,
        ],
        dtype=np.float64,
    )
    return x


def _bounds(order: tuple[int, int, int]):
    p, o, q = order
    return (
        [(-1000.0, 1000.0), (-20.0, 20.0)]
        + [(-2.0, 2.0)] * p
        + [(-2.0, 2.0)] * o
        + [(0.0, 0.999)] * q
        + [(2.05, 200.0)]
    )


def fit_order(
    segments: Sequence[Sequence[float]],
    order: tuple[int, int, int],
) -> EGARCHFit:
    """Fit one registered order with the frozen deterministic SLSQP contract."""
    if order not in ORDERS:
        raise PSR01BError("unregistered EGARCH order")
    try:
        start = initial_params(segments, order)
    except PSR01BError as exc:
        return EGARCHFit(order, False, None, None, None, str(exc))

    bounds = _bounds(order)
    if any(not (lo <= value <= hi) for value, (lo, hi) in zip(start, bounds)):
        return EGARCHFit(order, False, None, None, None, "registered start outside bounds")

    _, _, beta_slice, _ = _param_slices(order)

    def objective(x):
        try:
            return -joint_log_likelihood(segments, x, order)
        except (PSR01BError, FloatingPointError, OverflowError, ValueError):
            return 1e100

    constraint = {
        "type": "ineq",
        "fun": lambda x: 0.999 - float(np.sum(np.asarray(x)[beta_slice])),
    }
    result = minimize(
        objective,
        start,
        method="SLSQP",
        bounds=bounds,
        constraints=(constraint,),
        options={"maxiter": 5000, "ftol": 1e-10, "disp": False},
    )
    if not bool(result.success) or not np.isfinite(result.fun) or not np.isfinite(result.x).all():
        return EGARCHFit(order, False, None, None, None, str(result.message))
    try:
        ll = joint_log_likelihood(segments, result.x, order)
    except PSR01BError as exc:
        return EGARCHFit(order, False, None, None, None, str(exc))
    k = 3 + sum(order)
    aic = 2.0 * k - 2.0 * ll
    if not np.isfinite(aic):
        return EGARCHFit(order, False, None, None, None, "nonfinite AIC")
    return EGARCHFit(order, True, np.asarray(result.x, dtype=np.float64), float(ll), float(aic), None)


def select_best_order(segments: Sequence[Sequence[float]]) -> EGARCHFit:
    """Fit all four registered orders and choose lowest finite AIC; order breaks ties."""
    fits = [fit_order(segments, order) for order in ORDERS]
    available = [fit for fit in fits if fit.available and fit.aic is not None and np.isfinite(fit.aic)]
    if not available:
        raise PSR01BError("all four EGARCH orders unavailable")
    # Python min is stable, so exact AIC ties retain registered ORDERS sequence.
    return min(available, key=lambda fit: float(fit.aic))


def replay_segments(
    segments: Sequence[Sequence[float]],
    params: Sequence[float],
    order: tuple[int, int, int],
) -> tuple[EGARCHReplay, ...]:
    """Replay multiple continuity segments with an independent reset at each gap."""
    if not segments:
        raise PSR01BError("at least one replay segment required")
    return tuple(replay_segment(segment, params, order) for segment in segments)
