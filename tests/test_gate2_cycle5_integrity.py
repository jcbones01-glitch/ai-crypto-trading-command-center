from datetime import datetime, timedelta, timezone
from decimal import Decimal
from research_core.data_interfaces import MarketBar
from tests.gate2_cycle5_experiments import GRID, BASE, cartesian, condition, location

def bar(ts,o,h,l,c,v=100): return MarketBar(ts,'BTC/USDT',Decimal(str(o)),Decimal(str(h)),Decimal(str(l)),Decimal(str(c)),Decimal(str(v)))

def test_cycle5_registered_cells():
    assert len(list(cartesian(GRID['HYP-0017']))) == 6
    assert len(list(cartesian(GRID['HYP-0018']))) == 6
    assert len(list(cartesian(GRID['HYP-0019']))) == 16
    assert sum(len(list(cartesian(x))) for x in GRID.values()) == 28

def test_gap_continuation_predicate_satisfiable():
    t=datetime(2021,1,1,tzinfo=timezone.utc)
    b=[bar(t,100,101,99,100),bar(t+timedelta(hours=1),100.6,102,100,101.8)]
    assert condition('HYP-0017',1,b,BASE['HYP-0017'])

def test_three_bar_persistence_predicate_satisfiable():
    t=datetime(2021,1,1,tzinfo=timezone.utc)
    b=[bar(t,100,101,99,100),bar(t+timedelta(hours=1),100,101.5,99.9,100.4),bar(t+timedelta(hours=2),100.4,102,100.3,101),bar(t+timedelta(hours=3),101,103,100.8,102.2)]
    assert condition('HYP-0018',3,b,BASE['HYP-0018'])

def test_low_volume_breakout_predicate_satisfiable():
    t=datetime(2021,1,1,tzinfo=timezone.utc)
    b=[bar(t+timedelta(hours=i),100,101,99,100,100) for i in range(24)]
    b[23]=bar(t+timedelta(hours=23),100,101.5,99.5,101,100)
    b.append(bar(t+timedelta(hours=24),101,103,100.5,101.4,50))
    assert condition('HYP-0019',24,b,BASE['HYP-0019'])

def test_close_location_bounded():
    t=datetime(2021,1,1,tzinfo=timezone.utc); b=bar(t,100,110,90,105)
    assert location(b) == Decimal('.75')

def test_cycle5_baselines_frozen():
    assert BASE['HYP-0017']=={'gap':Decimal('.005'),'location':Decimal('.90')}
    assert BASE['HYP-0018']=={'threshold':Decimal('.01'),'location':Decimal('.90')}
    assert BASE['HYP-0019']=={'lookback':24,'breakout':Decimal('.0025'),'volume_cap':Decimal('.75'),'location':Decimal('.90')}
