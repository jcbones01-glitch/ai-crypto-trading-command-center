from __future__ import annotations
import json, os, sys, tempfile
from decimal import Decimal
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate2_next_cycle_experiments import START, END, FEE_GRID, DELAYS, months, fetch, parse_valid_bars, continuous_segments, event_return, concentration_and_dd, sha256_file
from research_core.data_ingestion import archive_url, checksum_url, verify_sha256_bytes
from research_core.data_quality import scan_archive
from research_core.data_quality_treatment_v2 import build_manifest

PREREG=Path('docs/GATE2_CYCLE3_PREREGISTRATION_V1.md'); ROOT=Path(__file__).resolve().parents[1]
GRID={
'HYP-0011':{'selloff':[Decimal('.005'),Decimal('.01'),Decimal('.015')],'location':[Decimal('.75'),Decimal('.85'),Decimal('.95')]},
'HYP-0012':{'lookback':[24,48],'multiplier':[Decimal('2'),Decimal('3'),Decimal('4')],'location':[Decimal('.75'),Decimal('.85')]},
'HYP-0013':{'pullback':[Decimal('.005'),Decimal('.01'),Decimal('.015')],'trend_lookback':[24,48],'location':[Decimal('.5'),Decimal('.7')]},}
BASE={'HYP-0011':{'selloff':Decimal('.01'),'location':Decimal('.85')},'HYP-0012':{'lookback':24,'multiplier':Decimal('3'),'location':Decimal('.85')},'HYP-0013':{'pullback':Decimal('.01'),'trend_lookback':24,'location':Decimal('.7')}}

def cartesian(g):
 keys=list(g)
 def rec(i,c):
  if i==len(keys): yield dict(c); return
  for v in g[keys[i]]:
   c[keys[i]]=v; yield from rec(i+1,c)
 yield from rec(0,{})

def ret(b,i): return b[i].close/b[i-1].close-1

