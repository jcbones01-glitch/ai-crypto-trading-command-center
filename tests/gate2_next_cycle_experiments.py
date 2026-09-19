from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import median
from zipfile import ZipFile

from research_core.data_ingestion import archive_url, checksum_url, parse_timestamp, verify_sha256_bytes
from research_core.data_interfaces import MarketBar
from research_core.data_quality import scan_archive
from research_core.data_quality_treatment_v2 import build_manifest, common_certified_intervals

START = datetime(2017, 8, 17, tzinfo=timezone.utc)
END = datetime(2022, 1, 1, tzinfo=timezone.utc)
FEE_GRID = [("baseline", Decimal("0.001"), Decimal("0.0005")), ("stress_1", Decimal("0.0015"), Decimal("0.001")), ("stress_2", Decimal("0.0025"), Decimal("0.0015"))]
DELAYS = [1, 2]
PREREG = Path("docs/GATE2_NEXT_CYCLE_PREREGISTRATION_V1.md")
ROOT = Path(__file__).resolve().parents[1]

GRIDS = {
    "HYP-0005": {"volume_lookback": [24, 48], "shock": [Decimal("2"), Decimal("3"), Decimal("4")], "return_threshold": [Decimal("0.005"), Decimal("0.01"), Decimal("0.015")]},
    "HYP-0006": {"btc_threshold": [Decimal("0.01"), Decimal("0.015"), Decimal("0.02")], "gap": [Decimal("0.0025"), Decimal("0.005"), Decimal("0.01")]},
    "HYP-0007": {"volume_lookback": [24, 48], "shock": [Decimal("2"), Decimal("3"), Decimal("4")], "return_threshold": [Decimal("-0.01"), Decimal("-0.015"), Decimal("-0.02")]},
}
BASE = {"HYP-0005": {"volume_lookback": 24, "shock": Decimal("3"), "return_threshold": Decimal("0.01")}, "HYP-0006": {"btc_threshold": Decimal("0.015"), "gap": Decimal("0.005")}, "HYP-0007": {"volume_lookback": 24, "shock": Decimal("3"), "return_threshold": Decimal("-0.015")}}

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def months(start: datetime, end: datetime):
    y, m = start.year, start.month
    while (y, m) < (end.year, end.month):
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1

def fetch(url: str) -> bytes:
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=90) as response:
                return response.read()
        except Exception as exc:
            last = exc
            if attempt < 2:
                time.sleep(2 ** attempt)
    raise last

def parse_valid_bars(path: Path, symbol: str, valid_timestamps: set[datetime]) -> list[MarketBar]:
    out = []
    with ZipFile(path) as archive:
        members = [n for n in archive.namelist() if not n.endswith("/")]
        if len(members) != 1:
            raise RuntimeError(f"unexpected archive members: {path}")
        rows = archive.read(members[0]).decode("utf-8").splitlines()
    market_symbol = "BTC/USDT" if symbol == "BTCUSDT" else "ETH/USDT"
    for row in csv.reader(rows):
        if not row or row[0].strip().lower() in {"open time", "timestamp"} or len(row) < 6:
            continue
        try:
            ts, _ = parse_timestamp(row[0])
            if ts not in valid_timestamps or not (START <= ts < END):
                continue
            vals = [Decimal(x) for x in row[1:6]]
            out.append(MarketBar(ts, market_symbol, *vals))
        except (ValueError, InvalidOperation):
            continue
    return out

def in_break(ts: datetime, breaks) -> bool:
    return any(datetime.fromisoformat(b.start) <= ts < datetime.fromisoformat(b.end) for b in breaks)

def continuous_segments(bars: list[MarketBar], breaks) -> list[list[MarketBar]]:
    out, current = [], []
    for bar in bars:
        if in_break(bar.timestamp, breaks):
            if current:
                out.append(current)
                current = []
            continue
        if current and bar.timestamp != current[-1].timestamp + timedelta(hours=1):
            out.append(current)
            current = []
        current.append(bar)
    if current:
        out.append(current)
    return [s for s in out if s]

