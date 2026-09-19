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
from zipfile import ZipFile

from research_core.backtesting import BacktestConfig, run_backtest
from research_core.data_ingestion import archive_url, checksum_url, verify_sha256_bytes, parse_timestamp
from research_core.data_interfaces import MarketBar
from research_core.data_quality import scan_archive
from research_core.data_quality_treatment_v2 import build_manifest
from research_core.metrics import calculate_metrics

START = datetime(2017, 8, 17, tzinfo=timezone.utc)
END = datetime(2022, 1, 1, tzinfo=timezone.utc)
CASH = Decimal("1000")
BASE_FEE = Decimal("0.001")
BASE_SLIP = Decimal("0.0005")
PERIODS_PER_YEAR = 8760
PREREG_PATH = Path("docs/GATE2_ROBUSTNESS_PREREGISTRATION_V1.md")
ROOT = Path(__file__).resolve().parents[1]

BASE = {
    "HYP-0001": {"name": "time_series_momentum", "lookback": 168, "confirmation": 24},
    "HYP-0002": {"name": "short_horizon_mean_reversion", "lookback": 48, "entry": Decimal("-0.02"), "exit": Decimal("-0.005")},
    "HYP-0003": {"name": "volatility_range_breakout", "lookback": 24, "range_lookback": 24, "threshold": Decimal("0.01")},
    "HYP-0004": {"name": "trend_pullback", "ema": 200, "slope": 24, "trigger": 24},
}

PARAM_GRID = {
    "HYP-0001": {"lookback": [120, 168, 216], "confirmation": [12, 24, 36]},
    "HYP-0002": {"lookback": [36, 48, 60], "entry": [Decimal("-0.015"), Decimal("-0.02"), Decimal("-0.025")], "exit": [Decimal("-0.0025"), Decimal("-0.005"), Decimal("-0.0075")]},
    "HYP-0003": {"lookback": [18, 24, 30], "range_lookback": [18, 24, 30], "threshold": [Decimal("0.0075"), Decimal("0.01"), Decimal("0.0125")]},
    "HYP-0004": {"ema": [160, 200, 240], "slope": [12, 24, 36], "trigger": [18, 24, 30]},
}
COST_GRID = [("baseline", BASE_FEE, BASE_SLIP), ("stress_1", Decimal("0.0015"), Decimal("0.001")), ("stress_2", Decimal("0.0025"), Decimal("0.0015"))]
TIMING_GRID = [1, 2]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def months(start: datetime, end: datetime):
    y, m = start.year, start.month
    while (y, m) < (end.year, end.month):
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


def fetch(url: str, attempts: int = 3) -> bytes:
    last = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=90) as response:
                return response.read()
        except Exception as exc:
            last = exc
            if attempt + 1 < attempts:
                time.sleep(2 ** attempt)
    raise last


def parse_valid_bars(path: Path, symbol: str, valid_timestamps: set[datetime]) -> list[MarketBar]:
    bars = []
    with ZipFile(path) as archive:
        member = [n for n in archive.namelist() if not n.endswith("/")][0]
        text = archive.read(member).decode("utf-8")
    for row in csv.reader(text.splitlines()):
        if not row or len(row) < 6 or row[0].strip().lower() in {"open time", "timestamp"}:
            continue
        try:
            ts, _ = parse_timestamp(row[0])
            if ts not in valid_timestamps or not (START <= ts < END):
                continue
            values = [Decimal(x) for x in row[1:6]]
            bars.append(MarketBar(ts, "BTC/USDT" if symbol == "BTCUSDT" else "ETH/USDT", *values))
        except (ValueError, InvalidOperation):
            continue
    return bars


def in_break(ts, breaks) -> bool:
    return any(datetime.fromisoformat(b.start) <= ts < datetime.fromisoformat(b.end) for b in breaks)


def continuous_segments(bars, breaks):
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
    return [x for x in out if x]


def sma(values, n, i):
    return sum(values[i - n + 1:i + 1], Decimal("0")) / Decimal(n)


def ema(values, n):
    alpha = Decimal("2") / Decimal(n + 1)
    out = [values[0]]
    for value in values[1:]:
        out.append(alpha * value + (Decimal("1") - alpha) * out[-1])
    return out


