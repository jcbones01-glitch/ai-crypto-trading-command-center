from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import time
import urllib.request
from dataclasses import asdict
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
COMMISSION = Decimal("0.001")
SLIPPAGE = Decimal("0.0005")
INITIAL = Decimal("1000")
PERIODS_PER_YEAR = 8760
EXPERIMENT_VERSION = "gate2-dev-v1"

HYPOTHESES = {
    "HYP-0001": {"name": "time_series_momentum", "lookback": 168},
    "HYP-0002": {"name": "short_horizon_mean_reversion", "lookback": 48},
    "HYP-0003": {"name": "volatility_range_breakout", "lookback": 24},
    "HYP-0004": {"name": "trend_pullback", "lookback": 224},
}


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
    bars: list[MarketBar] = []
    with ZipFile(path) as archive:
        member = [n for n in archive.namelist() if not n.endswith("/")][0]
        with archive.open(member, "r") as binary:
            text = binary.read().decode("utf-8")
    for row in csv.reader(text.splitlines()):
        if not row or len(row) < 6 or row[0].strip().lower() in {"open time", "timestamp"}:
            continue
        try:
            ts, _ = parse_timestamp(row[0])
            if ts not in valid_timestamps or not (START <= ts < END):
                continue
            values = [Decimal(x) for x in row[1:6]]
            bar = MarketBar(ts, "BTC/USDT" if symbol == "BTCUSDT" else "ETH/USDT", *values)
            bars.append(bar)
        except (ValueError, InvalidOperation):
            continue
    return bars


def in_break(ts: datetime, breaks) -> bool:
    return any(datetime.fromisoformat(b.start) <= ts < datetime.fromisoformat(b.end) for b in breaks)


def continuous_segments(bars: list[MarketBar], breaks) -> list[list[MarketBar]]:
    out: list[list[MarketBar]] = []
    current: list[MarketBar] = []
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
    return [segment for segment in out if segment]


def sma(values: list[Decimal], n: int, i: int) -> Decimal:
    return sum(values[i - n + 1:i + 1], Decimal("0")) / Decimal(n)


def ema(values: list[Decimal], n: int) -> list[Decimal]:
    alpha = Decimal("2") / Decimal(n + 1)
    out = [values[0]]
    for value in values[1:]:
        out.append(alpha * value + (Decimal("1") - alpha) * out[-1])
    return out


def signals(name: str, bars: list[MarketBar]) -> list[Decimal]:
    closes = [b.close for b in bars]
    targets = [Decimal("0")] * len(bars)
    active = False
    if name == "time_series_momentum":
        for i in range(167, len(bars)):
            targets[i] = Decimal("1") if closes[i] / closes[i-168] - Decimal("1") > 0 and closes[i] / closes[i-24] - Decimal("1") > 0 else Decimal("0")
    elif name == "short_horizon_mean_reversion":
        for i in range(47, len(bars)):
            dev = closes[i] / sma(closes, 48, i) - Decimal("1")
            if active and dev >= Decimal("-0.005"):
                active = False
            elif not active and dev <= Decimal("-0.02"):
                active = True
            targets[i] = Decimal("1") if active else Decimal("0")
    elif name == "volatility_range_breakout":
        for i in range(24, len(bars)):
            prior_high = max(closes[i-24:i])
            prior_low = min(closes[i-24:i])
            window = bars[i-23:i+1]
            normalized_range = (
              (max(b.high for b in window) - min(b.low for b in window))
    / (sum((b.close for b in window), Decimal("0")) / Decimal(24))
)
            if active and closes[i] < prior_low:
                active = False
            elif not active and closes[i] > prior_high and normalized_range >= Decimal("0.01"):
                active = True
            targets[i] = Decimal("1") if active else Decimal("0")
    elif name == "trend_pullback":
        trend = ema(closes, 200)
        for i in range(223, len(bars)):
            sma_now = sma(closes, 24, i)
            sma_prev = sma(closes, 24, i - 1)
            regime = trend[i] > trend[i-24] and closes[i] > trend[i]
            cross_up = closes[i-1] <= sma_prev and closes[i] > sma_now
            if active and (closes[i] < sma_now or not regime):
                active = False
            elif not active and regime and cross_up:
                active = True
            targets[i] = Decimal("1") if active else Decimal("0")
    return targets


