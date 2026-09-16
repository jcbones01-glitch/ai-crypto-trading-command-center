from datetime import datetime, timedelta, timezone
from decimal import Decimal
from research_core.data_interfaces import MarketBar
from tests.gate2_cycle6_experiments import GRID, BASE, cartesian, condition, location

def bar(ts,o,h,l,c,v=100): return MarketBar(ts,'BTC/USDT',Decimal(str(o)),Decimal(str(h)),Decimal(str(l)),Decimal(str(c)),Decimal(str(v)))

def test_cycle6_registered_cells():
    assert len(list(cartesian(GRID['HYP-0020']))) == 20
    assert len(list(cartesian(GRID['HYP-0021']))) == 8
    assert len(list(cartesian(GRID['HYP-0022']))) == 12
    assert sum(len(list(cartesian(x))) for x in GRID.values()) == 40

def test_hour_condition_satisfiable():
    t=datetime(2021,1,1,0,tzinfo=timezone.utc)
    b=[bar(t,100,101,99,100),bar(t+timedelta(hours=1),100,101,99,100),bar(t+timedelta(hours=24),100,102,99,101)]
    assert condition('HYP-0020',2,b,BASE['HYP-0020'])

def test_streak_exhaustion_uses_previous_completed_returns():
    t=datetime(2021,1,1,tzinfo=timezone.utc)
    b=[bar(t+timedelta(hours=i),100+i,101+i,99+i,100+i+0.4) for i in range(5)]
    assert condition('HYP-0021',4,b,BASE['HYP-0021'])

def test_body_dominance_uses_body_return_threshold():
    t=datetime(2021,1,1,tzinfo=timezone.utc)
    b=[bar(t,100,100,99,100),bar(t+timedelta(hours=1),100,102,99.5,101)]
    assert condition('HYP-0022',1,b,BASE['HYP-0022'])
    p=dict(BASE['HYP-0022']); p['body_return']=Decimal('.02')
    assert not condition('HYP-0022',1,b,p)

def test_close_location_bounded():
    t=datetime(2021,1,1,tzinfo=timezone.utc); b=bar(t,100,110,90,105)
    assert location(b)==Decimal('.75')

def test_cycle6_baselines_frozen():
    assert BASE['HYP-0020']=={'hour':0,'threshold':Decimal('.005'),'location':Decimal('.90')}
    assert BASE['HYP-0021']=={'k':3,'threshold':Decimal('.005'),'location':Decimal('.50')}
    assert BASE['HYP-0022']=={'body_ratio':Decimal('.60'),'range_ratio':Decimal('.005'),'body_return':Decimal('.0025')}
