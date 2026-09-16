from __future__ import annotations

import json
import os
from decimal import Decimal
from pathlib import Path

from tests.gate2_next_cycle_experiments import (
    START, END, FEE_GRID, DELAYS, months, fetch, parse_valid_bars,
    continuous_segments, event_return, concentration_and_dd, sha256_file,
)
from research_core.data_ingestion import archive_url, checksum_url, verify_sha256_bytes
from research_core.data_quality import scan_archive
from research_core.data_quality_treatment_v2 import build_manifest

PREREG = Path('docs/GATE2_CYCLE2_PREREGISTRATION_V1.md')
ROOT = Path(__file__).resolve().parents[1]
GRID = {
 'HYP-0008': {'lookback':[24,48], 'multiplier':[Decimal('2'),Decimal('3'),Decimal('4')], 'threshold':[Decimal('0.01'),Decimal('0.015'),Decimal('0.02')]},
 'HYP-0009': {'compression':[Decimal('0.5'),Decimal('0.7'),Decimal('0.9')], 'breakout_lookback':[12,24], 'breakout':[Decimal('0.001'),Decimal('0.005'),Decimal('0.01')]},
 'HYP-0010': {'selloff':[Decimal('0.005'),Decimal('0.01'),Decimal('0.015')], 'volume_multiplier':[Decimal('0'),Decimal('1'),Decimal('1.5')]},
}
BASE = {
 'HYP-0008': {'lookback':24,'multiplier':Decimal('3'),'threshold':Decimal('0.015')},
 'HYP-0009': {'compression':Decimal('0.7'),'breakout_lookback':12,'breakout':Decimal('0.005')},
 'HYP-0010': {'selloff':Decimal('0.01'),'volume_multiplier':Decimal('0')},
}

def cartesian(grid):
 keys=list(grid)
 def rec(i,cur):
  if i==len(keys): yield dict(cur); return
  for v in grid[keys[i]]:
   cur[keys[i]]=v; yield from rec(i+1,cur)
 yield from rec(0,{})

def ret(bars,i): return bars[i].close/bars[i-1].close-1

def abs_median_previous(bars,i,n):
 if i<n+1: return None
 vals=sorted(abs(ret(bars,j)) for j in range(i-n,i)); m=len(vals)//2
 return vals[m] if len(vals)%2 else (vals[m-1]+vals[m])/2

def volume_median_previous(bars,i,n):
 if i<n: return None
 vals=sorted(b.volume for b in bars[i-n:i]); m=len(vals)//2
 return vals[m] if len(vals)%2 else (vals[m-1]+vals[m])/2

def realized_previous(bars,i,n):
 if i<n+1: return None
 vals=[abs(ret(bars,j)) for j in range(i-n,i)]
 return sum(vals,Decimal('0'))/Decimal(len(vals))

def event_condition(hyp,i,bars,p):
 if hyp=='HYP-0008':
  if i<4: return False
  base=abs_median_previous(bars,i,p['lookback'])
  if base is None or base<=0: return False
  four=bars[i].close/bars[i-4].close-1
  return four>=p['threshold'] and four>=p['multiplier']*base
 if hyp=='HYP-0009':
  if i<48: return False
  current=realized_previous(bars,i,12)
  history=[realized_previous(bars,j,12) for j in range(i-48,i)]
  if current is None or any(x is None for x in history): return False
  history=sorted(history); m=len(history)//2
  med=history[m] if len(history)%2 else (history[m-1]+history[m])/2
  prior=max(b.close for b in bars[i-p['breakout_lookback']:i])
  return current<=p['compression']*med and bars[i].close>=prior*(Decimal('1')+p['breakout'])
 if hyp=='HYP-0010':
  if i<2: return False
  r1=ret(bars,i-1); r2=ret(bars,i)
  if r1>-p['selloff'] or r2>-p['selloff'] or bars[i].close<=bars[i].open: return False
  v=p['volume_multiplier']
  if v==0: return True
  base=volume_median_previous(bars,i,24)
  return base is not None and bars[i].volume>=v*base
 raise ValueError(hyp)

def simulate(bars,hyp,p,fee,slip,delay):
 if delay not in DELAYS: raise ValueError('delay must be 1 or 2')
 events=[]; i=1
 while i+delay<len(bars):
  if event_condition(hyp,i,bars,p):
   entry=i+delay
   r=event_return(bars[entry],bars[entry],fee,slip)
   events.append({'signal_index':i,'entry_index':entry,'exit_index':entry,'signal_timestamp':bars[i].timestamp.isoformat(),'entry_timestamp':bars[entry].timestamp.isoformat(),'return':str(r)})
   i=entry+1
  else: i+=1
 return events

def compound(rs):
 g=Decimal('1')
 for r in rs: g*=Decimal('1')+r
 return g-1

def summary(details):
 valid=[d for d in details if d['aggregate'] and d['aggregate']['events']]
 ev=[Decimal(e['return']) for d in valid for e in d['events']]
 seg=[Decimal(d['aggregate']['compound_return']) for d in valid]
 return {'events':len(ev),'compound_return':str(compound(ev)),'mean_event_return':str(sum(ev,Decimal('0'))/Decimal(len(ev))) if ev else '0','positive_event_fraction':str(Decimal(sum(x>0 for x in ev))/Decimal(len(ev))) if ev else '0','mean_segment_return':str(sum(seg,Decimal('0'))/Decimal(len(seg))) if seg else '0','eligible_segments':len(valid)}