def signal_targets(name: str, bars: list[MarketBar], p: dict) -> list[Decimal]:
    closes = [b.close for b in bars]
    targets = [Decimal("0")] * len(bars)
    active = False
    if name == "time_series_momentum":
        n, confirm = p["lookback"], p["confirmation"]
        for i in range(max(n, confirm), len(bars)):
            targets[i] = Decimal("1") if closes[i] / closes[i-n] - 1 > 0 and closes[i] / closes[i-confirm] - 1 > 0 else Decimal("0")
    elif name == "short_horizon_mean_reversion":
        n, entry, exit_ = p["lookback"], p["entry"], p["exit"]
        for i in range(n - 1, len(bars)):
            dev = closes[i] / sma(closes, n, i) - 1
            if active and dev >= exit_:
                active = False
            elif not active and dev <= entry:
                active = True
            targets[i] = Decimal("1") if active else Decimal("0")
    elif name == "volatility_range_breakout":
        n, rn, threshold = p["lookback"], p["range_lookback"], p["threshold"]
        for i in range(max(n, rn), len(bars)):
            prior_high = max(closes[i-n:i])
            prior_low = min(closes[i-n:i])
            window = bars[i-rn+1:i+1]
            normalized_range = (max(b.high for b in window) - min(b.low for b in window)) / (sum((b.close for b in window), Decimal("0")) / Decimal(rn))
            if active and closes[i] < prior_low:
                active = False
            elif not active and closes[i] > prior_high and normalized_range >= threshold:
                active = True
            targets[i] = Decimal("1") if active else Decimal("0")
    elif name == "trend_pullback":
        en, slope, trigger = p["ema"], p["slope"], p["trigger"]
        trend = ema(closes, en)
        start = max(en - 1, slope + trigger - 1)
        for i in range(start, len(bars)):
            sma_now = sma(closes, trigger, i)
            sma_prev = sma(closes, trigger, i - 1)
            regime = trend[i] > trend[i-slope] and closes[i] > trend[i]
            cross_up = closes[i-1] <= sma_prev and closes[i] > sma_now
            if active and (closes[i] < sma_now or not regime):
                active = False
            elif not active and regime and cross_up:
                active = True
            targets[i] = Decimal("1") if active else Decimal("0")
    else:
        raise ValueError(f"unknown hypothesis {name}")
    return targets


def run_cell(segment, name, params, fee, slip, delay):
    targets = signal_targets(name, segment, params)
    result = run_backtest(segment, targets, BacktestConfig(CASH, fee, slip, execution_delay_bars=delay))
    metrics = calculate_metrics(result.equity, result.trade_pnls, result.positions, periods_per_year=PERIODS_PER_YEAR)
    return result, metrics


def aggregate(metrics_list):
    returns = [m.total_return for m in metrics_list]
    compounded = Decimal("1")
    for r in returns:
        if r <= -1:
            raise ValueError("segment return <= -100% cannot be compounded")
        compounded *= 1 + r
    return {
        "segments": len(returns),
        "compound_return": str(compounded - 1),
        "mean_segment_return": str(sum(returns, Decimal("0")) / Decimal(len(returns))) if returns else "0",
        "positive_segment_fraction": str(Decimal(sum(r > 0 for r in returns)) / Decimal(len(returns))) if returns else "0",
        "max_segment_drawdown": str(max((m.max_drawdown for m in metrics_list), default=Decimal("0"))),
        "trade_count": sum(m.trade_count for m in metrics_list),
    }


def cartesian(grid: dict):
    keys = list(grid)
    def rec(i, current):
        if i == len(keys):
            yield dict(current)
            return
        for value in grid[keys[i]]:
            current[keys[i]] = value
            yield from rec(i + 1, current)
    yield from rec(0, {})


