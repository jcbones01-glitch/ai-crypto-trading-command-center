"""Synthetic numerical oracles only; no market data or network access."""
from fractions import Fraction

import numpy as np
import pytest

from research_core.dependence_statistics import (
    InferenceError, RESTRICTIONS, bartlett_meat, holm_six, ols_hac,
    primary_design, variance_ratio, wald_zero,
)


def test_hac_matches_direct_exact_time_double_sum_and_gaps():
    rng = np.random.default_rng(99)
    scores = rng.normal(size=(7, 3))
    hours = np.array([0, 1, 3, 4, 5, 8, 9])
    segments = np.array([0, 0, 0, 1, 1, 1, 1])
    for lag in (0, 1, 3, 12):
        oracle = np.zeros((3, 3))
        for i in range(len(hours)):
            for j in range(len(hours)):
                distance = abs(hours[i]-hours[j])
                if segments[i] == segments[j] and distance <= lag:
                    oracle += (1-distance/(lag+1))*np.outer(scores[i], scores[j])
        np.testing.assert_allclose(bartlett_meat(scores, hours, segments, lag), oracle, atol=1e-12)
    compressed = bartlett_meat(scores, np.arange(7), segments, 3)
    assert not np.allclose(compressed, bartlett_meat(scores, hours, segments, 3))


def test_hac_cannot_bridge_declared_continuity_break():
    scores = np.array([[1., 2.], [3., 4.]])
    got = bartlett_meat(scores, np.array([0, 1]), np.array([0, 1]), 168)
    np.testing.assert_allclose(got, scores.T@scores, atol=1e-12)


@pytest.mark.parametrize('hours,segments', [
    ([0, 0, 1], [0, 0, 0]), ([0, 2, 1], [0, 0, 0]),
    ([0., 1., 2.], [0, 0, 0]), ([0, 1, 2], [0, 1, 0]),
    ([0, 1, 100001], [0, 0, 0]), ([0, 1, 2], [0, 0]),
])
def test_hac_bad_timing_or_segment_metadata_rejected(hours, segments):
    with pytest.raises(InferenceError):
        bartlett_meat(np.ones((3, 2)), hours, segments)


def test_ols_hc1_against_separate_normal_equation_oracle():
    rng = np.random.default_rng(77)
    x = np.column_stack([np.ones(100), rng.normal(size=(100, 2))])
    y = x@np.array([1., 2., -3.]) + rng.normal(size=100)
    fit = ols_hac(x, y, np.arange(100), np.zeros(100, dtype=int), max_lag=0)
    b = np.linalg.solve(x.T@x, x.T@y)
    inv = np.linalg.inv(x.T@x)
    score = x * (y-x@b)[:, None]
    cov = inv@(score.T@score)@inv * 100/97
    np.testing.assert_allclose(fit.coefficients, b, atol=1e-12)
    np.testing.assert_allclose(fit.covariance, cov, atol=1e-12)
    np.testing.assert_allclose(fit.marginal_intervals_95.mean(axis=1), b)
    stat = b[1]**2/cov[1, 1]
    np.testing.assert_allclose(wald_zero(fit, [1])['statistic'], stat)


def test_scaling_invariance_of_wald_inference():
    rng = np.random.default_rng(2026)
    x = np.column_stack([np.ones(500), rng.normal(size=500)])
    y = .15*x[:, 1] + rng.normal(size=500)
    args = (np.arange(500), np.zeros(500, dtype=int))
    a = ols_hac(x, y, *args)
    b = ols_hac(x*np.array([1., 1e-8]), y, *args)
    np.testing.assert_allclose(wald_zero(a, [1])['p_value'], wald_zero(b, [1])['p_value'], rtol=1e-10)


@pytest.mark.parametrize('x,y', [
    (np.ones((5, 2)), np.arange(5)),
    (np.zeros((5, 1)), np.arange(5)),
    (np.ones((1, 1)), np.ones(1)),
    (np.eye(5), np.ones(5)),
    (np.array([[1], [2], [np.nan]]), np.ones(3)),
])
def test_invalid_or_unidentified_fit_is_not_repaired(x, y):
    with pytest.raises(InferenceError):
        ols_hac(x, y, np.arange(len(y)), np.zeros(len(y), dtype=int))


