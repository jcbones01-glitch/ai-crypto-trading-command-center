"""Bounded deterministic engineering fixture; never a calibration DGP run."""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[name]='1'
import json
import hashlib
import subprocess
import platform
import time
from pathlib import Path
import numpy as np
import scipy
from research_core.dependence_statistics import primary_design
from research_core.dependent_wild_bootstrap_v2 import engineering_fixture


def main():
    if (platform.python_version(),np.__version__,scipy.__version__) != ('3.12.14','2.2.6','1.15.3'):
        raise RuntimeError('unregistered engineering environment')
    n_per_year=2000
    n=5*n_per_year
    t=np.arange(n,dtype=float)
    x=.01*(np.sin(t*np.sqrt(2))+.3*np.cos(t*np.sqrt(3)))
    y=.01*np.cos(t*np.sqrt(5))+.15*x
    years=np.repeat(np.arange(2017,2022),n_per_year)
    states=np.array(['LOW','NORMAL','HIGH'])[(np.arange(n)//37)%3]
    hours=np.concatenate([np.arange(n_per_year)+k*10000 for k in range(5)])
    segments=np.repeat(np.arange(5),n_per_year)
    start=time.perf_counter()
    result=engineering_fixture(primary_design(x,years,states),y,hours,segments,'DEP',draws=8)
    elapsed=time.perf_counter()-start
    upper_draws=11*2000*6*4999
    out={'executing_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
         'source_sha256':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ('src/research_core/dependent_wild_bootstrap_v2.py','research/scripts/check_ams_dep_v2_engineering.py')},
         'classification':'DETERMINISTIC_ENGINEERING_RESOURCE_CHECK_NOT_CALIBRATION',
         'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,
         'blas_threads':1,'rows':n,'fixture_draws':8,'wall_seconds_including_setup':elapsed,
         'calibration_draws_if_11_cases_all_six_slots':upper_draws,
         'linear_serial_hours_including_repeated_setup':elapsed/8*upper_draws/3600,
         'estimate_caveat':'Rough upper workload estimate, not measured calibration runtime; includes setup, ignores batching/sharding and machine variation.',
         'engineering':result,'calibration_run':False,'market_data_accessed':False,
         'validation_or_oos_accessed':False}
    path=Path('research/experiments/ams_dep_v2_engineering_resource_check.json')
    path.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out,indent=2))


if __name__=='__main__': main()