def synchronized_segments(btc_bars: list[MarketBar], eth_bars: list[MarketBar], btc_breaks, eth_breaks) -> list[tuple[list[MarketBar], list[MarketBar]]]:
    """Build HYP-0006 samples from exact canonical timestamp intersections."""
    btc_by_ts = {bar.timestamp: bar for bar in btc_bars if not in_break(bar.timestamp, btc_breaks)}
    eth_by_ts = {bar.timestamp: bar for bar in eth_bars if not in_break(bar.timestamp, eth_breaks)}
    common = sorted(set(btc_by_ts) & set(eth_by_ts))
    pairs: list[tuple[list[MarketBar], list[MarketBar]]] = []
    btc_segment, eth_segment = [], []
    for ts in common:
        if btc_segment and ts != btc_segment[-1].timestamp + timedelta(hours=1):
            pairs.append((btc_segment, eth_segment)); btc_segment, eth_segment = [], []
        btc_segment.append(btc_by_ts[ts]); eth_segment.append(eth_by_ts[ts])
    if btc_segment:
        pairs.append((btc_segment, eth_segment))
    return [(btc, eth) for btc, eth in pairs if btc and eth]

def median_previous(values: list[Decimal], i: int, n: int) -> Decimal | None:
    if i < n:
        return None
    window = values[i - n:i]
    return Decimal(str(median([float(x) for x in window]))) if window else None

def event_condition(hyp: str, i: int, bars, params: dict, btc_bars=None) -> bool:
    if i < 1:
        return False
    ret = bars[i].close / bars[i - 1].close - 1
    if hyp in {"HYP-0005", "HYP-0007"}:
        n = params["volume_lookback"]
        baseline = median_previous([b.volume for b in bars], i, n)
        if baseline is None or baseline <= 0:
            return False
        shock = bars[i].volume >= Decimal(params["shock"]) * baseline
        threshold = Decimal(params["return_threshold"])
        return shock and (ret >= threshold if hyp == "HYP-0005" else ret <= threshold)
    if btc_bars is None or len(btc_bars) != len(bars) or btc_bars[i].timestamp != bars[i].timestamp:
        raise ValueError("HYP-0006 requires exact BTC/ETH timestamp synchronization")
    btc_ret = btc_bars[i].close / btc_bars[i - 1].close - 1
    return btc_ret >= Decimal(params["btc_threshold"]) and btc_ret - ret >= Decimal(params["gap"])

def event_return(entry: MarketBar, exit_bar: MarketBar, fee: Decimal, slip: Decimal) -> Decimal:
    buy = entry.open * (Decimal("1") + slip)
    sell = exit_bar.close * (Decimal("1") - slip)
    gross = sell / buy - 1
    return (Decimal("1") + gross) * (Decimal("1") - fee) * (Decimal("1") - fee) - 1

def simulate_events(bars: list[MarketBar], hyp: str, params: dict, fee: Decimal, slip: Decimal, delay: int, btc_bars=None) -> dict:
    if delay not in (1, 2):
        raise ValueError("delay must be 1 or 2")
    returns, event_records = [], []
    i = 1
    while i + delay < len(bars):
        if not event_condition(hyp, i, bars, params, btc_bars):
            i += 1
            continue
        entry_i = i + delay
        r = event_return(bars[entry_i], bars[entry_i], fee, slip)
        returns.append(r)
        event_records.append({"signal_index": i, "entry_index": entry_i, "exit_index": entry_i, "signal_timestamp": bars[i].timestamp.isoformat(), "entry_timestamp": bars[entry_i].timestamp.isoformat(), "return": str(r)})
        i = entry_i + 1
    equity = [Decimal("1")]
    for r in returns:
        equity.append(equity[-1] * (Decimal("1") + r))
    return {"returns": returns, "events": event_records, "equity": equity}