def detail_segments(segments,hyp,p,fee,slip,delay):
 out=[]
 for idx,seg in enumerate(segments):
  try:
   ev=simulate(seg,hyp,p,fee,slip,delay)
   out.append({'segment':idx,'aggregate':{'events':len(ev),'compound_return':str(compound([Decimal(x['return']) for x in ev]))},'events':ev,'error':None})
  except Exception as exc:
   out.append({'segment':idx,'aggregate':None,'events':[],'error':f'{type(exc).__name__}: {exc}'})
 return out

def regime(detail,segments):
 out={'bull':[],'neutral':[],'bear':[]}
 for d,seg in zip(detail,segments):
  for e in d['events']:
   i=e['signal_index']
   if i<168: continue
   r=seg[i].close/seg[i-168].close-1
   k='bull' if r>Decimal('0.10') else 'bear' if r<Decimal('-0.10') else 'neutral'
   out[k].append(Decimal(e['return']))
 return {k:{'events':len(v),'compound_return':str(compound(v)) if v else '0','mean_return':str(sum(v,Decimal('0'))/Decimal(len(v))) if v else '0'} for k,v in out.items()}

def loo(detail):
 vals=[Decimal(d['aggregate']['compound_return']) for d in detail if d['aggregate'] and d['aggregate']['events']]
 return {'segments_used':len(vals),'leave_one_out_min_compound':str(min((compound([x for j,x in enumerate(vals) if j!=i]) for i in range(len(vals)) if len(vals)>1),default=Decimal('0')))}

def benchmark(segments,fee,slip):
 bh=[]
 for seg in segments:
  if len(seg)<2: continue
  buy=seg[0].open*(Decimal('1')+slip); sell=seg[-1].close*(Decimal('1')-slip)
  bh.append((sell/buy-1+Decimal('1'))*(Decimal('1')-fee)*(Decimal('1')-fee)-1)
 return {'cash_compound_return':'0','buy_hold_compound_return':str(compound(bh)) if bh else '0','eligible_segments':len(bh)}

def main():
 report={'experiment_version':'gate2-cycle2-v1','code_commit':os.environ.get('GITHUB_SHA','UNKNOWN'),'preregistration':{'path':str(PREREG),'sha256':sha256_file(ROOT/PREREG)},'development_window':[START.isoformat(),END.isoformat()],'validation_or_oos_accessed':False,'registered_parameter_cell_count':54,'assets':{},'decision':'UNASSESSED'}
 import tempfile
 with tempfile.TemporaryDirectory(prefix='gate2-cycle2-') as td:
  root=Path(td); loaded={}
  for symbol in ('BTCUSDT','ETHUSDT'):
   scans=[]; paths=[]
   for y,m in months(START,END):
    url=archive_url(symbol,y,m); payload=fetch(url); checksum=fetch(checksum_url(url)).decode()
    if not verify_sha256_bytes(payload,checksum): raise RuntimeError('checksum mismatch')
    path=root/symbol/Path(url).name; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(payload); scans.append(scan_archive(path,symbol,True)); paths.append(path)
   manifest=build_manifest(symbol,scans,START,END); bars=[]
   for path,scan in zip(paths,scans): bars.extend(parse_valid_bars(path,symbol,set(scan.valid_timestamps)))
   bars.sort(key=lambda b:b.timestamp); loaded[symbol]={'manifest':manifest,'bars':bars,'segments':continuous_segments(bars,manifest.continuity_breaks)}
  for symbol,asset in loaded.items():
   segs=asset['segments']; ad={'dataset_identity':asset['manifest'].dataset_identity,'source_integrity':asset['manifest'].source_integrity,'certification':asset['manifest'].research_certification,'parameter_cells':{},'fee_slippage':{},'timing':{},'regime':{},'leave_one_segment_out':{},'concentration_drawdown':{},'benchmarks':benchmark(segs,Decimal('0.001'),Decimal('0.0005'))}
   for hyp in GRID:
    plist=list(cartesian(GRID[hyp])); ad['parameter_cells'][hyp]=[]
    for n,p in enumerate(plist):
     det=detail_segments(segs,hyp,p,Decimal('0.001'),Decimal('0.0005'),1)
     ad['parameter_cells'][hyp].append({'cell':f'parameter_{n:03d}','params':{k:str(v) for k,v in p.items()},'summary':summary(det),'errors':[d['error'] for d in det if d['error']]})
    bp=BASE[hyp]; base_detail=detail_segments(segs,hyp,bp,Decimal('0.001'),Decimal('0.0005'),1)
    ad['regime'][hyp]=regime(base_detail,segs); ad['leave_one_segment_out'][hyp]=loo(base_detail); ad['concentration_drawdown'][hyp]=concentration_and_dd(base_detail); ad['fee_slippage'][hyp]=[]
    for label,fee,slip in FEE_GRID:
     ad['fee_slippage'][hyp].append({'fee_case':label,'commission':str(fee),'slippage':str(slip),'summary':summary(detail_segments(segs,hyp,bp,fee,slip,1))})
    ad['timing'][hyp]=[{'delay_bars':delay,'summary':summary(detail_segments(segs,hyp,bp,Decimal('0.001'),Decimal('0.0005'),delay))} for delay in DELAYS]
   report['assets'][symbol]=ad
 out=Path('gate2_cycle2_results'); out.mkdir(exist_ok=True); (out/'cycle2_results.json').write_text(json.dumps(report,separators=(',',':'))); print('Gate 2 Cycle 2 evidence generated')

if __name__=='__main__': main()
