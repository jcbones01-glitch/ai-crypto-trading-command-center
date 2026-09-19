"""Independent dense/direct formulas on engineering fixtures, not calibration."""
import numpy as np
import pytest
from research_core import dependent_wild_bootstrap_v2 as mod
from research_core.dependence_statistics import primary_design, RESTRICTIONS, InferenceError


def scalar_kernel(distance, bandwidth):
    z=abs(float(distance))/bandwidth
    if z >= 1: return 0.
    if z <= .5: return 1-6*z**2+6*z**3
    return 2*(1-z)**3


def oracle_kernel(hours,segments):
    out=np.zeros((len(hours),len(hours)))
    for i in range(len(hours)):
        n=sum(s==segments[i] for s in segments)
        for j in range(len(hours)):
            if segments[i]==segments[j]:
                out[i,j]=scalar_kernel(int(hours[i])-int(hours[j]),max(2.,n**(1/5)))
    return out


def fixture(n_per_year=30):
    n=5*n_per_year
    t=np.arange(n,dtype=float)
    years=np.repeat(np.arange(2017,2022),n_per_year)
    states=np.array(['LOW','NORMAL','HIGH'])[(np.arange(n)//3)%3]
    x=.01*(np.sin(t*np.sqrt(2))+.3*np.cos(t*np.sqrt(3)))
    y=.01*np.cos(t*np.sqrt(5))+.15*x
    h=np.concatenate([np.arange(n_per_year)+k*10000 for k in range(5)])
    seg=np.repeat(np.arange(5),n_per_year)
    return primary_design(x,years,states),y,h,seg


def test_multiplier_factor_matches_independent_exact_time_psd_oracle():
    h=np.array([0,1,3,4,20,21,22,24],dtype=int)
    s=np.array([0,0,0,0,1,1,1,1],dtype=int)
    g=mod.ParzenGeometry(h,s)
    expected=oracle_kernel(h,s)
    actual=np.zeros_like(expected)
    for (start,end,_),band in zip(g.blocks,g.factors):
        lower=np.zeros((end-start,end-start))
        for d in range(len(band)):
            for j in range(end-start-d): lower[j+d,j]=band[d,j]
        actual[start:end,start:end]=lower@lower.T
    np.testing.assert_allclose(actual,expected,atol=1e-14,rtol=1e-14)
    np.testing.assert_array_equal(expected,expected.T)
    np.testing.assert_array_equal(np.diag(expected),np.ones(len(h)))
    assert np.linalg.eigvalsh(expected)[0]>=-1e-14
    assert np.count_nonzero(expected[:4,4:])==0
    assert expected[1,2]==0 # Two real hours apart, not adjacent pseudo-time.
    assert expected[0,1]>0


def test_parzen_meat_matches_dense_direct_oracle():
    h=np.array([0,1,3,4,20,21,22,24]);s=np.repeat([0,1],4)
    scores=np.arange(24,dtype=float).reshape(8,3)/17
    np.testing.assert_allclose(mod.ParzenGeometry(h,s).meat(scores),
                               scores.T@oracle_kernel(h,s)@scores,atol=1e-12,rtol=1e-12)


def test_ols_and_restricted_fit_match_independent_normal_equations():
    x,y,h,s=fixture()
    g=mod.ParzenGeometry(h,s)
    fit=mod.FixedOLS(x).fit(y,g)
    bread=np.linalg.inv(x.T@x)
    beta=np.linalg.solve(x.T@x,x.T@y)
    residual=y-x@beta
    scores=x*residual[:,None]
    cov=bread@(scores.T@oracle_kernel(h,s)@scores)@bread*len(y)/(len(y)-14)
    np.testing.assert_allclose(fit.coefficients,beta,atol=1e-10,rtol=1e-10)
    np.testing.assert_allclose(fit.covariance,cov,atol=1e-10,rtol=1e-10)
    for name,ix in RESTRICTIONS.items():
        r=np.eye(14)[list(ix)]
        restricted=beta-bread@r.T@np.linalg.solve(r@bread@r.T,r@beta)
        fitted,centered=mod.restricted_components(x,y,g,name)
        np.testing.assert_allclose(fitted,x@restricted,atol=1e-10,rtol=1e-10)
        for start,end,_ in g.blocks:
            assert abs(centered[start:end].mean())<1e-14
        expected=float((r@beta)@np.linalg.solve(r@cov@r.T,r@beta))
        assert mod.wald(fit,name)==pytest.approx(expected,rel=1e-10,abs=1e-10)


def test_seed_order_replay_and_segment_independence():
    h=np.arange(12);s=np.repeat([0,1],6)
    g=mod.ParzenGeometry(h,s)
    key=[2026092001,2,0,0,0,0,3]
    first=g.multipliers(key)
    g.multipliers(key[:-1]+[9])
    np.testing.assert_array_equal(first,g.multipliers(key))
    altered=mod.ParzenGeometry(np.r_[np.arange(6),np.arange(6)+100],s)
    np.testing.assert_array_equal(first,altered.multipliers(key))
    assert not np.array_equal(first,g.multipliers([2026092001,2,0,0,1,0,3]))


def test_invalid_draws_count_as_exceedances_without_redraw():
    assert mod.count_exceedances(2,[None,float('nan'),float('inf'),-1,2,1])==(5,4)
    p=mod.bootstrap_p_value(2,[None]+[1.]*4998)
    assert p['raw_p']==2/5000
    assert p['invalid_draws']==1
    with pytest.raises(InferenceError,match='4999'):
        mod.bootstrap_p_value(2,[1.]*10)


def test_geometry_rejects_bad_time_and_recurring_segments():
    with pytest.raises(InferenceError): mod.ParzenGeometry([0,0],[0,0])
    with pytest.raises(InferenceError): mod.ParzenGeometry([0.,1.],[0,0])
    with pytest.raises(InferenceError): mod.ParzenGeometry([0,1,2],[0,1,0])
    with pytest.raises(InferenceError): mod.ParzenGeometry([0,100001],[0,0])


def test_engineering_fixture_is_bounded_and_does_not_report_p_value():
    x,y,h,s=fixture()
    result=mod.engineering_fixture(x,y,h,s,'DEP',draws=2)
    assert result['p_value'] is None
    assert result['classification']=='ENGINEERING_ONLY_NOT_CALIBRATION'
    with pytest.raises(InferenceError): mod.engineering_fixture(x,y,h,s,'DEP',draws=33)


def test_proposed_seed_namespaces_are_disjoint_and_execution_is_not_frozen():
    import json
    from pathlib import Path
    p=Path(__file__).resolve().parents[1]/'research/experiments/ams_dep_synthetic_core_v2_proposed.json'
    spec=json.loads(p.read_text())
    roots=list(spec['bootstrap_roots'].values())+list(spec['data_roots'].values())
    assert len(roots)==len(set(roots))
    assert spec['bootstrap_requested_draws']==mod.BOOTSTRAP_DRAWS==4999
    assert spec['calibration_replications_per_dgp']==spec['holdout_replications_per_dgp']==2000
    assert spec['calibration_authorized'] is False
    assert spec['market_data_authorized'] is False
    assert len(spec['cases'])==11
