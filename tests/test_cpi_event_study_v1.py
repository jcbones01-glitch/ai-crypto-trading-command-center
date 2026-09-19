from datetime import timedelta
from decimal import Decimal
import json
import pytest
from research.scripts import run_cpi_event_study_v1 as mod
from tests.test_fomc_event_study_v1 import T0, bar


def test_anchor_never_includes_pre_release_half_hour():
    assert mod.hourly_anchor(T0+timedelta(minutes=30)) == T0+timedelta(hours=1)
    with pytest.raises(ValueError):
        mod.hourly_anchor(T0)


def test_manifest_recomputes_identity_and_rejects_tampering(tmp_path):
    _, events = mod.load_cpi_events()
    assert len(events) == 52
    assert all(e['anchor']-e['timestamp'] == timedelta(minutes=30) for e in events)
    data = json.loads(mod.CPI_MANIFEST.read_text())
    data['events'][0]['raw_event_hash'] = '0'*64
    path = tmp_path/'bad.json'
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='identity'):
        mod.load_cpi_events(path)


def test_control_contamination_covers_whole_forward_interval():
    assert mod.contaminated_control(T0,24,(T0+timedelta(hours=48),))
    assert not mod.contaminated_control(T0,24,(T0+timedelta(hours=48,seconds=1),))
    assert mod.contaminated_control(T0,1,(T0-timedelta(hours=24),))


def test_pairing_weights_events_equally_and_uses_absolute_control_returns():
    p=mod.paired_summary([(Decimal('.02'),[Decimal('.01')]),
                          (Decimal('.06'),[Decimal('-.02'),Decimal('.02')])])
    assert Decimal(p['event_mean_absolute_return']) == Decimal('.04')
    assert Decimal(p['control_mean_absolute_return']) == Decimal('.015')
    assert Decimal(p['control_mean_signed_return']) == Decimal('.005')
    assert mod.paired_summary([])['absolute_return_ratio'] is None


def test_synthetic_study_uses_delayed_open_and_requires_controls():
    anchor=T0+timedelta(hours=1)
    event={'event_id':'synthetic','timestamp':T0+timedelta(minutes=30),'anchor':anchor}
    segments=[[bar(T0+timedelta(hours=i), 1 if i==0 else 100+i-1) for i in range(26)]]
    lookup=mod.base.build_segment_lookup(segments)
    first=mod.study_asset(lookup,[event],())['1']
    assert first['primary_matched_comparison']['matched_events']==0
    assert Decimal(first['observations'][0]['return'])==Decimal('.01')
    segments.append([bar(anchor-timedelta(days=7)+timedelta(hours=i),100) for i in range(25)])
    second=mod.study_asset(mod.base.build_segment_lookup(segments),[event],())['1']
    assert second['primary_matched_comparison']['matched_events']==1
    assert second['primary_matched_comparison']['absolute_return_ratio'] is None
