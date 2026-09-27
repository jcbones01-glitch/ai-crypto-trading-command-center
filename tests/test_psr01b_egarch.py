"""Synthetic numerical oracles for PSR-01B segmented EGARCH."""
import math

import numpy as np
import pytest
from scipy.special import gamma

from research_core.psr01b_core import PSR01BError
from research_core.psr01b_egarch import (
    ORDERS,
    fit_order,
    initial_params,
    joint_log_likelihood,
    replay_segment,
    replay_segments,
    segment_log_likelihood,
    standardized_t_abs_mean,
    standardized_t_log_density,
)


def test_registered_order_sequence_is_exact():
    assert ORDERS == ((1, 1, 1), (2, 1, 1), (1, 1, 2), (2, 1, 2))


def test_student_t_absolute_moment_matches_registered_formula():
    nu = 8.0
    expected = (
        2
        * math.sqrt(nu - 2)
        * gamma((nu + 1) / 2)
        / ((nu - 1) * math.sqrt(math.pi) * gamma(nu / 2))
    )
    assert standardized_t_abs_mean(nu) == pytest.approx(expected, rel=1e-14)


def test_student_t_log_density_matches_direct_formula():
    z = 0.75
    nu = 8.0
    expected = (
        math.lgamma((nu + 1) / 2)
        - math.lgamma(nu / 2)
        - 0.5 * math.log(math.pi * (nu - 2))
        - ((nu + 1) / 2) * math.log(1 + z * z / (nu - 2))
    )
    assert standardized_t_log_density(z, nu) == pytest.approx(expected, rel=1e-14)


def test_first_reset_h_equals_hbar_and_next_feature_is_causal():
    # order (1,1,1): [mu, omega, alpha, gamma, beta, nu]
    params = np.array([0.0, -0.1, 0.1, -0.05, 0.8, 8.0])
    y = np.array([0.2, -0.1])
    out = replay_segment(y, params, (1, 1, 1))

    h_bar = -0.1 / (1 - 0.8)
    assert out.h_current[0] == pytest.approx(h_bar)

    sigma0 = math.exp(h_bar / 2)
    z0 = y[0] / sigma0
    m = standardized_t_abs_mean(8.0)
    a0 = abs(z0) - m
    h1 = -0.1 + 0.1 * a0 - 0.05 * z0 + 0.8 * h_bar
    assert out.z_current[0] == pytest.approx(z0)
    assert out.log_sigma_next[0] == pytest.approx(h1 / 2)
    assert out.sigma_next[0] == pytest.approx(math.exp(h1 / 2))
    # Current y1 cannot affect the feature emitted after y0.
    assert out.sigma_next[0] != pytest.approx(out.sigma_next[1])


def test_segmented_joint_likelihood_resets_each_segment():
    params = np.array([0.0, -0.1, 0.1, 0.0, 0.8, 8.0])
    y = np.array([0.1, -0.2, 0.3, 0.05])
    one = segment_log_likelihood(y, params, (1, 1, 1))
    joint = joint_log_likelihood([y, y], params, (1, 1, 1))
    assert joint == pytest.approx(2 * one, rel=1e-14)

    replays = replay_segments([y, y], params, (1, 1, 1))
    np.testing.assert_allclose(replays[0].h_current, replays[1].h_current, atol=0, rtol=0)
    np.testing.assert_allclose(replays[0].z_current, replays[1].z_current, atol=0, rtol=0)


def test_initial_parameters_match_frozen_contract():
    a = np.array([1.0, 2.0, 3.0])
    b = np.array([4.0, 5.0])
    x = initial_params([a, b], (2, 1, 2))
    pooled = np.r_[a, b]
    expected_variance = np.var(pooled, ddof=0)
    assert x[0] == pytest.approx(np.mean(pooled))
    assert x[1] == pytest.approx(math.log(expected_variance) * 0.10)
    np.testing.assert_allclose(x[2:4], [0.025, 0.025])
    assert x[4] == 0.0
    np.testing.assert_allclose(x[5:7], [0.45, 0.45])
    assert x[7] == 8.0


def test_invalid_reset_constraints_fail_closed():
    y = [0.1, -0.1]
    bad_beta = [0.0, -0.1, 0.1, 0.0, 1.0, 8.0]
    with pytest.raises(PSR01BError):
        segment_log_likelihood(y, bad_beta, (1, 1, 1))

    bad_nu = [0.0, -0.1, 0.1, 0.0, 0.8, 2.0]
    with pytest.raises(PSR01BError):
        segment_log_likelihood(y, bad_nu, (1, 1, 1))


def test_zero_variance_training_makes_order_unavailable():
    fit = fit_order([np.ones(100)], (1, 1, 1))
    assert not fit.available
    assert fit.params is None
    assert fit.aic is None


def test_deterministic_slsqp_fit_is_reproducible_on_synthetic_returns():
    rng = np.random.default_rng(20260924)
    # Synthetic only: nonconstant bounded sample, no market data.
    y = rng.standard_t(df=8, size=240) * math.sqrt((8 - 2) / 8)
    first = fit_order([y[:120], y[120:]], (1, 1, 1))
    second = fit_order([y[:120], y[120:]], (1, 1, 1))
    assert first.available and second.available
    assert first.aic == pytest.approx(second.aic, rel=0, abs=1e-10)
    assert first.log_likelihood == pytest.approx(second.log_likelihood, rel=0, abs=1e-10)
    np.testing.assert_allclose(first.params, second.params, rtol=0, atol=1e-10)


def test_fit_aic_uses_k_equals_three_plus_p_plus_o_plus_q():
    rng = np.random.default_rng(7)
    y = rng.normal(size=180)
    fit = fit_order([y], (1, 1, 1))
    assert fit.available
    k = 3 + 1 + 1 + 1
    assert fit.aic == pytest.approx(2 * k - 2 * fit.log_likelihood)