def median(v):
 v=sorted(v); n=len(v); return v[n//2] if n%2 else (v[n//2-1]+v[n//2])/2

def location(b):
 r=b.high-b.low
 return Decimal('0') if r<=0 else (b.close-b.low)/r

def range_ratio(b,i,n):
 if i<n: return None
 hist=[(b[j].high-b[j].low)/b[j-1].close for j in range(i-n,i)]
 return (b[i].high-b[i].low)/b[i-1].close / median(hist) if hist and median(hist)>0 else None

def condition(h,i,b,p):
 if h=='HYP-0011':
  return i>=1 and ret(b,i-1)<=-p['selloff'] and b[i].close>b[i].open and location(b[i])>=p['location']
 if h=='HYP-0012':
  rr=range_ratio(b,i,p['lookback'])
  return rr is not None and rr>=p['multiplier'] and location(b[i])>=p['location']
 if h=='HYP-0013':
  n=p['trend_lookback']
  return i>=n+1 and b[i-1].close/b[i-n].close-1>0 and ret(b,i-1)<=-p['pullback'] and b[i].close>b[i].open and b[i].close>b[i-n].close and location(b[i])>=p['location']
 raise ValueError(h)

def simulate(seg,h,p,fee,slip,delay):
 events=[]; i=1
 while i+delay<len(seg):
  if condition(h,i,seg,p):
   e=i+delay; r=event_return(seg[e],seg[e],fee,slip)
   events.append({'signal_index':i,'entry_index':e,'exit_index':e,'signal_timestamp':seg[i].timestamp.isoformat(),'entry_timestamp':seg[e].timestamp.isoformat(),'return':str(r)})
   i=e+1
  else: i+=1
 return events

def compound(rs):
 g=Decimal('1')
 for r in rs:g*=Decimal('1')+r
 return g-1

def detail(segs,h,p,fee,slip,delay):
 out=[]
 for i,s in enumerate(segs):
  try:
   ev=simulate(s,h,p,fee,slip,delay); rs=[Decimal(x['return']) for x in ev]
   out.append({'segment':i,'aggregate':{'events':len(ev),'compound_return':str(compound(rs))},'events':ev,'error':None})
  except Exception as e: out.append({'segment':i,'aggregate':None,'events':[],'error':f'{type(e).__name__}: {e}'})
 return out

def summarize(ds):
 valid=[d for d in ds if d['aggregate'] and d['aggregate']['events']]; ev=[Decimal(e['return']) for d in valid for e in d['events']]; sr=[Decimal(d['aggregate']['compound_return']) for d in valid]
 return {'events':len(ev),'compound_return':str(compound(ev)),'mean_event_return':str(sum(ev,Decimal('0'))/Decimal(len(ev))) if ev else '0','positive_event_fraction':str(Decimal(sum(x>0 for x in ev))/Decimal(len(ev))) if ev else '0','mean_segment_return':str(sum(sr,Decimal('0'))/Decimal(len(sr))) if sr else '0','eligible_segments':len(valid)}

def regime(ds,segs):
 r={'bull':[],'neutral':[],'bear':[]}
 for d,s in zip(ds,segs):
  for e in d['events']:
   i=e['signal_index']
   if i<168: continue
   x=s[i].close/s[i-168].close-1; k='bull' if x>Decimal('.10') else 'bear' if x<Decimal('-.10') else 'neutral'; r[k].append(Decimal(e['return']))
 return {k:{'events':len(v),'compound_return':str(compound(v)) if v else '0','mean_return':str(sum(v,Decimal('0'))/Decimal(len(v))) if v else '0'} for k,v in r.items()}

def loo(ds):
 vals=[Decimal(d['aggregate']['compound_return']) for d in ds if d['aggregate'] and d['aggregate']['events']]
 return {'segments_used':len(vals),'leave_one_out_min_compound':str(min((compound([x for j,x in enumerate(vals) if j!=i]) for i in range(len(vals)) if len(vals)>1),default=Decimal('0')))}

def benchmark(segs,fee,slip):
 rs=[]
 for s in segs:
  if len(s)>1:
   buy=s[0].open*(1+slip); sell=s[-1].close*(1-slip); rs.append(sell/buy*(1-fee)*(1-fee)-1)
 return {'cash_compound_return':'0','buy_hold_compound_return':str(compound(rs)) if rs else '0','eligible_segments':len(rs)}

def main():
 cells=sum(len(list(cartesian(g))) for g in GRID.values())
 if cells!=33: raise RuntimeError(cells)
 report={'experiment_version':'gate2-cycle3-v1','github_sha':os.environ.get('GITHUB_SHA','UNKNOWN'),'checked_out_sha':os.environ.get('CHECKED_OUT_SHA','UNKNOWN'),'preregistration':{'path':str(PREREG),'sha256':sha256_file(ROOT/PREREG)},'development_window':[START.isoformat(),END.isoformat()],'validation_or_oos_accessed':False,'registered_parameter_cell_count':cells,'assets':{},'decision':'UNASSESSED'}
 with tempfile.TemporaryDirectory(prefix='gate2-cycle3-') as td:
  root=Path(td); loaded={}
  for sym in ('BTCUSDT','ETHUSDT'):
   scans=[]; paths=[]
   for y,m in months(START,END):
    u=archive_url(sym,y,m); payload=fetch(u); checksum=fetch(checksum_url(u)).decode()
    if not verify_sha256_bytes(payload,checksum): raise RuntimeError('checksum mismatch')
    p=root/sym/Path(u).name; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(payload); scans.append(scan_archive(p,sym,True)); paths.append(p)
   man=build_manifest(sym,scans,START,END); bars=[]
   for p,s in zip(paths,scans): bars.extend(parse_valid_bars(p,sym,set(s.valid_timestamps)))
   bars.sort(key=lambda x:x.timestamp); loaded[sym]={'manifest':man,'segments':continuous_segments(bars,man.continuity_breaks)}
  for sym,a in loaded.items():
   segs=a['segments']; out={'dataset_identity':a['manifest'].dataset_identity,'source_integrity':a['manifest'].source_integrity,'certification':a['manifest'].research_certification,'parameter_cells':{},'fee_slippage':{},'timing':{},'regime':{},'leave_one_segment_out':{},'concentration_drawdown':{},'benchmarks':benchmark(segs,Decimal('.001'),Decimal('.0005'))}
   for h,g in GRID.items():
    out['parameter_cells'][h]=[]
    for n,p in enumerate(cartesian(g)):
     ds=detail(segs,h,p,Decimal('.001'),Decimal('.0005'),1); out['parameter_cells'][h].append({'cell':f'parameter_{n:03d}','params':{k:str(v) for k,v in p.items()},'summary':summarize(ds),'errors':[d['error'] for d in ds if d['error']]})
     if p==BASE[h]:
      out['regime'][h]=regime(ds,segs); out['leave_one_segment_out'][h]=loo(ds); out['concentration_drawdown'][h]=concentration_and_dd(ds); out['fee_slippage'][h]=[]
      for label,fee,slip in FEE_GRID: out['fee_slippage'][h].append({'fee_case':label,'commission':str(fee),'slippage':str(slip),'summary':summarize(detail(segs,h,p,fee,slip,1))})
      out['timing'][h]=[{'delay_bars':d,'summary':summarize(detail(segs,h,p,Decimal('.001'),Decimal('.0005'),d))} for d in DELAYS]
   report['assets'][sym]=out
 out=Path('gate2_cycle3_results'); out.mkdir(exist_ok=True); (out/'cycle3_results.json').write_text(json.dumps(report,indent=2,sort_keys=True)); print('Gate 2 Cycle 3 evidence generated')
if __name__=='__main__': main()
