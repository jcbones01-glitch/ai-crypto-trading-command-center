from datetime import datetime, timedelta, timezone
from decimal import Decimal
from research_core.data_interfaces import MarketBar
from tests.gate2_cycle3_experiments import GRID, BASE, cartesian, condition, location

def bar(ts,o,h,l,c): return MarketBar(ts,'BTC/USDT',Decimal(str(o)),Decimal(str(h)),Decimal(str(l)),Decimal(str(c)),Decimal('100'))

def test_cycle3_registered_cells():
    assert len(list(cartesian(GRID['HYP-0011']))) == 9
    assert len(list(cartesian(GRID['HYP-0012']))) == 12
    assert len(list(cartesian(GRID['HYP-0013']))) == 12
    assert sum(len(list(cartesian(x))) for x in GRID.values()) == 33

def test_recovery_predicates_are_satisfiable():
    t=datetime(2021,1,1,tzinfo=timezone.utc)
    b=[bar(t,100,101,99,100),bar(t+timedelta(hours=1),100,101,95,96),bar(t+timedelta(hours=2),96,101,95,100)]
    assert condition('HYP-0011',2,b,BASE['HYP-0011'])
    assert b[2].close > b[2].open

def test_close_location_bounded():
    t=datetime(2021,1,1,tzinfo=timezone.utc); b=bar(t,100,110,90,105)
    assert location(b) == Decimal('.75')

def test_cycle3_baselines_frozen():
    assert BASE['HYP-0011']=={'selloff':Decimal('.01'),'location':Decimal('.85')}
    assert BASE['HYP-0012']=={'lookback':24,'multiplier':Decimal('3'),'location':Decimal('.85')}
    assert BASE['HYP-0013']=={'pullback':Decimal('.01'),'trend_lookback':24,'location':Decimal('.7')}