def aggregate(returns: list[Decimal]) -> dict:
    if not returns:
        return {"events": 0, "compound_return": "0", "mean_event_return": "0", "positive_event_fraction": "0"}
    growth = Decimal("1")
    for r in returns:
        growth *= 1 + r
    return {"events": len(returns), "compound_return": str(growth - 1), "mean_event_return": str(sum(returns, Decimal("0")) / Decimal(len(returns))), "positive_event_fraction": str(Decimal(sum(r > 0 for r in returns)) / Decimal(len(returns)))}

def max_drawdown(equity: list[Decimal]) -> Decimal:
    peak, out = equity[0], Decimal("0")
    for value in equity:
        peak = max(peak, value)
        if peak > 0:
            out = max(out, (peak - value) / peak)
    return out

def longest_recovery(equity: list[Decimal]) -> int:
    peak, peak_i, longest = equity[0], 0, 0
    for i, value in enumerate(equity):
        if value >= peak:
            peak, peak_i = value, i
        else:
            longest = max(longest, i - peak_i)
    return longest

def parameter_cells(hyp):
    keys = list(GRIDS[hyp]); out = []
    def rec(k, current):
        if k == len(keys): out.append(dict(current)); return
        for value in GRIDS[hyp][keys[k]]:
            current[keys[k]] = value; rec(k + 1, current)
    rec(0, {})
    return out

def summarize_segments(segments, hyp, params, fee, slip, delay, btc_segments=None):
    details = []
    for idx, seg in enumerate(segments):
        try:
            btc = btc_segments[idx] if btc_segments is not None else None
            if btc is not None and [b.timestamp for b in btc] != [b.timestamp for b in seg]:
                raise ValueError("HYP-0006 segment timestamps are not exactly synchronized")
            sim = simulate_events(seg, hyp, params, fee, slip, delay, btc)
            details.append({"segment": idx, "aggregate": aggregate(sim["returns"]), "events": sim["events"], "error": None})
        except Exception as exc:
            details.append({"segment": idx, "aggregate": None, "events": [], "error": f"{type(exc).__name__}: {exc}"})
    valid = [d for d in details if d["aggregate"] and d["aggregate"]["events"]]
    event_returns = [Decimal(e["return"]) for d in valid for e in d["events"]]
    seg_returns = [Decimal(d["aggregate"]["compound_return"]) for d in valid]
    return {"segments": details, "aggregate": {**aggregate(event_returns), "mean_segment_return": str(sum(seg_returns, Decimal("0")) / Decimal(len(seg_returns))) if seg_returns else "0", "eligible_segments": len(valid)}}

def concentration_and_dd(details):
    seg_returns = [Decimal(d["aggregate"]["compound_return"]) for d in details if d["aggregate"] and d["aggregate"]["events"]]
    positive_log_total = sum((Decimal(1 + r).ln() for r in seg_returns if r > 0 and r > -1), Decimal("0"))
    contributions, events = [], []
    worst, maxdd, recovery, total_events = None, Decimal("0"), 0, 0
    for d in details:
        if not d["aggregate"] or not d["aggregate"]["events"]:
            continue
        r = Decimal(d["aggregate"]["compound_return"])
        contribution = Decimal("0") if r <= 0 or positive_log_total <= 0 else Decimal(1 + r).ln() / positive_log_total
        contributions.append({"segment": d["segment"], "positive_log_contribution": str(contribution), "return": str(r)})
        events.extend(Decimal(e["return"]) for e in d["events"])
        worst = r if worst is None else min(worst, r)
        eq = [Decimal("1")]
        for e in d["events"]:
            event_r = Decimal(e["return"])
            eq.append(eq[-1] * (Decimal("1") + event_r))
        maxdd = max(maxdd, max_drawdown(eq)); recovery = max(recovery, longest_recovery(eq)); total_events += len(d["events"])
    positive = sorted((x for x in events if x > 0), reverse=True)
    top_n = max(1, math.ceil(len(positive) * 0.10)) if positive else 0
    top_fraction = sum(positive[:top_n], Decimal("0")) / sum(positive, Decimal("0")) if positive else None
    worst_value = worst if worst is not None else Decimal("0")
    return {"segments": contributions, "top_10_positive_event_pnl_fraction": str(top_fraction) if top_fraction is not None else None, "max_drawdown": str(maxdd), "worst_segment_return": str(worst_value), "longest_recovery_events": recovery, "eligible_events": total_events}

