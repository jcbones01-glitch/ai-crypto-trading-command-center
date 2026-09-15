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
from research_core.data_quality_treatment_v2 import build_manifest

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


def median_previous(values: list[Decimal], i: int, n: int) -> Decimal | None:
    if i < n:
        return None
    window = values[i - n:i]
    return Decimal(str(median([float(x) for x in window]))) if window else None


def event_condition(hyp: str, i: int, bars, params: dict, btc_bars=None) -> bool:
    closes = [b.close for b in bars]
    if i < 1:
        return False
    ret = closes[i] / closes[i - 1] - 1
    if hyp in {"HYP-0005", "HYP-0007"}:
        n = params["volume_lookback"]
        baseline = median_previous([b.volume for b in bars], i, n)
        if baseline is None or baseline <= 0:
            return False
        shock = bars[i].volume >= Decimal(params["shock"]) * baseline
        threshold = Decimal(params["return_threshold"])
        return shock and (ret >= threshold if hyp == "HYP-0005" else ret <= threshold)
    btc = btc_bars[i]
    btc_ret = btc.close / btc_bars[i - 1].close - 1
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
        if entry_i >= len(bars):
            break
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
        if peak > 0: out = max(out, (peak - value) / peak)
    return out


def longest_recovery(equity: list[Decimal]) -> int:
    peak, peak_i, longest = equity[0], 0, 0
    for i, value in enumerate(equity):
        if value >= peak: peak, peak_i = value, i
        else: longest = max(longest, i - peak_i)
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
    worst, maxdd, recovery, total_events = Decimal("0"), Decimal("0"), 0, 0
    for d in details:
        if not d["aggregate"] or not d["aggregate"]["events"]: continue
        r = Decimal(d["aggregate"]["compound_return"])
        contribution = Decimal("0") if r <= 0 or positive_log_total <= 0 else Decimal(1 + r).ln() / positive_log_total
        contributions.append({"segment": d["segment"], "positive_log_contribution": str(contribution), "return": str(r)})
        events.extend(Decimal(e["return"]) for e in d["events"])
        worst = min(worst, r)
        eq = [Decimal("1")]
        for e in d["events"]: eq.append(eq[-1] * (Decimal("1") + e))
        maxdd = max(maxdd, max_drawdown(eq)); recovery = max(recovery, longest_recovery(eq)); total_events += len(d["events"])
    positive = sorted((x for x in events if x > 0), reverse=True)
    top_n = max(1, math.ceil(len(positive) * 0.10)) if positive else 0
    top_fraction = sum(positive[:top_n], Decimal("0")) / sum(positive, Decimal("0")) if positive else None
    return {"segments": contributions, "top_10_positive_event_pnl_fraction": str(top_fraction) if top_fraction is not None else None, "max_drawdown": str(maxdd), "worst_segment_return": str(worst), "longest_recovery_events": recovery, "eligible_events": total_events}


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
                if not verify_sha256_bytes(payload, checksum): raise RuntimeError(f"checksum mismatch: {url}")
                path = root / symbol / Path(url).name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(payload)
                reports.append(scan_archive(path, symbol, True)); paths.append(path)
            manifest = build_manifest(symbol, reports, START, END)
            bars = []
            for scan, path in zip(reports, paths): bars.extend(parse_valid_bars(path, symbol, set(scan.valid_timestamps)))
            bars.sort(key=lambda b: b.timestamp); loaded[symbol] = {"manifest": manifest, "segments": continuous_segments(bars, manifest.continuity_breaks)}
        btc_by_ts = {b.timestamp: b for s in loaded["BTCUSDT"]["segments"] for b in s}
        common = []
        for eseg in loaded["ETHUSDT"]["segments"]:
            current = []
            for bar in eseg:
                if bar.timestamp in btc_by_ts:
                    if current and bar.timestamp != current[-1].timestamp + timedelta(hours=1): common.append(current); current = []
                    current.append(bar)
                elif current: common.append(current); current = []
            if current: common.append(current)
        loaded["COMMON"] = {"segments": common}
        report["assets"] = {s: {"dataset_identity": loaded[s]["manifest"].dataset_identity, "source_integrity": loaded[s]["manifest"].source_integrity, "certification": loaded[s]["manifest"].research_certification, "segment_count": len(loaded[s]["segments"])} for s in ("BTCUSDT", "ETHUSDT")}
        for hyp in GRIDS:
            targets = ["BTCUSDT", "ETHUSDT"] if hyp != "HYP-0006" else ["ETHUSDT"]
            data = {"parameter_cells": [], "fee_slippage": [], "timing": [], "baseline_details": {}, "sample_size": {}, "concentration_drawdown": {}}
            for cid, params in enumerate(parameter_cells(hyp)):
                row = {"cell": f"parameter_{cid:02d}", "parameters": {k: str(v) for k, v in params.items()}, "assets": {}}
                for symbol in targets:
                    segs = loaded[symbol]["segments"] if hyp != "HYP-0006" else common
                    btc = [[btc_by_ts[b.timestamp] for b in s] for s in segs] if hyp == "HYP-0006" else None
                    row["assets"][symbol] = summarize_segments(segs, hyp, params, FEE_GRID[0][1], FEE_GRID[0][2], 1, btc)["aggregate"]
                data["parameter_cells"].append(row)
            params = BASE[hyp]
            for label, fee, slip in FEE_GRID:
                row = {"stress": label, "fee": str(fee), "slippage": str(slip), "assets": {}}
                for symbol in targets:
                    segs = loaded[symbol]["segments"] if hyp != "HYP-0006" else common; btc = [[btc_by_ts[b.timestamp] for b in s] for s in segs] if hyp == "HYP-0006" else None
                    row["assets"][symbol] = summarize_segments(segs, hyp, params, fee, slip, 1, btc)["aggregate"]
                data["fee_slippage"].append(row)
            for delay in DELAYS:
                row = {"delay_bars": delay, "assets": {}}
                for symbol in targets:
                    segs = loaded[symbol]["segments"] if hyp != "HYP-0006" else common; btc = [[btc_by_ts[b.timestamp] for b in s] for s in segs] if hyp == "HYP-0006" else None
                    row["assets"][symbol] = summarize_segments(segs, hyp, params, FEE_GRID[0][1], FEE_GRID[0][2], delay, btc)["aggregate"]
                data["timing"].append(row)
            for symbol in targets:
                segs = loaded[symbol]["segments"] if hyp != "HYP-0006" else common; btc = [[btc_by_ts[b.timestamp] for b in s] for s in segs] if hyp == "HYP-0006" else None
                base = summarize_segments(segs, hyp, params, FEE_GRID[0][1], FEE_GRID[0][2], 1, btc)
                data["baseline_details"][symbol] = base; data["concentration_drawdown"][symbol] = concentration_and_dd(base["segments"])
                valid = [d for d in base["segments"] if d["aggregate"] and d["aggregate"]["events"]]; loo = []
                for omit in range(len(valid)):
                    kept = [Decimal(d["aggregate"]["compound_return"]) for j, d in enumerate(valid) if j != omit]; growth = Decimal("1")
                    for r in kept: growth *= 1 + r
                    loo.append({"omitted_segment": valid[omit]["segment"], "compound_return": str(growth - 1) if kept else "0"})
                data["sample_size"][symbol] = {"leave_one_out": loo}
            report["decisions"][hyp] = data
    final = {}
    for hyp, data in report["decisions"].items():
        targets = ["BTCUSDT", "ETHUSDT"] if hyp != "HYP-0006" else ["ETHUSDT"]; checks = []
        for symbol in targets:
            b = data["baseline_details"][symbol]["aggregate"]; positive = Decimal(b["compound_return"]) > 0 and Decimal(b["mean_segment_return"]) > 0
            vals = [r["assets"][symbol] for r in data["parameter_cells"] if r["assets"].get(symbol) and r["assets"][symbol]["events"]]; param_pass = bool(vals) and sum(Decimal(v["mean_segment_return"]) > 0 for v in vals) / len(vals) >= Decimal("0.60") and sum(Decimal(v["compound_return"]) > 0 for v in vals) / len(vals) >= Decimal("0.50")
            stress = data["fee_slippage"][-1]["assets"][symbol]; fee_pass = stress and Decimal(stress["compound_return"]) > 0 and Decimal(stress["mean_segment_return"]) > 0
            timing = data["timing"][1]["assets"][symbol]; timing_pass = timing and Decimal(timing["compound_return"]) > 0 and Decimal(timing["mean_segment_return"]) > 0
            loo = data["sample_size"][symbol]["leave_one_out"]; loo_pass = positive and bool(loo) and sum(Decimal(x["compound_return"]) > 0 for x in loo) / len(loo) >= Decimal("0.75")
            conc = data["concentration_drawdown"][symbol]; seg_pass = bool(conc["segments"]) and max(Decimal(x["positive_log_contribution"]) for x in conc["segments"]) <= Decimal("0.50"); trade_pass = conc["top_10_positive_event_pnl_fraction"] is not None and Decimal(conc["top_10_positive_event_pnl_fraction"]) <= Decimal("0.50")
            dd_pass = Decimal(conc["max_drawdown"]) < Decimal("0.70") and Decimal(conc["worst_segment_return"]) > Decimal("-0.50") and Decimal(conc["longest_recovery_events"]) / Decimal(max(conc["eligible_events"], 1)) <= Decimal("0.50")
            checks.append({"asset": symbol, "baseline": positive, "parameter_neighborhood": param_pass, "fee_slippage": fee_pass, "timing": timing_pass, "sample_size": loo_pass, "concentration": seg_pass and trade_pass, "drawdown_recovery": dd_pass})
        final[hyp] = {"checks": checks, "decision": "ROBUSTNESS_PASS" if all(all(v for k, v in c.items() if k != "asset") for c in checks) else "ROBUSTNESS_FAIL"}
    report["final"] = final; (output / "next_cycle_results.json").write_text(json.dumps(report, sort_keys=True, indent=2, default=str), encoding="utf-8")
    print("GATE2 NEXT CYCLE COMPLETE"); print(json.dumps({"final": final, "preregistration_sha256": prereg_sha, "oos_accessed": False}, sort_keys=True))


if __name__ == "__main__": main()
