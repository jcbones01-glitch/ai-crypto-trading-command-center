from datetime import datetime, timedelta, timezone
from decimal import Decimal
from research_core.data_interfaces import MarketBar
from tests.gate2_cycle4_experiments import GRID, BASE, cartesian, condition, location, volume_ratio

def bar(ts,o,h,l,c,v=100): return MarketBar(ts,'BTC/USDT',Decimal(str(o)),Decimal(str(h)),Decimal(str(l)),Decimal(str(c)),Decimal(str(v)))

def test_cycle4_registered_cells():
    assert len(list(cartesian(GRID['HYP-0014']))) == 6
    assert len(list(cartesian(GRID['HYP-0015']))) == 12
    assert len(list(cartesian(GRID['HYP-0016']))) == 8
    assert sum(len(list(cartesian(x))) for x in GRID.values()) == 26

def test_inside_breakout_predicate_satisfiable():
    t=datetime(2021,1,1,tzinfo=timezone.utc)
    b=[bar(t,100,105,95,100),bar(t+timedelta(hours=1),100,103,98,101),bar(t+timedelta(hours=2),101,106,100,105.5)]
    assert condition('HYP-0014',2,b,BASE['HYP-0014'])

def test_volume_confirmation_uses_completed_history():
    t=datetime(2021,1,1,tzinfo=timezone.utc)
    b=[bar(t+timedelta(hours=i),100,101,99,100,10) for i in range(24)]
    b += [bar(t+timedelta(hours=24),100,102,99,101,30)]
    assert volume_ratio(b,24,24) == Decimal('3')

def test_weekend_predicate_satisfiable():
    t=datetime(2021,9,4,0,tzinfo=timezone.utc)  # Saturday
    b=[bar(t+timedelta(hours=i),100,101,99,100) for i in range(9)]
    b[4]=bar(t+timedelta(hours=4),100,101,99,101)
    b[8]=bar(t+timedelta(hours=8),103,105,102,104.5)
    assert b[8].timestamp.weekday()==5
    assert condition('HYP-0016',8,b,BASE['HYP-0016'])

def test_close_location_bounded():
    t=datetime(2021,1,1,tzinfo=timezone.utc); b=bar(t,100,110,90,105)
    assert location(b) == Decimal('.75')

def test_cycle4_baselines_frozen():
    assert BASE['HYP-0014']=={'breakout':Decimal('.0025'),'location':Decimal('.85')}
    assert BASE['HYP-0015']=={'lookback':24,'volume_multiplier':Decimal('2.5'),'location':Decimal('.90')}
    assert BASE['HYP-0016']=={'weekday':5,'trend_threshold':Decimal('.005'),'location':Decimal('.90')}