def compound_return(returns):
    growth = Decimal("1")
    for r in returns:
        growth *= Decimal("1") + Decimal(r)
    return growth - Decimal("1")

def regime_for_signal(bars, i):
    if i < 168:
        return None
    trailing = bars[i].close / bars[i - 168].close - Decimal("1")
    if trailing > Decimal("0.10"):
        return "bull"
    if trailing < Decimal("-0.10"):
        return "bear"
    return "neutral"

def regime_summary(segments, hyp, params, fee, slip, delay, btc_segments=None):
    by_regime = {k: [] for k in ("bull", "bear", "neutral")}
    eligible_bars = {k: 0 for k in by_regime}
    for idx, seg in enumerate(segments):
        btc = btc_segments[idx] if btc_segments is not None else None
        for i in range(len(seg)):
            regime = regime_for_signal(seg, i)
            if regime is not None:
                eligible_bars[regime] += 1
        sim = simulate_events(seg, hyp, params, fee, slip, delay, btc)
        for event in sim["events"]:
            regime = regime_for_signal(seg, event["signal_index"])
            if regime is not None:
                by_regime[regime].append(Decimal(event["return"]))
    results = {}
    for regime, values in by_regime.items():
        comp = compound_return(values)
        results[regime] = {"eligible_bars": eligible_bars[regime], "events": len(values), "compound_return": str(comp), "mean_event_return": str(sum(values, Decimal("0")) / Decimal(len(values))) if values else "0", "positive": bool(values and comp > 0)}
    qualifying = [r for r in results.values() if r["eligible_bars"] >= 100]
    positive_qualifying = [r for r in qualifying if r["positive"]]
    return {"regimes": results, "qualifying_regimes": len(qualifying), "positive_qualifying_regimes": len(positive_qualifying), "pass": len(qualifying) < 2 or len(positive_qualifying) >= 2}

def leave_one_out(segments, hyp, params, fee, slip, delay, btc_segments=None):
    variants = []
    for excluded in range(len(segments)):
        returns = []
        for idx, seg in enumerate(segments):
            if idx == excluded:
                continue
            btc = btc_segments[idx] if btc_segments is not None else None
            returns.extend(simulate_events(seg, hyp, params, fee, slip, delay, btc)["returns"])
        comp = compound_return(returns)
        variants.append({"excluded_segment": excluded, "events": len(returns), "compound_return": str(comp), "above_cash": comp > 0})
    passing = sum(v["above_cash"] for v in variants)
    return {"variants": variants, "passing_variants": passing, "total_variants": len(variants), "pass_fraction": str(Decimal(passing) / Decimal(len(variants))) if variants else "0"}

def concentration_metrics(segments, hyp, params, fee, slip, delay, btc_segments=None):
    segment_returns, event_records = [], []
    for idx, seg in enumerate(segments):
        btc = btc_segments[idx] if btc_segments is not None else None
        sim = simulate_events(seg, hyp, params, fee, slip, delay, btc)
        if sim["events"]:
            segment_returns.append((idx, compound_return(sim["returns"])))
            event_records.extend(sim["events"])
    positive_logs = [(idx, (Decimal("1") + r).ln()) for idx, r in segment_returns if r > 0 and r > -1]
    total_positive_log = sum(v for _, v in positive_logs)
    contributions = [{"segment": idx, "positive_log_contribution": str(v / total_positive_log if total_positive_log > 0 else Decimal("0")), "return": str(dict(segment_returns)[idx])} for idx, v in positive_logs]
    positive_events = sorted((Decimal(e["return"]) for e in event_records if Decimal(e["return"]) > 0), reverse=True)
    positive_event_pnl = sum(positive_events, Decimal("0"))
    top_n = max(1, math.ceil(len(positive_events) * 0.10)) if positive_events else 0
    top_fraction = sum(positive_events[:top_n], Decimal("0")) / positive_event_pnl if positive_event_pnl > 0 else None
    max_single_segment_contribution = max((Decimal(x["positive_log_contribution"]) for x in contributions), default=Decimal("0"))
    return {"segments": contributions, "max_single_segment_positive_log_contribution": str(max_single_segment_contribution), "top_10_positive_event_pnl_fraction": str(top_fraction) if top_fraction is not None else None, "positive_event_count": len(positive_events), "positive_event_pnl": str(positive_event_pnl), "pass": bool(contributions) and max_single_segment_contribution <= Decimal("0.50") and top_fraction is not None and top_fraction <= Decimal("0.50")}

