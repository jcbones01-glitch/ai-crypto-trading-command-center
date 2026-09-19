from __future__ import annotations
import math
from research_core.dependence_statistics import holm_six

SLOTS=("BTC_DEP","BTC_TIME","BTC_STATE","ETH_DEP","ETH_TIME","ETH_STATE")


def task_index(dgp,outer,asset,hyp,n_outer):
    return (((dgp*n_outer)+outer)*2+asset)*3+hyp


def wilson(count,total):
    if total<=0:
        return {"count":count,"denominator":total,"rate":None,"wilson_95":None}
    z=1.959963984540054
    rate=count/total
    den=1+z*z/total
    center=(rate+z*z/(2*total))/den
    half=z*math.sqrt(rate*(1-rate)/total+z*z/(4*total*total))/den
    return {"count":count,"denominator":total,"rate":rate,
            "wilson_95":[max(0.,center-half),min(1.,center+half)]}


def summarize(config,rows):
    n_outer=int(config["calibration_replications_per_dgp"])
    cases={}
    outer_ledger=[]
    for dgp,case in enumerate(config["cases"]):
        rejects=[0]*6
        orig_bad=[0]*6
        inner_bad=[0]*6
        inner_n=[0]*6
        inner_max=[0.]*6
        any_orig_bad=0
        false_reject=0
        true_null=set(int(x) for x in config["null_slots"].get(case,[]))
        for outer in range(n_outer):
            raw=[]
            available=[]
            fractions=[]
            for slot in range(6):
                row=rows[task_index(dgp,outer,slot//3,slot%3,n_outer)]
                ok=bool(row["available"])
                available.append(ok)
                raw.append(float(row["raw_p"]) if ok else None)
                if not ok:
                    orig_bad[slot]+=1
                    fractions.append(None)
                else:
                    requested=int(row["requested_draws"])
                    invalid=int(row["invalid_draws"])
                    if requested!=int(config["bootstrap_requested_draws"]):
                        raise RuntimeError("wrong requested draw count")
                    inner_n[slot]+=requested
                    inner_bad[slot]+=invalid
                    f=invalid/requested
                    fractions.append(f)
                    inner_max[slot]=max(inner_max[slot],f)
            tests=holm_six(raw)
            if not all(available):
                any_orig_bad+=1
            for i,test in enumerate(tests):
                rejects[i]+=int(test["reject"])
            if true_null and any(tests[i]["reject"] for i in true_null):
                false_reject+=1
            outer_ledger.append({"dgp_index":dgp,"case":case,"outer_index":outer,
                                 "tests":tests,"original_available":available,
                                 "bootstrap_invalid_fraction":fractions})
        rejection={SLOTS[i]:wilson(rejects[i],n_outer) for i in range(6)}
        original={SLOTS[i]:wilson(orig_bad[i],n_outer) for i in range(6)}
        inner={}
        for i,slot in enumerate(SLOTS):
            inner[slot]={**wilson(inner_bad[i],inner_n[i]),
                         "per_outer_max":inner_max[i] if inner_n[i] else None}
        fwer=wilson(false_reject,n_outer) if true_null else None
        passed=True
        for slot in SLOTS:
            if original[slot]["rate"] is None or original[slot]["rate"]>config["invalid_fraction_upper_bound"]:
                passed=False
            if inner[slot]["rate"] is None or inner[slot]["rate"]>config["invalid_fraction_upper_bound"]:
                passed=False
        if fwer is not None and fwer["rate"]>config["null_fwer_upper_bound"]:
            passed=False
        for slot in config["power_slots"].get(case,[]):
            if rejection[slot]["rate"]<config["power_lower_bound"]:
                passed=False
        cases[case]={"rejection_rates":rejection,
                     "original_invalidity_by_slot":original,
                     "any_original_invalid_family":wilson(any_orig_bad,n_outer),
                     "bootstrap_invalidity_by_slot":inner,
                     "false_rejection_any_true_null":fwer,
                     "true_null_slot_indices":sorted(true_null),
                     "power_screen_slots":list(config["power_slots"].get(case,[])),
                     "calibration_screen_pass":bool(passed)}
    return cases,outer_ledger