def cell_summary(asset, hyp, label, params, segments, fee, slip, delay=1):
    parts, results = [], []
    try:
        for idx, segment in enumerate(segments):
            required = max(params.values()) if all(isinstance(v, int) for v in params.values()) else 0
            if len(segment) < required + 2:
                continue
            result, metrics = run_cell(segment, BASE[hyp]["name"], params, fee, slip, delay)
            parts.append(metrics)
            results.append(result)
        if not parts:
            raise ValueError("no eligible segments")
        return {"asset": asset, "hypothesis": hyp, "cell": label, "parameters": {k: str(v) for k, v in params.items()}, "fee": str(fee), "slippage": str(slip), "delay_bars": delay, "aggregate": aggregate(parts), "error": None, "results": results}
    except Exception as exc:
        return {"asset": asset, "hypothesis": hyp, "cell": label, "parameters": {k: str(v) for k, v in params.items()}, "fee": str(fee), "slippage": str(slip), "delay_bars": delay, "aggregate": None, "error": f"{type(exc).__name__}: {exc}", "results": []}


def max_recovery_duration(equity):
    peak = equity[0]
    peak_index = 0
    longest = 0
    for i, value in enumerate(equity):
        if value >= peak:
            peak = value
            peak_index = i
        elif peak_index >= 0:
            longest = max(longest, i - peak_index)
    return longest


def regime_returns(result, bars):
    regimes = {"bull": [], "bear": [], "neutral": []}
    for i in range(1, len(result.equity)):
        if i < 168:
            continue
        ret168 = bars[i].close / bars[i-168].close - 1
        regime = "bull" if ret168 > Decimal("0.10") else "bear" if ret168 < Decimal("-0.10") else "neutral"
        regimes[regime].append(result.equity[i] / result.equity[i-1] - 1)
    out = {}
    for regime, returns in regimes.items():
        growth = Decimal("1")
        for r in returns:
            growth *= 1 + r
        out[regime] = {"bars": len(returns), "return": str(growth - 1)}
    return out