def test_primary_column_order_and_restrictions():
    x = np.array([2., 3., 4.])
    design = primary_design(x, [2017, 2019, 2021], ['NORMAL', 'LOW', 'HIGH'])
    assert design.shape == (3, 14)
    np.testing.assert_array_equal(design[0], [1,0,0,0,0,0,0,2,0,0,0,0,0,0])
    np.testing.assert_array_equal(design[1], [1,0,1,0,0,1,0,3,0,3,0,0,3,0])
    assert RESTRICTIONS['TIME'] == (8,9,10,11)
    for years, states in [([2017,2019,2022],['NORMAL','LOW','HIGH']),
                          ([2017,2019,2021],['NORMAL','LOW','UNKNOWN'])]:
        with pytest.raises(InferenceError):
            primary_design(x, years, states)


def test_holm_fixed_family_with_missing_and_ties():
    out = holm_six([.001, .01, .03, None, .2, .01])
    assert [v['adjusted_p'] for v in out] == [.006, .05, .09, None, .4, .05]
    assert [v['reject'] for v in out] == [True, True, False, False, False, True]
    assert out[3]['calculation_p'] == 1 and not out[3]['available']
    assert holm_six([.009, None, None, None, None, None])[0]['reject'] is False


@pytest.mark.parametrize('ps', [[.1]*5, [np.nan]*6, [np.inf]*6, [-.1]*6, [1.1]*6])
def test_invalid_multiplicity_input_rejected(ps):
    with pytest.raises(InferenceError):
        holm_six(ps)


@pytest.mark.parametrize('q', [2, 6, 24])
def test_variance_ratio_against_exact_rational_oracle(q):
    # N deliberately not divisible by q: no hidden truncation of tail returns.
    r = [Fraction((i*7)%17-8, 1000) for i in range(721)]
    n = len(r)
    mean = sum(r)/n
    centered = [v-mean for v in r]
    a = sum(z*z for z in centered)/(n-1)
    q_squares = sum(sum(centered[i:i+q])**2 for i in range(n-q+1))
    b = q_squares/(q*(n-q+1)*(1-Fraction(q,n)))
    result = variance_ratio(np.array(r,dtype=float), np.arange(n), q)
    assert result['vr'] == pytest.approx(float(b/a), rel=1e-12)
    assert result['p_value'] is None
    assert result['overlapping_sums'] == n-q+1
    shifted = variance_ratio(np.array(r,dtype=float)*3+.15, np.arange(n), q)
    assert shifted['vr'] == pytest.approx(result['vr'], rel=1e-12)


def test_vr_gaps_constants_short_samples_and_unregistered_q():
    r = np.sin(np.arange(720))
    for returns,hours,q in [(r,np.arange(720)*2,2), (np.ones(720),np.arange(720),2),
                           (r[:10],np.arange(10),2), (r,np.arange(720),3),
                           (r,np.arange(720),2.0)]:
        with pytest.raises(InferenceError):
            variance_ratio(returns,hours,q)


def test_synthetic_generator_reproducible_paired_labels_and_year_boundaries():
    import json
    import runpy
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    runner = runpy.run_path(str(root/'research/scripts/run_ams_dep_synthetic_core_v1.py'))
    config = json.loads((root/'research/experiments/ams_dep_synthetic_core_v1.json').read_text())
    years, states, hours, segments = runner['calendar'](config)
    assert len(years) == 10000
    assert len(np.flatnonzero(np.diff(hours) != 1)) == 4
    for year in config['years']:
        for state in ('LOW','NORMAL','HIGH'):
            mask = (years==year)&(states==state)
            assert mask.sum() >= 200
            assert len(np.unique(hours[mask]//24)) >= 10
    for case in ('iid_null','garch_null','state_ar','bid_ask_bounce'):
        x,y = runner['simulate'](case,0,config)
        x2,y2 = runner['simulate'](case,0,config)
        np.testing.assert_array_equal(x,x2)
        np.testing.assert_array_equal(y,y2)
        within = segments[1:]==segments[:-1]
        np.testing.assert_array_equal(x[1:][within],y[:-1][within])
        assert np.isfinite(x).all() and np.isfinite(y).all()


def test_synthetic_failure_accounting_does_not_drop_replicates():
    import runpy
    from pathlib import Path
    runner = runpy.run_path(str(Path(__file__).resolve().parents[1]/'research/scripts/run_ams_dep_synthetic_core_v1.py'))
    rows = [{'tests':holm_six([None]*6)}, {'tests':holm_six([.0001]*6)}]
    config = {'invalid_fraction_upper_bound':.01,'null_fwer_upper_bound':.075,'power_lower_bound':.8}
    summary = runner['summarize']('iid_null',rows,config)
    assert summary['invalid_replicates']['rate'] == .5
    assert summary['false_rejection_any_true_null']['rate'] == .5
    assert not summary['engineering_screen_pass']
