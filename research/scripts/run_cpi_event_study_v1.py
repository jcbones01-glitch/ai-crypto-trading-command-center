"""Preregistered delayed CPI study; no immediate-reaction or trading inference."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from intelligence import EventRecord, build_event_dataset_manifest
from research.scripts import run_fomc_event_study_v1 as base

ROOT = base.ROOT
CPI_MANIFEST = ROOT / 'research/experiments/cpi_development_manifest_v1.json'
PREREGISTRATION = ROOT / 'docs/GATE2_CPI_EVENT_STUDY_PREREGISTRATION_V1.md'
EXPECTED_CPI_DATASET_ID = '7773afbb02bbfff60031e3a8455ce119308b1d1b86c0b45adc43d54a6c1dc119'


def load_cpi_events(path: Path = CPI_MANIFEST):
    payload = json.loads(path.read_text())
    if payload.get('validation_or_oos_accessed') is not False:
        raise ValueError('Development-only manifest required')
    events = payload['events']
    records = []
    normalized = []
    for item in events:
        record = {k: v for k, v in item.items() if k != 'source_url'}
        for k in ('event_time', 'published_at', 'first_market_available_at'):
            record[k] = base.parse_utc(record[k])
        record['assets'] = tuple(record['assets'])
        event = EventRecord(**record)
        t = event.first_market_available_at
        if not base.START <= t < base.END:
            raise ValueError('CPI outside Development')
        if t.minute != 30 or t.second or t.microsecond:
            raise ValueError('CPI must be at the frozen half-hour release time')
        if not event.event_time == event.published_at == t:
            raise ValueError('CPI release timestamps disagree')
        records.append(event)
        normalized.append({**item, 'timestamp': t, 'anchor': hourly_anchor(t)})
    m = build_event_dataset_manifest(records)
    if (m.dataset_id != EXPECTED_CPI_DATASET_ID or m.record_count != 52
            or payload['event_dataset']['dataset_id'] != m.dataset_id
            or payload['event_dataset']['record_count'] != 52):
        raise ValueError('CPI dataset identity/count mismatch')
    return payload, normalized


def hourly_anchor(t):
    if t.minute != 30 or t.second or t.microsecond:
        raise ValueError('expected exact half-hour timestamp')
    return t.replace(minute=0) + timedelta(hours=1)


def contaminated_control(anchor, horizon, event_times):
    return any(anchor - timedelta(hours=24) <= t <= anchor + timedelta(hours=horizon+24)
               for t in event_times)


def average(values):
    return sum(values, Decimal(0)) / Decimal(len(values)) if values else None


def paired_summary(pairs):
    if not pairs:
        return {'matched_events': 0, 'event_mean_signed_return': None,
                'control_mean_signed_return': None, 'event_mean_absolute_return': None,
                'control_mean_absolute_return': None, 'absolute_return_ratio': None,
                'signed_difference': None, 'absolute_difference': None}
    es = average([p[0] for p in pairs])
    cs = average([average(p[1]) for p in pairs])
    ea = average([abs(p[0]) for p in pairs])
    ca = average([average([abs(v) for v in p[1]]) for p in pairs])
    return {'matched_events': len(pairs), 'event_mean_signed_return': str(es),
            'control_mean_signed_return': str(cs), 'event_mean_absolute_return': str(ea),
            'control_mean_absolute_return': str(ca),
            'absolute_return_ratio': str(ea/ca) if ca else None,
            'signed_difference': str(es-cs), 'absolute_difference': str(ea-ca)}


def study_asset(lookup, events, contamination_times):
    results = {}
    for horizon in base.HORIZONS_HOURS:
        rows, pairs, all_events, all_controls = [], [], [], []
        for event in events:
            anchor = event['anchor']
            eligible, reason, value = base.forward_open_return(lookup, anchor, horizon)
            controls, values = [], []
            for lag in base.CONTROL_LAGS_DAYS:
                t = anchor - timedelta(days=lag)
                cv = None
                if not base.START <= t < t + timedelta(hours=horizon) < base.END:
                    ok, why = False, 'control interval outside Development'
                elif contaminated_control(t, horizon, contamination_times):
                    ok, why = False, 'control interval within 24h of CPI/FOMC'
                else:
                    ok, why, cv = base.forward_open_return(lookup, t, horizon)
                if cv is not None:
                    values.append(cv)
                    all_controls.append(cv)
                controls.append({'lag_days':lag, 'anchor':t.isoformat(), 'eligible':ok,
                                 'reason':why, 'return':str(cv) if cv is not None else None})
            if value is not None:
                all_events.append(value)
                if values:
                    pairs.append((value, values))
            rows.append({'event_id':event['event_id'], 'event_timestamp':event['timestamp'].isoformat(),
                         'anchor':anchor.isoformat(), 'eligible':eligible, 'reason':reason,
                         'return':str(value) if value is not None else None,
                         'matched':value is not None and bool(values), 'controls':controls})
        results[str(horizon)] = {'primary_matched_comparison':paired_summary(pairs),
                                'secondary_all_events':base.summarize_returns(all_events),
                                'secondary_pooled_controls':base.summarize_returns(all_controls),
                                'observations':rows}
    return results


def run_study():
    _, events = load_cpi_events()
    _, fomc = base.load_frozen_events()
    contamination_times = tuple(e['timestamp'] for e in events + fomc)
    report = {'study_version':'cpi-delayed-descriptive-event-study-v1',
              'github_sha':os.environ.get('GITHUB_SHA','UNKNOWN'),
              'preregistration_sha256':base.sha256_file(PREREGISTRATION),
              'cpi_manifest_sha256':base.sha256_file(CPI_MANIFEST),
              'cpi_dataset_id':EXPECTED_CPI_DATASET_ID,
              'fomc_manifest_sha256':base.sha256_file(base.FOMC_MANIFEST),
              'validation_or_oos_accessed':False,
              'interpretation_boundary':'DESCRIPTIVE_ONLY_NO_STRATEGY_PROMOTION',
              'anchor_delay_minutes':30, 'horizons_hours':list(base.HORIZONS_HOURS),
              'control_lags_days':list(base.CONTROL_LAGS_DAYS),
              'market_datasets':{}, 'results':{}}
    with tempfile.TemporaryDirectory(prefix='cpi-study-') as tmp:
        for symbol in base.ASSETS:
            manifest, segments = base.load_market_data(symbol, Path(tmp))
            report['market_datasets'][symbol] = {'dataset_identity':manifest.dataset_identity,
                                               'source_integrity':manifest.source_integrity}
            report['results'][symbol] = study_asset(base.build_segment_lookup(segments), events,
                                                    contamination_times)
    return report


def main():
    report = run_study()
    out = Path('event_intelligence_results/cpi_event_study_v1.json')
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('CPI_REPORT_BEGIN')
    print(out.read_text())
    print('CPI_REPORT_END')
    print('CPI_REPORT_SHA256='+base.sha256_file(out))


if __name__ == '__main__':
    main()