def drawdown_recovery_metrics(segments, hyp, params, fee, slip, delay, btc_segments=None):
    max_dd = Decimal("0")
    worst_segment = Decimal("0")
    longest_recovery_hours = Decimal("0")
    total_events = 0
    segment_metrics = []
    for idx, seg in enumerate(segments):
        btc = btc_segments[idx] if btc_segments is not None else None
        sim = simulate_events(seg, hyp, params, fee, slip, delay, btc)
        if not sim["events"]:
            continue
        eq, peak, peak_time, local_max_dd, local_recovery = [Decimal("1")], Decimal("1"), None, Decimal("0"), Decimal("0")
        for r, event in zip(sim["returns"], sim["events"]):
            eq.append(eq[-1] * (Decimal("1") + r))
            ts = datetime.fromisoformat(event["entry_timestamp"])
            if eq[-1] >= peak:
                peak, peak_time = eq[-1], ts
            else:
                local_max_dd = max(local_max_dd, (peak - eq[-1]) / peak if peak > 0 else Decimal("0"))
                if peak_time is not None:
                    local_recovery = max(local_recovery, Decimal((ts - peak_time).total_seconds()) / Decimal("3600"))
        seg_return = eq[-1] - Decimal("1")
        worst_segment = min(worst_segment, seg_return)
        max_dd = max(max_dd, local_max_dd)
        longest_recovery_hours = max(longest_recovery_hours, local_recovery)
        segment_metrics.append({"segment": idx, "compound_return": str(seg_return), "max_drawdown": str(local_max_dd), "longest_recovery_hours": str(local_recovery), "events": len(sim["events"])})
        total_events += len(sim["events"])
    eligible_duration_hours = sum(max(0, int((seg[-1].timestamp - seg[0].timestamp).total_seconds() // 3600) + 1) for seg in segments if seg)
    return {"max_drawdown": str(max_dd), "worst_segment_return": str(worst_segment), "longest_recovery_hours": str(longest_recovery_hours), "eligible_duration_hours": eligible_duration_hours, "segment_metrics": segment_metrics, "eligible_events": total_events, "pass": bool(total_events) and max_dd < Decimal("0.70") and worst_segment >= Decimal("-0.50") and longest_recovery_hours <= Decimal("0.50") * Decimal(eligible_duration_hours)}

def control_difference(eth_segments, btc_segments, params, delay):
    conditional, control = [], []
    for btc_seg, eth_seg in zip(btc_segments, eth_segments):
        for i in range(1, len(eth_seg)):
            if i + delay >= len(eth_seg):
                continue
            btc_ret = btc_seg[i].close / btc_seg[i - 1].close - Decimal("1")
            eth_ret = eth_seg[i].close / eth_seg[i - 1].close - Decimal("1")
            if btc_ret >= Decimal(params["btc_threshold"]) and btc_ret - eth_ret >= Decimal(params["gap"]):
                conditional.append(eth_seg[i + delay].close / eth_seg[i + delay - 1].close - Decimal("1"))
            control.append(eth_seg[i + delay].close / eth_seg[i + delay - 1].close - Decimal("1"))
    cond_mean = sum(conditional, Decimal("0")) / Decimal(len(conditional)) if conditional else Decimal("0")
    ctrl_mean = sum(control, Decimal("0")) / Decimal(len(control)) if control else Decimal("0")
    return {"conditional_events": len(conditional), "control_events": len(control), "conditional_mean": str(cond_mean), "control_mean": str(ctrl_mean), "difference": str(cond_mean - ctrl_mean)}

def assess_hypothesis(hyp, report, loaded, common_pairs):
    required = ["BTCUSDT", "ETHUSDT"] if hyp in {"HYP-0005", "HYP-0007"} else ["ETHUSDT"]
    fee0, slip0 = FEE_GRID[0][1], FEE_GRID[0][2]
    fee2, slip2 = FEE_GRID[-1][1], FEE_GRID[-1][2]
    params = BASE[hyp]
    cells_by_asset = {asset: report["assets"][asset]["cells"][hyp] for asset in required}
    def match(asset, fee_name, delay):
        target = {k: str(v) for k, v in params.items()}
        return next(x for x in cells_by_asset[asset] if x["params"] == target and x["fee_case"] == fee_name and x["delay_bars"] == delay)
    dimensions, param_checks = {}, []
    for asset in required:
        perturb = [x for x in cells_by_asset[asset] if x["fee_case"] == "baseline" and x["delay_bars"] == 1]
        valid = [x for x in perturb if x["summary"]["aggregate"]["eligible_segments"] > 0]
        positive = [x for x in valid if Decimal(x["summary"]["aggregate"]["mean_segment_return"]) > 0]
        compounds = sorted(Decimal(x["summary"]["aggregate"]["compound_return"]) for x in valid)
        median_comp = (compounds[len(compounds)//2] if len(compounds)%2 else (compounds[len(compounds)//2-1] + compounds[len(compounds)//2]) / Decimal("2")) if compounds else Decimal("0")
        fraction = Decimal(len(positive)) / Decimal(len(valid)) if valid else Decimal("0")
        param_checks.append({"asset": asset, "valid_cells": len(valid), "positive_mean_segment_cells": len(positive), "positive_fraction": str(fraction), "median_compound_return": str(median_comp), "pass": fraction >= Decimal("0.60") and median_comp > 0})
    dimensions["parameter_neighborhood"] = {"checks": param_checks, "pass": all(x["pass"] for x in param_checks)}
    fee_checks, timing_checks, regime_checks, sample_checks, concentration_checks, dd_checks = [], [], [], [], [], []
    for asset in required:
        fee_cell, timing_cell = match(asset, "stress_2", 1), match(asset, "baseline", 2)
        fee_pass = Decimal(fee_cell["summary"]["aggregate"]["mean_segment_return"]) > 0 and Decimal(fee_cell["summary"]["aggregate"]["compound_return"]) > 0
        timing_pass = Decimal(timing_cell["summary"]["aggregate"]["mean_segment_return"]) > 0 and Decimal(timing_cell["summary"]["aggregate"]["compound_return"]) > 0
        fee_checks.append({"asset": asset, "cell": fee_cell, "pass": fee_pass})
        timing_checks.append({"asset": asset, "cell": timing_cell, "pass": timing_pass})
        segments = [p[1] for p in common_pairs] if hyp == "HYP-0006" else loaded[asset]["segments"]
        btc_segments = [p[0] for p in common_pairs] if hyp == "HYP-0006" else None
        reg = regime_summary(segments, hyp, params, fee0, slip0, 1, btc_segments)
        loo = leave_one_out(segments, hyp, params, fee0, slip0, 1, btc_segments)
        conc = concentration_metrics(segments, hyp, params, fee0, slip0, 1, btc_segments)
        dd = drawdown_recovery_metrics(segments, hyp, params, fee0, slip0, 1, btc_segments)
        base_comp = Decimal(match(asset, "baseline", 1)["summary"]["aggregate"]["compound_return"])
        sample_pass = base_comp > 0 and Decimal(loo["pass_fraction"]) >= Decimal("0.75")
        sample_checks.append({"asset": asset, "baseline_compound_return": str(base_comp), "loo": loo, "pass": sample_pass})
        concentration_checks.append({"asset": asset, "metrics": conc, "pass": conc["pass"]})
        dd_checks.append({"asset": asset, "metrics": dd, "pass": dd["pass"]})
        regime_checks.append({"asset": asset, "result": reg, "pass": reg["pass"]})
    dimensions["fee_slippage"] = {"checks": fee_checks, "pass": all(x["pass"] for x in fee_checks)}
    dimensions["timing"] = {"checks": timing_checks, "pass": all(x["pass"] for x in timing_checks)}
    dimensions["regime_stability"] = {"checks": regime_checks, "pass": all(x["pass"] for x in regime_checks)}
    dimensions["sample_size_stability"] = {"checks": sample_checks, "pass": all(x["pass"] for x in sample_checks)}
    dimensions["concentration"] = {"checks": concentration_checks, "pass": all(x["pass"] for x in concentration_checks)}
    dimensions["drawdown_recovery"] = {"checks": dd_checks, "pass": all(x["pass"] for x in dd_checks)}
    if hyp in {"HYP-0005", "HYP-0007"}:
        transfer = []
        for asset in required:
            base_cell = match(asset, "baseline", 1)
            transfer.append({"asset": asset, "mean_segment_return": base_cell["summary"]["aggregate"]["mean_segment_return"], "compound_return": base_cell["summary"]["aggregate"]["compound_return"], "pass": Decimal(base_cell["summary"]["aggregate"]["mean_segment_return"]) > 0 and Decimal(base_cell["summary"]["aggregate"]["compound_return"]) > 0})
        dimensions["asset_transferability"] = {"checks": transfer, "pass": all(x["pass"] for x in transfer)}
    else:
        eth_segments = [p[1] for p in common_pairs]
        btc_segments = [p[0] for p in common_pairs]
        control = control_difference(eth_segments, btc_segments, params, 1)
        base_cell = match("ETHUSDT", "baseline", 1)
        transfer_pass = Decimal(base_cell["summary"]["aggregate"]["mean_segment_return"]) > 0 and Decimal(base_cell["summary"]["aggregate"]["compound_return"]) > 0 and Decimal(control["difference"]) > 0
        dimensions["asset_transferability"] = {"checks": [{"asset": "ETHUSDT", "control": control, "mean_segment_return": base_cell["summary"]["aggregate"]["mean_segment_return"], "compound_return": base_cell["summary"]["aggregate"]["compound_return"], "pass": transfer_pass}], "pass": transfer_pass}
    passed = [name for name, value in dimensions.items() if value["pass"]]
    dimensions["overall"] = {"pass": len(passed) == 8, "passed_dimensions": passed, "required_dimensions": 8}
    return dimensions

def main():
    prereg_sha = sha256_file(ROOT / PREREG)
    output = Path("gate2_next_cycle_results"); output.mkdir(exist_ok=True)
    report = {"experiment_version": "gate2-next-cycle-v1", "code_commit": os.environ.get("GITHUB_SHA", "UNKNOWN"), "preregistration": {"path": str(PREREG), "sha256": prereg_sha}, "development_window": [START.isoformat(), END.isoformat()], "validation_or_oos_accessed": False, "registered_parameter_cell_count": 45, "assets": {}, "decisions": {}}
    with tempfile.TemporaryDirectory(prefix="gate2-next-") as directory:
        root = Path(directory); loaded = {}
        for symbol in ("BTCUSDT", "ETHUSDT"):
            reports, paths = [], []
            for year, month in months(START, END):
                url = archive_url(symbol, year, month)
                payload = fetch(url); checksum = fetch(checksum_url(url)).decode("utf-8")
                if not verify_sha256_bytes(payload, checksum):
                    raise RuntimeError(f"checksum mismatch: {url}")
                path = root / symbol / Path(url).name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(payload)
                reports.append(scan_archive(path, symbol, True)); paths.append(path)
            manifest = build_manifest(symbol, reports, START, END)
            bars = []
            for path, report_item in zip(paths, reports):
                bars.extend(parse_valid_bars(path, symbol, set(report_item.valid_timestamps)))
            bars.sort(key=lambda b: b.timestamp)
            segments = continuous_segments(bars, manifest.continuity_breaks)
            loaded[symbol] = {"manifest": manifest, "bars": bars, "segments": segments}
        btc = loaded["BTCUSDT"]; eth = loaded["ETHUSDT"]
        common_pairs = synchronized_segments(btc["bars"], eth["bars"], btc["manifest"].continuity_breaks, eth["manifest"].continuity_breaks)
        report["synchronized_common_segments"] = len(common_pairs)
        for symbol, data in (("BTCUSDT", btc), ("ETHUSDT", eth)):
            report["assets"][symbol] = {"dataset_identity": data["manifest"].dataset_identity, "source_integrity": data["manifest"].source_integrity, "certification": data["manifest"].research_certification, "baseline": {}, "cells": {}}
        for symbol, segments in (("BTCUSDT", btc["segments"]), ("ETHUSDT", eth["segments"])):
            for hyp in ("HYP-0005", "HYP-0007"):
                report["assets"][symbol]["cells"][hyp] = []
                for params in parameter_cells(hyp):
                    for fee_name, fee, slip in FEE_GRID:
                        for delay in DELAYS:
                            summary = summarize_segments(segments, hyp, params, fee, slip, delay)
                            report["assets"][symbol]["cells"][hyp].append({"params": {k: str(v) for k, v in params.items()}, "fee_case": fee_name, "commission": str(fee), "slippage": str(slip), "delay_bars": delay, "summary": summary})
                base = next(x for x in report["assets"][symbol]["cells"][hyp] if x["params"] == {k: str(v) for k, v in BASE[hyp].items()} and x["fee_case"] == "baseline" and x["delay_bars"] == 1)
                report["assets"][symbol]["baseline"][hyp] = base
                report["assets"][symbol].setdefault("concentration_drawdown", {})[hyp] = concentration_and_dd(base["summary"]["segments"])
        report["assets"]["ETHUSDT"]["cells"]["HYP-0006"] = []
        for params in parameter_cells("HYP-0006"):
            for fee_name, fee, slip in FEE_GRID:
                for delay in DELAYS:
                    eth_segments = [pair[1] for pair in common_pairs]
                    btc_segments = [pair[0] for pair in common_pairs]
                    summary = summarize_segments(eth_segments, "HYP-0006", params, fee, slip, delay, btc_segments)
                    report["assets"]["ETHUSDT"]["cells"]["HYP-0006"].append({"params": {k: str(v) for k, v in params.items()}, "fee_case": fee_name, "commission": str(fee), "slippage": str(slip), "delay_bars": delay, "summary": summary})
        base = next(x for x in report["assets"]["ETHUSDT"]["cells"]["HYP-0006"] if x["params"] == {k: str(v) for k, v in BASE["HYP-0006"].items()} and x["fee_case"] == "baseline" and x["delay_bars"] == 1)
        report["assets"]["ETHUSDT"]["baseline"]["HYP-0006"] = base
        report["assets"]["ETHUSDT"].setdefault("concentration_drawdown", {})["HYP-0006"] = concentration_and_dd(base["summary"]["segments"])
        for hyp in ("HYP-0005", "HYP-0006", "HYP-0007"):
            report["assets"].setdefault("robustness", {})
            report["assets"]["robustness"][hyp] = assess_hypothesis(hyp, report, loaded, common_pairs)
        report["decisions"] = {}
        for hyp in ("HYP-0005", "HYP-0006", "HYP-0007"):
            result = report["assets"]["robustness"][hyp]
            report["decisions"][hyp] = "ROBUSTNESS_PASS" if result["overall"]["pass"] else "ROBUSTNESS_FAIL"
        report["decisions"]["overall"] = "ROBUSTNESS_PASS" if all(v == "ROBUSTNESS_PASS" for k, v in report["decisions"].items() if k != "overall") else "ROBUSTNESS_FAIL"
    with open(output / "next_cycle_results.json", "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)

if __name__ == "__main__":
    main()