def main():
    prereg = ROOT / PREREG_PATH
    if not prereg.exists():
        raise RuntimeError(f"missing robustness preregistration: {PREREG_PATH}")
    prereg_sha = sha256_file(prereg)
    output = Path("gate2_robustness_results")
    output.mkdir(exist_ok=True)
    report = {
        "experiment_version": "gate2-robustness-v1",
        "code_commit": os.environ.get("GITHUB_SHA", "UNKNOWN"),
        "preregistration": {"path": str(PREREG_PATH), "sha256": prereg_sha},
        "development_window": [START.isoformat(), END.isoformat()],
        "validation_or_oos_accessed": False,
        "dimensions": {},
        "assets": {},
    }
    with tempfile.TemporaryDirectory(prefix="gate2-robust-") as directory:
        root = Path(directory)
        for symbol in ("BTCUSDT", "ETHUSDT"):
            reports, paths = [], []
            for year, month in months(START, END):
                url = archive_url(symbol, year, month)
                payload = fetch(url)
                checksum = fetch(checksum_url(url)).decode("utf-8")
                if not verify_sha256_bytes(payload, checksum):
                    raise RuntimeError(f"checksum mismatch: {url}")
                path = root / symbol / Path(url).name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
                reports.append(scan_archive(path, symbol, True))
                paths.append(path)
            manifest = build_manifest(symbol, reports, START, END)
            bars = []
            for scan, path in zip(reports, paths):
                bars.extend(parse_valid_bars(path, symbol, set(scan.valid_timestamps)))
            bars.sort(key=lambda b: b.timestamp)
            segments = continuous_segments(bars, manifest.continuity_breaks)
            asset = {"dataset_identity": manifest.dataset_identity, "source_integrity": manifest.source_integrity, "certification": manifest.research_certification, "segment_count": len(segments), "dimensions": {}}

            # Fixed parameter neighborhood. Every Cartesian cell is attempted and retained.
            for hyp in BASE:
                cells = []
                for idx, params in enumerate(cartesian(PARAM_GRID[hyp])):
                    cells.append(cell_summary(symbol, hyp, f"parameter_{idx:03d}", params, segments, BASE_FEE, BASE_SLIP, 1))
                asset["dimensions"].setdefault("parameter_neighborhood", {})[hyp] = cells

            # Fee/slippage stress, timing, and baseline are fixed cells.
            base_params = {k: v for k, v in BASE.items()}
            asset["dimensions"]["fee_slippage"] = {}
            asset["dimensions"]["timing"] = {}
            for hyp, params in base_params.items():
                asset["dimensions"]["fee_slippage"][hyp] = [cell_summary(symbol, hyp, label, params, segments, fee, slip, 1) for label, fee, slip in COST_GRID]
                asset["dimensions"]["timing"][hyp] = [cell_summary(symbol, hyp, f"delay_{delay}", params, segments, BASE_FEE, BASE_SLIP, delay) for delay in TIMING_GRID]

            # Baseline detailed evidence used by regime, concentration, drawdown and LOO dimensions.
            baseline_detail = {}
            for hyp, params in BASE.items():
                seg_details = []
                for idx, segment in enumerate(segments):
                    try:
                        result, metrics = run_cell(segment, params["name"], params, BASE_FEE, BASE_SLIP, 1)
                        seg_details.append({"segment": idx, "metrics": metrics, "result": result, "bars": segment})
                    except Exception as exc:
                        seg_details.append({"segment": idx, "error": f"{type(exc).__name__}: {exc}", "result": None, "bars": segment})
                baseline_detail[hyp] = seg_details

            # Regime dimension: classify causal 168h close-to-close regime and attribute realized equity changes.
            regime = {}
            for hyp, details in baseline_detail.items():
                combined = {"bull": [], "bear": [], "neutral": []}
                for d in details:
                    if d.get("result") is not None:
                        rr = regime_returns(d["result"], d["bars"])
                        for r in combined:
                            combined[r].append(rr[r])
                regime[hyp] = {}
                for r in combined:
                    vals = combined[r]
                    growth = Decimal("1")
                    bars_count = 0
                    for v in vals:
                        growth *= 1 + Decimal(v["return"])
                        bars_count += int(v["bars"])
                    regime[hyp][r] = {"bars": bars_count, "return": str(growth - 1)}
            asset["dimensions"]["regime"] = regime

            # Sample size: leave-one-segment-out. No result-driven segment exclusion.
            loo = {}
            for hyp, details in baseline_detail.items():
                valid = [d for d in details if d.get("result") is not None]
                variants = []
                for omitted in range(len(valid)):
                    kept = [d["metrics"] for j, d in enumerate(valid) if j != omitted]
                    variants.append({"omitted_segment": valid[omitted]["segment"], "aggregate": aggregate(kept) if kept else None})
                loo[hyp] = variants
            asset["dimensions"]["sample_size_leave_one_out"] = loo

            # Concentration and drawdown/recovery, using exact baseline segment/trade evidence.
            concentration, drawdown = {}, {}
            for hyp, details in baseline_detail.items():
                seg_returns = [d["metrics"].total_return for d in details if d.get("result") is not None]
                positive_log_total = sum((Decimal(1 + r).ln() for r in seg_returns if r > -1 and r > 0), Decimal("0"))
                seg_contrib = []
                all_pnls = []
                longest_recovery = 0
                worst_segment = Decimal("0")
                max_dd = Decimal("0")
                for d in details:
                    if d.get("result") is None:
                        continue
                    m, result = d["metrics"], d["result"]
                    r = m.total_return
                    contrib = (Decimal(1 + r).ln() / positive_log_total) if positive_log_total > 0 and r > 0 else Decimal("0")
                    seg_contrib.append({"segment": d["segment"], "return": str(r), "positive_log_contribution": str(contrib)})
                    all_pnls.extend(result.trade_pnls)
                    longest_recovery = max(longest_recovery, max_recovery_duration(result.equity))
                    worst_segment = min(worst_segment, r)
                    max_dd = max(max_dd, m.max_drawdown)
                all_pnls.sort(reverse=True)
                top_n = math.ceil(len(all_pnls) * 0.10) if all_pnls else 0
                positive_trade_total = sum((p for p in all_pnls if p > 0), Decimal("0"))
                top_trade_positive = sum((max(p, Decimal("0")) for p in all_pnls[:top_n]), Decimal("0"))
                concentration[hyp] = {"segments": seg_contrib, "top_10_percent_trade_count": top_n, "top_10_positive_trade_pnl_fraction": str(top_trade_positive / positive_trade_total) if positive_trade_total > 0 else None}
                total_bars = sum(len(d["bars"]) for d in details)
                drawdown[hyp] = {"max_drawdown": str(max_dd), "worst_segment_return": str(worst_segment), "longest_recovery_bars": longest_recovery, "eligible_bars": total_bars, "longest_recovery_fraction": str(Decimal(longest_recovery) / Decimal(total_bars)) if total_bars else None}
            asset["dimensions"]["concentration"] = concentration
            asset["dimensions"]["drawdown_recovery"] = drawdown

            report["assets"][symbol] = asset

    # Deterministic pass/fail classification. Fail closed on missing/error/non-positive evidence.
    decisions = {}
    for symbol, asset in report["assets"].items():
        decisions[symbol] = {}
        for hyp in BASE:
            base_cell = cell_summary(symbol, hyp, "baseline_recomputed", BASE[hyp], [d["bars"] for d in baseline_detail[hyp] if d.get("result") is not None], BASE_FEE, BASE_SLIP, 1)
            base_agg = base_cell["aggregate"]
            baseline_positive = base_agg is not None and Decimal(base_agg["compound_return"]) > 0
            parameter_cells = asset["dimensions"]["parameter_neighborhood"][hyp]
            valid = [c for c in parameter_cells if c["aggregate"] is not None]
            parameter_pass = bool(valid) and sum(Decimal(c["aggregate"]["mean_segment_return"]) > 0 for c in valid) / len(valid) >= 0.60 and sum(Decimal(c["aggregate"]["compound_return"]) > 0 for c in valid) / len(valid) >= 0.60
            stress = asset["dimensions"]["fee_slippage"][hyp][-1]
            fee_pass = stress["aggregate"] is not None and Decimal(stress["aggregate"]["mean_segment_return"]) > 0 and Decimal(stress["aggregate"]["compound_return"]) > 0
            timing = asset["dimensions"]["timing"][hyp][1]
            timing_pass = timing["aggregate"] is not None and Decimal(timing["aggregate"]["mean_segment_return"]) > 0 and Decimal(timing["aggregate"]["compound_return"]) > 0
            regimes = asset["dimensions"]["regime"][hyp]
            regime_positive = sum(Decimal(v["return"]) > 0 for v in regimes.values() if v["bars"] >= 100)
            regime_pass = regime_positive >= 2 and not (baseline_positive and sum(Decimal(v["return"]) > 0 for v in regimes.values()) == 1)
            loo = asset["dimensions"]["sample_size_leave_one_out"][hyp]
            loo_pass = baseline_positive and bool(loo) and sum(Decimal(v["aggregate"]["compound_return"]) > 0 for v in loo if v["aggregate"]) / len(loo) >= 0.75
            conc = asset["dimensions"]["concentration"][hyp]
            seg_contribs = [Decimal(v["positive_log_contribution"]) for v in conc["segments"]]
            concentration_pass = bool(seg_contribs) and max(seg_contribs) <= Decimal("0.50") and conc["top_10_positive_trade_pnl_fraction"] is not None and Decimal(conc["top_10_positive_trade_pnl_fraction"]) <= Decimal("0.50")
            dd = asset["dimensions"]["drawdown_recovery"][hyp]
            dd_pass = Decimal(dd["max_drawdown"]) < Decimal("0.70") and Decimal(dd["worst_segment_return"]) > Decimal("-0.50") and dd["longest_recovery_fraction"] is not None and Decimal(dd["longest_recovery_fraction"]) <= Decimal("0.50")
            decisions[symbol][hyp] = {"baseline_positive": baseline_positive, "parameter_neighborhood": parameter_pass, "fee_slippage": fee_pass, "timing_2_bar": timing_pass, "regime": regime_pass, "sample_size": loo_pass, "concentration": concentration_pass, "drawdown_recovery": dd_pass}
    report["decisions"] = decisions
    report["overall"] = "PASS" if all(all(all(v.values()) for v in hs.values()) for hs in decisions.values()) else "FAIL"
    (output / "robustness_results.json").write_text(json.dumps(report, default=str, sort_keys=True, indent=2), encoding="utf-8")
    print("GATE2 ROBUSTNESS EXPERIMENTS COMPLETE")
    print(json.dumps({"overall": report["overall"], "decisions": report["decisions"], "preregistration_sha256": prereg_sha}, sort_keys=True))


if __name__ == "__main__":
    main()
