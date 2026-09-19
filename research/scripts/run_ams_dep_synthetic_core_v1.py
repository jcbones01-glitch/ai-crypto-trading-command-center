"""Fixed numerical-core calibration using generated data only; no market loader."""
from __future__ import annotations

# Set before importing NumPy. Multi-thread reductions are excluded from this plan.
import os
for variable in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[variable] = '1'

import gzip
import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy

from research_core.dependence_statistics import (
    InferenceError, RESTRICTIONS, holm_six, ols_hac, primary_design,
    wald_zero,
)

ROOT = Path(__file__).resolve().parents[2]
CONFIG = Path('research/experiments/ams_dep_synthetic_core_v1.json')
PLAN = Path('docs/AMS_DEP_SYNTHETIC_CALIBRATION_V1.md')
NUMERICAL = Path('docs/AMS_DEP_NUMERICAL_CONTRACT_V1.md')
SPEC_COMMIT = '2dd1543f654b5a605a902ce2b3cf98c70c9755b1'


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def metadata():
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    # Do not claim a committed numerical result for a modified tracked tree.
    subprocess.run(['git', 'diff', '--exit-code', 'HEAD', '--'], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    for path in (CONFIG, PLAN, NUMERICAL):
        original = subprocess.check_output(['git', 'show', f'{SPEC_COMMIT}:{path.as_posix()}'], cwd=ROOT)
        if original != (ROOT/path).read_bytes():
            raise RuntimeError(f'pre-result specification changed: {path}')
    sources = [Path(__file__).relative_to(ROOT), Path('src/research_core/dependence_statistics.py'), CONFIG, PLAN, NUMERICAL]
    for path in sources:
        committed = subprocess.check_output(['git', 'show', f'{sha}:{path.as_posix()}'], cwd=ROOT)
        if committed != (ROOT/path).read_bytes():
            raise RuntimeError(f'uncommitted source: {path}')
    if np.__version__ != '2.2.6' or scipy.__version__ != '1.15.3':
        raise RuntimeError('unregistered numerical dependency versions')
    return {'executing_commit': sha, 'specification_commit': SPEC_COMMIT,
            'file_sha256': {str(path): digest((ROOT/path).read_bytes()) for path in sources},
            'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__,
            'platform': platform.platform(), 'blas_threads': 1}


def calendar(config):
    n = config['observations_per_year']
    years = np.repeat(config['years'], n)
    states = np.tile(np.array(['LOW','NORMAL','HIGH'])[(np.arange(n)//config['state_block_hours'])%3], len(config['years']))
    hours = np.concatenate([int(datetime(y,1,1,tzinfo=timezone.utc).timestamp()//3600)+np.arange(n) for y in config['years']])
    segments = np.repeat(np.arange(len(config['years'])), n)
    return years, states, hours, segments


def simulate(case, replication, config):
    case_index = config['cases'].index(case)
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([config['seed'], case_index, replication])))
    xs, ys = [], []
    burn, n = config['burn_in'], config['observations_per_year']
    length = burn+n+1
    state_index = ((np.arange(length)-1-burn)//config['state_block_hours'])%3
    rho = config['asset_correlation']
    for year in config['years']:
        z = rng.standard_normal((length,2))
        z[:,1] = rho*z[:,0] + np.sqrt(1-rho*rho)*z[:,1]
        if case == 'bid_ask_bounce':
            errors = (2*rng.integers(0,2,size=(length+1,2))-1)*.005
            r = config['innovation_sd']*z + np.diff(errors,axis=0)
        elif case == 'iid_null':
            r = config['innovation_sd']*z
        elif case == 'heteroskedastic_null':
            r = np.array([.005,.01,.03])[state_index,None]*z
        else:
            r = np.empty_like(z)
            previous = np.zeros(2)
            variance = np.full(2,.0001)
            for j in range(length):
                phi = 0.
                sigma = config['innovation_sd']
                if case == 'stable_ar':
                    phi = .10
                elif case == 'time_ar':
                    phi = .15 if year in (2017,2019,2021) else -.15
                elif case == 'state_ar':
                    phi = (.15,0.,-.15)[state_index[j]]
                elif case == 'heteroskedastic_null':
                    sigma = (.005,.01,.03)[state_index[j]]
                elif case == 'garch_null':
                    variance = .000005 + .10*previous**2 + .85*variance
                    sigma = np.sqrt(variance)
                elif case != 'iid_null':
                    raise ValueError('unregistered simulation case')
                r[j] = phi*previous + sigma*z[j]
                previous = r[j]
        xs.append(r[burn:burn+n])
        ys.append(r[burn+1:burn+n+1])
    return np.concatenate(xs),np.concatenate(ys)


def wilson(count, total):
    z = 1.959963984540054
    rate = count/total
    denominator = 1+z*z/total
    center = (rate+z*z/(2*total))/denominator
    half = z*np.sqrt(rate*(1-rate)/total+z*z/(4*total*total))/denominator
    return {'count':count,'denominator':total,'rate':rate,'wilson_95':[max(0.,center-half),min(1.,center+half)]}


def summarize(case, rows, config):
    n = len(rows)
    reject_rates = {slot:wilson(sum(r['tests'][i]['reject'] for r in rows),n)
                    for i,slot in enumerate(('BTC_DEP','BTC_TIME','BTC_STATE','ETH_DEP','ETH_TIME','ETH_STATE'))}
    null_slots = {'iid_null':range(6),'heteroskedastic_null':range(6),'garch_null':range(6),
                  'stable_ar':(1,2,4,5),'time_ar':(2,5),'state_ar':(1,4)}
    invalid = wilson(sum(any(not t['available'] for t in r['tests']) for r in rows),n)
    # Invalid fraction uses replicates with any invalid fit, conservatively.
    screen = invalid['rate'] <= config['invalid_fraction_upper_bound']
    null_rate = None
    if case in null_slots:
        null_rate = wilson(sum(any(r['tests'][i]['reject'] for i in null_slots[case]) for r in rows),n)
        screen &= null_rate['rate'] <= config['null_fwer_upper_bound']
    targets = {'stable_ar':('BTC_DEP','ETH_DEP'),'time_ar':('BTC_TIME','ETH_TIME'),
               'state_ar':('BTC_STATE','ETH_STATE')}.get(case,())
    for slot in targets:
        screen &= reject_rates[slot]['rate'] >= config['power_lower_bound']
    return {'rejection_rates':reject_rates,'invalid_replicates':invalid,'false_rejection_any_true_null':null_rate,
            'power_screen_slots':list(targets),'engineering_screen_pass':bool(screen),
            'interpretation':'MEASUREMENT_EFFECT_NOT_TRADING_EDGE' if case=='bid_ask_bounce' else 'SYNTHETIC_ONLY'}


def main():
    meta = metadata()
    config = json.loads((ROOT/CONFIG).read_text())
    years,states,hours,segments = calendar(config)
    all_rows, summaries = [], {}
    for case in config['cases']:
        rows = []
        for replication in range(config['replications']):
            x,y = simulate(case,replication,config)
            ps,errors = [],[]
            for asset in range(2):
                try:
                    fit = ols_hac(primary_design(x[:,asset],years,states),y[:,asset],hours,segments,config['hac_lags'])
                    tests = [wald_zero(fit,RESTRICTIONS[name]) for name in ('DEP','TIME','STATE')]
                    ps.extend(t['p_value'] for t in tests)
                    errors.append(None)
                except (InferenceError,np.linalg.LinAlgError) as exc:
                    ps.extend([None]*3)
                    errors.append(str(exc))
            row={'case':case,'replication':replication,'tests':holm_six(ps),'errors':errors}
            rows.append(row)
            if (replication+1)%100==0:
                print(f'{case}: {replication+1}/{config["replications"]}',flush=True)
        summaries[case]=summarize(case,rows,config)
        all_rows.extend(rows)
        print(json.dumps({'case':case,'summary':summaries[case]},sort_keys=True),flush=True)
    out = ROOT/'research/experiments/ams_dep_synthetic_core_v1_results'
    out.mkdir(exist_ok=True)
    ledger = b''.join((json.dumps(row,sort_keys=True,allow_nan=False)+'\n').encode() for row in all_rows)
    compressed = gzip.compress(ledger,mtime=0)
    (out/'replicates.jsonl.gz').write_bytes(compressed)
    report={'classification':'SYNTHETIC_NUMERICAL_CALIBRATION_NOT_MARKET_EVIDENCE',
            'market_data_accessed':False,'validation_or_oos_accessed':False,'empirical_release_authorized':False,
            'scope':'fixed exogenous states; not full AMS-V1 pipeline calibration',
            'config':config,'provenance':meta,'replicate_ledger_sha256':digest(compressed),
            'replicate_ledger_uncompressed_sha256':digest(ledger),'replicate_count':len(all_rows),
            'cases':summaries,'engineering_screen_pass':all(v['engineering_screen_pass'] for v in summaries.values())}
    (out/'summary.json').write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n')
    print('SYNTHETIC CORE SCREEN: '+('PASS' if report['engineering_screen_pass'] else 'FAIL'),flush=True)


if __name__=='__main__':
    main()