def summarize_segment(strategy: str, bars: list[MarketBar], target: list[Decimal], segment_id: int) -> dict:
    config = BacktestConfig(INITIAL, COMMISSION, SLIPPAGE)
    result = run_backtest(bars, target, config)
    metrics = calculate_metrics(result.equity, result.trade_pnls, result.positions, periods_per_year=PERIODS_PER_YEAR)
    return {"segment": segment_id, "start": bars[0].timestamp.isoformat(), "end": bars[-1].timestamp.isoformat(), "bars": len(bars), "metrics": {k: (str(v) if v is not None else None) for k, v in asdict(metrics).items()}}


def aggregate(parts: list[dict]) -> dict:
    returns = [Decimal(p["metrics"]["total_return"]) for p in parts]
    compounded = Decimal("1")
    for r in returns:
        compounded *= Decimal("1") + r
    return {"segments": len(parts), "compound_segment_return": str(compounded - Decimal("1")), "mean_segment_return": str(sum(returns, Decimal("0")) / Decimal(len(returns))) if returns else "0", "positive_segment_fraction": str(Decimal(sum(r > 0 for r in returns)) / Decimal(len(returns))) if returns else "0", "max_segment_drawdown": str(max(Decimal(p["metrics"]["max_drawdown"]) for p in parts)) if parts else "0", "trade_count": sum(int(p["metrics"]["trade_count"]) for p in parts)}


def main() -> None:
    output = Path("gate2_results")
    output.mkdir(exist_ok=True)
    all_results = {"experiment_version": EXPERIMENT_VERSION, "development_window": [START.isoformat(), END.isoformat()], "oos_accessed": False, "commission": str(COMMISSION), "slippage": str(SLIPPAGE), "initial_capital": str(INITIAL), "hypotheses": {}}
    with tempfile.TemporaryDirectory(prefix="gate2-dev-") as directory:
        root = Path(directory)
        for symbol in ("BTCUSDT", "ETHUSDT"):
            reports = []
            paths = []
            for year, month in months(START, END):
                url = archive_url(symbol, year, month)
                name = Path(url).name
                payload = fetch(url)
                checksum = fetch(checksum_url(url)).decode("utf-8")
                if not verify_sha256_bytes(payload, checksum):
                    raise RuntimeError(f"checksum mismatch: {name}")
                path = root / symbol / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
                report = scan_archive(path, symbol, True)
                reports.append(report)
                paths.append(path)
            manifest = build_manifest(symbol, reports, START, END)
            bars = []
            for report, path in zip(reports, paths):
                bars.extend(parse_valid_bars(path, symbol, set(report.valid_timestamps)))
            bars.sort(key=lambda b: b.timestamp)
            segments = continuous_segments(bars, manifest.continuity_breaks)
            symbol_results = {"dataset_identity": manifest.dataset_identity, "source_integrity": manifest.source_integrity, "certification": manifest.research_certification, "segments": len(segments), "hypotheses": {}}
            for hyp_id, spec in HYPOTHESES.items():
                parts = []
                for idx, segment in enumerate(segments):
                    if len(segment) < spec["lookback"] + 2:
                        continue
                    target = signals(spec["name"], segment)
                    parts.append(summarize_segment(spec["name"], segment, target, idx))
                symbol_results["hypotheses"][hyp_id] = {"name": spec["name"], "pre_registered_parameters": spec, "aggregate": aggregate(parts), "segments": parts}
            all_results["hypotheses"].setdefault(symbol, symbol_results)
    (output / "development_experiments.json").write_text(json.dumps(all_results, sort_keys=True, indent=2), encoding="utf-8")
    print("GATE2 DEVELOPMENT EXPERIMENTS COMPLETE")
    print(json.dumps({s: {h: v["aggregate"] for h, v in d["hypotheses"].items()} for s, d in all_results["hypotheses"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
