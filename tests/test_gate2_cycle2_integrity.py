from datetime import datetime, timedelta, timezone
from decimal import Decimal

from research_core.data_interfaces import MarketBar
from tests.gate2_cycle2_experiments import BASE, GRID, cartesian, event_condition, volume_median_previous


def bar(ts, close, open_=None, volume=100):
    v=Decimal(str(close)); o=v if open_ is None else Decimal(str(open_))
    return MarketBar(ts, 'BTC/USDT', o, v, v, v, Decimal(str(volume)))


def test_cycle2_registered_parameter_cells():
    assert len(list(cartesian(GRID['HYP-0008']))) == 18
    assert len(list(cartesian(GRID['HYP-0009']))) == 27
    assert len(list(cartesian(GRID['HYP-0010']))) == 9
    assert sum(len(list(cartesian(GRID[h]))) for h in GRID) == 54


def test_volume_median_uses_only_previous_completed_bars():
    ts=datetime(2021,1,1,tzinfo=timezone.utc)
    bars=[bar(ts+timedelta(hours=i),100,volume=100) for i in range(24)]
    bars.append(bar(ts+timedelta(hours=24),100,volume=10000))
    assert volume_median_previous(bars,24,24) == Decimal('100')


def test_hyp0010_volume_filter_is_registered_semantics():
    ts=datetime(2021,1,1,tzinfo=timezone.utc)
    bars=[bar(ts+timedelta(hours=i),100,volume=100) for i in range(24)]
    bars += [bar(ts+timedelta(hours=24),98,open_=99,volume=200),bar(ts+timedelta(hours=25),96,open_=95,volume=200)]
    assert event_condition('HYP-0010',25,bars,{'selloff':Decimal('0.01'),'volume_multiplier':Decimal('1')})
    assert not event_condition('HYP-0010',25,bars,{'selloff':Decimal('0.01'),'volume_multiplier':Decimal('1.5')})


def test_cycle2_baselines_are_frozen():
    assert BASE['HYP-0008'] == {'lookback':24,'multiplier':Decimal('3'),'threshold':Decimal('0.015')}
    assert BASE['HYP-0009'] == {'compression':Decimal('0.7'),'breakout_lookback':12,'breakout':Decimal('0.005')}
    assert BASE['HYP-0010'] == {'selloff':Decimal('0.01'),'volume_multiplier':Decimal('0')}
