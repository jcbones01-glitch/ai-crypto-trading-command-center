from research_core.ams_dep_v2_aggregation import SLOTS, summarize, task_index


def base_config(case, null_slots, power_slots=None, n=4):
    return {
        "cases": [case],
        "primary_slots": list(SLOTS),
        "calibration_replications_per_dgp": n,
        "bootstrap_requested_draws": 4999,
        "invalid_fraction_upper_bound": 0.01,
        "null_fwer_upper_bound": 0.075,
        "power_lower_bound": 0.8,
        "null_slots": {case: list(null_slots)},
        "power_slots": {case: list(power_slots or [])},
    }


def make_rows(config, raw_ps, invalid_slot=None):
    rows={}
    n=config["calibration_replications_per_dgp"]
    for outer in range(n):
        for slot in range(6):
            idx=task_index(0,outer,slot//3,slot%3,n)
            bad=invalid_slot==slot
            rows[idx]={"available":not bad,"raw_p":None if bad else raw_ps[slot],
                       "requested_draws":0 if bad else 4999,"invalid_draws":0}
    return rows


def test_null_family_passes_without_false_rejection():
    cfg=base_config("iid_null",range(6))
    cases,outer=summarize(cfg,make_rows(cfg,[0.5]*6))
    assert cases["iid_null"]["calibration_screen_pass"] is True
    assert cases["iid_null"]["false_rejection_any_true_null"]["rate"]==0
    assert len(outer)==4


def test_power_slots_do_not_replace_true_null_family():
    cfg=base_config("stable_ar",[1,2,4,5],["BTC_DEP","ETH_DEP"])
    cases,_=summarize(cfg,make_rows(cfg,[0.0001,0.5,0.5,0.0001,0.5,0.5]))
    r=cases["stable_ar"]
    assert r["rejection_rates"]["BTC_DEP"]["rate"]==1
    assert r["rejection_rates"]["ETH_DEP"]["rate"]==1
    assert r["false_rejection_any_true_null"]["rate"]==0
    assert r["calibration_screen_pass"] is True


def test_original_invalidity_above_one_percent_fails():
    cfg=base_config("iid_null",range(6),n=100)
    rows=make_rows(cfg,[0.5]*6)
    for outer in (0,1):
        idx=task_index(0,outer,0,0,100)
        rows[idx]={"available":False,"raw_p":None,"requested_draws":0,"invalid_draws":0}
    cases,_=summarize(cfg,rows)
    assert cases["iid_null"]["original_invalidity_by_slot"]["BTC_DEP"]["rate"]==0.02
    assert cases["iid_null"]["calibration_screen_pass"] is False


def test_bootstrap_invalidity_above_one_percent_fails():
    cfg=base_config("iid_null",range(6))
    rows=make_rows(cfg,[0.5]*6)
    for outer in range(4):
        rows[task_index(0,outer,0,0,4)]["invalid_draws"]=50
    cases,_=summarize(cfg,rows)
    assert cases["iid_null"]["bootstrap_invalidity_by_slot"]["BTC_DEP"]["rate"]>0.01
    assert cases["iid_null"]["calibration_screen_pass"] is False
