from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gate2_next_cycle_experiments import (
    START, END, FEE_GRID, DELAYS, months, fetch, parse_valid_bars,
    continuous_segments, event_return, sha256_file, max_drawdown, longest_recovery,
)
from research_core.data_ingestion import archive_url, checksum_url, verify_sha256_bytes
from research_core.data_quality import scan_archive
from research_core.data_quality_treatment_v2 import build_manifest

PREREG = Path("docs/GATE2_CYCLE7_PREREGISTRATION_V1.md")
ROOT = Path(__file__).resolve().parents[1]

GRID = {
    "HYP-0023": {
        "abnormal_24h": [Decimal("0.05"), Decimal("0.10")],
        "hourly_threshold": [Decimal("0"), Decimal("0.005")],
        "hold_bars": [6, 12, 24],
    },
    "HYP-0024": {
        "compression_quantile": [Decimal("0.20"), Decimal("0.30")],
        "breakout_buffer": [Decimal("0"), Decimal("0.0025")],
        "hold_bars": [12, 24],
    },
    "HYP-0025": {
        "parent_body_ratio": [Decimal("0.50"), Decimal("0.70")],
        "close_location": [Decimal("0.50"), Decimal("0.75")],
        "hold_bars": [6, 12],
    },
}

BASE = {
    "HYP-0023": {"abnormal_24h": Decimal("0.10"), "hourly_threshold": Decimal("0.005"), "hold_bars": 12},
    "HYP-0024": {"compression_quantile": Decimal("0.20"), "breakout_buffer": Decimal("0.0025"), "hold_bars": 12},
    "HYP-0025": {"parent_body_ratio": Decimal("0.50"), "close_location": Decimal("0.75"), "hold_bars": 12},
}


def cartesian(grid):
    keys = list(grid)
    out = []
    def rec(i, cur):
        if i == len(keys):
            out.append(dict(cur))
            return
        for value in grid[keys[i]]:
            cur[keys[i]] = value
            rec(i + 1, cur)
    rec(0, {})
    return out


def compound(returns):
    growth = Decimal("1")
    for r in returns:
        growth *= Decimal("1") + Decimal(r)
    return growth - Decimal("1")


def hourly_return(bars, i):
    return bars[i].close / bars[i - 1].close - Decimal("1")


def close_location(bar):
    rng = bar.high - bar.low
    return Decimal("0") if rng <= 0 else (bar.close - bar.low) / rng


def range_ratio_24h(bars, end_i):
    if end_i < 23:
        return None
    window = bars[end_i - 23:end_i + 1]
    hi = max(x.high for x in window)
    lo = min(x.low for x in window)
    return (hi - lo) / bars[end_i].close if bars[end_i].close > 0 else None


def compression_rank(bars, signal_i):
    # Latest completed pre-signal 24h window ends at signal_i-1.
    # Reference distribution is the prior 720 completed 24h-window ratios,
    # excluding the latest ratio itself and all future information.
    latest_end = signal_i - 1
    latest = range_ratio_24h(bars, latest_end)
    if latest is None or signal_i < 744:
        return None
    refs = []
    for end_i in range(signal_i - 721, signal_i - 1):
        value = range_ratio_24h(bars, end_i)
        if value is None:
            return None
        refs.append(value)
    if len(refs) != 720:
        return None
    return Decimal(sum(x <= latest for x in refs)) / Decimal(len(refs))


def build_cycle7_feature_cache(bars):
    """Precompute causal HYP-0024 features once for a continuous segment.

    This is an implementation optimization only. Each cached value uses the
    exact same historical windows as compression_rank() and condition().
    """
    range_ratios = [None] * len(bars)
    for end_i in range(23, len(bars)):
        window = bars[end_i - 23:end_i + 1]
        hi = max(x.high for x in window)
        lo = min(x.low for x in window)
        range_ratios[end_i] = (hi - lo) / bars[end_i].close if bars[end_i].close > 0 else None

    prior_high_24 = [None] * len(bars)
    for signal_i in range(24, len(bars)):
        prior_high_24[signal_i] = max(x.high for x in bars[signal_i - 24:signal_i])

    compression_ranks = [None] * len(bars)
    for signal_i in range(744, len(bars)):
        latest = range_ratios[signal_i - 1]
        if latest is None:
            continue
        refs = range_ratios[signal_i - 721:signal_i - 1]
        if len(refs) != 720 or any(value is None for value in refs):
            continue
        compression_ranks[signal_i] = Decimal(sum(value <= latest for value in refs)) / Decimal(720)

    return {
        "compression_rank": compression_ranks,
        "prior_high_24": prior_high_24,
    }


def condition(hyp, i, bars, params, features=None):
    if hyp == "HYP-0023":
        if i < 24:
            return False
        trailing = bars[i].close / bars[i - 24].close - Decimal("1")
        return trailing >= params["abnormal_24h"] and hourly_return(bars, i) >= params["hourly_threshold"]

    if hyp == "HYP-0024":
        if i < 744:
            return False
        if features is None:
            rank = compression_rank(bars, i)
            prior_high = max(x.high for x in bars[i - 24:i])
        else:
            rank = features["compression_rank"][i]
            prior_high = features["prior_high_24"][i]
        if rank is None or rank > params["compression_quantile"]:
            return False
        return bars[i].close >= prior_high * (Decimal("1") + params["breakout_buffer"])

    if hyp == "HYP-0025":
        if i < 1:
            return False
        parent = bars[i - 1]
        current = bars[i]
        parent_range = parent.high - parent.low
        if parent_range <= 0 or parent.close >= parent.open or current.close <= current.open:
            return False
        if (parent.open - parent.close) / parent_range < params["parent_body_ratio"]:
            return False
        inside = current.open >= parent.close and current.close <= parent.open
        return inside and close_location(current) >= params["close_location"]

    raise ValueError(hyp)


def simulate(segment, hyp, params, fee, slip, delay, features=None):
    if delay not in (1, 2):
        raise ValueError("delay must be 1 or 2")
    hold = int(params["hold_bars"])
    if hold <= 0:
        raise ValueError("hold_bars must be positive")
    events = []
    i = 1
    while i < len(segment):
        if not condition(hyp, i, segment, params, features):
            i += 1
            continue
        entry_i = i + delay
        exit_i = entry_i + hold - 1
        if exit_i >= len(segment):
            break
        r = event_return(segment[entry_i], segment[exit_i], fee, slip)
        events.append({
            "signal_index": i,
            "entry_index": entry_i,
            "exit_index": exit_i,
            "signal_timestamp": segment[i].timestamp.isoformat(),
            "entry_timestamp": segment[entry_i].timestamp.isoformat(),
            "exit_timestamp": segment[exit_i].timestamp.isoformat(),
            "hold_bars": hold,
            "return": str(r),
        })
        i = exit_i + 1
    return events


def details(segments, hyp, params, fee, slip, delay, features_by_segment=None):
    out = []
    for idx, segment in enumerate(segments):
        try:
            features = features_by_segment[idx] if features_by_segment is not None else None
            events = simulate(segment, hyp, params, fee, slip, delay, features)
            returns = [Decimal(e["return"]) for e in events]
            out.append({
                "segment": idx,
                "aggregate": {"events": len(events), "compound_return": str(compound(returns))},
                "events": events,
                "error": None,
            })
        except Exception as exc:
            out.append({"segment": idx, "aggregate": None, "events": [], "error": f"{type(exc).__name__}: {exc}"})
    return out


def summarize(ds):
    valid = [d for d in ds if d["aggregate"] and d["aggregate"]["events"]]
    event_returns = [Decimal(e["return"]) for d in valid for e in d["events"]]
    segment_returns = [Decimal(d["aggregate"]["compound_return"]) for d in valid]
    return {
        "events": len(event_returns),
        "compound_return": str(compound(event_returns)),
        "mean_event_return": str(sum(event_returns, Decimal("0")) / Decimal(len(event_returns))) if event_returns else "0",
        "positive_event_fraction": str(Decimal(sum(x > 0 for x in event_returns)) / Decimal(len(event_returns))) if event_returns else "0",
        "mean_segment_return": str(sum(segment_returns, Decimal("0")) / Decimal(len(segment_returns))) if segment_returns else "0",
        "eligible_segments": len(valid),
    }


def regime(ds, segments):
    buckets = {"bull": [], "neutral": [], "bear": []}
    eligible_signals = {"bull": 0, "neutral": 0, "bear": 0}
    for d, segment in zip(ds, segments):
        for e in d["events"]:
            i = e["signal_index"]
            if i < 168:
                continue
            trailing = segment[i].close / segment[i - 168].close - Decimal("1")
            key = "bull" if trailing > Decimal("0.10") else "bear" if trailing < Decimal("-0.10") else "neutral"
            buckets[key].append(Decimal(e["return"]))
            eligible_signals[key] += 1
    return {
        key: {
            "events": len(values),
            "compound_return": str(compound(values)),
            "mean_return": str(sum(values, Decimal("0")) / Decimal(len(values))) if values else "0",
            "positive": bool(values and compound(values) > 0),
        }
        for key, values in buckets.items()
    }


def leave_one_out(ds):
    active = [d for d in ds if d["aggregate"] and d["aggregate"]["events"]]
    variants = []
    for excluded in range(len(active)):
        returns = [
            Decimal(e["return"])
            for idx, d in enumerate(active)
            if idx != excluded
            for e in d["events"]
        ]
        c = compound(returns)
        variants.append({"excluded_active_segment": excluded, "events": len(returns), "compound_return": str(c), "above_cash": c > 0})
    passing = sum(v["above_cash"] for v in variants)
    return {
        "variants": variants,
        "pass_fraction": str(Decimal(passing) / Decimal(len(variants))) if variants else "0",
        "passing_variants": passing,
        "total_variants": len(variants),
    }


def concentration(ds):
    active = [d for d in ds if d["aggregate"] and d["aggregate"]["events"]]
    segment_returns = [(d["segment"], Decimal(d["aggregate"]["compound_return"])) for d in active]
    positive_logs = [(idx, (Decimal("1") + r).ln()) for idx, r in segment_returns if r > 0 and r > -1]
    total_log = sum(v for _, v in positive_logs)
    max_seg = max((v / total_log for _, v in positive_logs), default=Decimal("0")) if total_log > 0 else None
    positive_events = sorted((Decimal(e["return"]) for d in active for e in d["events"] if Decimal(e["return"]) > 0), reverse=True)
    total_pnl = sum(positive_events, Decimal("0"))
    top_n = max(1, (len(positive_events) + 9) // 10) if positive_events else 0
    top_fraction = sum(positive_events[:top_n], Decimal("0")) / total_pnl if total_pnl > 0 else None
    return {
        "positive_log_total": str(total_log),
        "max_single_segment_positive_log_contribution": str(max_seg) if max_seg is not None else None,
        "positive_event_pnl": str(total_pnl),
        "top_10_positive_event_pnl_fraction": str(top_fraction) if top_fraction is not None else None,
        "pass": max_seg is not None and top_fraction is not None and max_seg <= Decimal("0.50") and top_fraction <= Decimal("0.50"),
    }


def drawdown_recovery(ds, segments):
    active = [d for d in ds if d["aggregate"] and d["aggregate"]["events"]]
    max_dd = Decimal("0")
    worst_segment = Decimal("0")
    longest_recovery_hours = Decimal("0")
    eligible_events = 0
    eligible_duration_hours = sum(len(segment) for segment in segments)

    for d in active:
        segment = segments[d["segment"]]
        equity = [Decimal("1")]
        peak = Decimal("1")
        peak_time = None
        local_max_dd = Decimal("0")
        local_recovery_hours = Decimal("0")

        for event in d["events"]:
            r = Decimal(event["return"])
            equity.append(equity[-1] * (Decimal("1") + r))
            ts = datetime.fromisoformat(event["exit_timestamp"])
            if equity[-1] >= peak:
                peak = equity[-1]
                peak_time = ts
            else:
                local_max_dd = max(local_max_dd, (peak - equity[-1]) / peak if peak > 0 else Decimal("0"))
                if peak_time is not None:
                    local_recovery_hours = max(
                        local_recovery_hours,
                        Decimal((ts - peak_time).total_seconds()) / Decimal("3600"),
                    )

        if peak_time is not None and equity[-1] < peak:
            unresolved = Decimal((segment[-1].timestamp - peak_time).total_seconds()) / Decimal("3600")
            local_recovery_hours = max(local_recovery_hours, unresolved)

        seg_return = Decimal(d["aggregate"]["compound_return"])
        worst_segment = min(worst_segment, seg_return)
        max_dd = max(max_dd, local_max_dd)
        longest_recovery_hours = max(longest_recovery_hours, local_recovery_hours)
        eligible_events += len(d["events"])

    return {
        "max_drawdown": str(max_dd),
        "worst_segment_return": str(worst_segment),
        "longest_recovery_hours": str(longest_recovery_hours),
        "eligible_duration_hours": eligible_duration_hours,
        "eligible_events": eligible_events,
        "pass": bool(eligible_events)
            and max_dd < Decimal("0.70")
            and worst_segment >= Decimal("-0.50")
            and longest_recovery_hours <= Decimal("0.50") * Decimal(max(1, eligible_duration_hours)),
    }


def benchmark(segments, fee, slip):
    returns = []
    for segment in segments:
        if len(segment) < 2:
            continue
        returns.append(event_return(segment[0], segment[-1], fee, slip))
    return {
        "cash_compound_return": "0",
        "buy_hold_compound_return": str(compound(returns)),
        "eligible_segments": len(returns),
    }


def serial_params(params):
    return {k: str(v) for k, v in params.items()}


def find_cell(cells, params):
    target = serial_params(params)
    return next(x for x in cells if x["params"] == target)


def assess(hyp, report):
    assets = ("BTCUSDT", "ETHUSDT")
    base = BASE[hyp]
    dimensions = {}

    param_checks = []
    for asset in assets:
        cells = report["assets"][asset]["parameter_cells"][hyp]
        valid = [c for c in cells if not c["errors"] and c["baseline"]["summary"]["eligible_segments"] > 0]
        positive = [c for c in valid if Decimal(c["baseline"]["summary"]["mean_segment_return"]) > 0]
        compounds = sorted(Decimal(c["baseline"]["summary"]["compound_return"]) for c in valid)
        if compounds:
            n = len(compounds)
            med = compounds[n // 2] if n % 2 else (compounds[n // 2 - 1] + compounds[n // 2]) / Decimal("2")
        else:
            med = Decimal("0")
        frac = Decimal(len(positive)) / Decimal(len(valid)) if valid else Decimal("0")
        param_checks.append({"asset": asset, "valid_cells": len(valid), "positive_cells": len(positive), "positive_fraction": str(frac), "median_compound_return": str(med), "pass": frac >= Decimal("0.60") and med > 0})
    dimensions["parameter_neighborhood"] = {"checks": param_checks, "pass": all(x["pass"] for x in param_checks)}

    fee_checks, timing_checks, regime_checks, sample_checks, conc_checks, dd_checks, transfer_checks = [], [], [], [], [], [], []
    total_events = 0
    total_segments = 0
    protocol_asset_pass = []

    for asset in assets:
        cell = find_cell(report["assets"][asset]["parameter_cells"][hyp], base)
        baseline = cell["baseline"]["summary"]
        stress = next(x for x in cell["fee_slippage"] if x["fee_case"] == "stress_2")["summary"]
        timing = next(x for x in cell["timing"] if x["delay_bars"] == 2)["summary"]
        fee_pass = Decimal(stress["compound_return"]) > 0 and Decimal(stress["mean_segment_return"]) > 0
        timing_pass = Decimal(timing["compound_return"]) > 0 and Decimal(timing["mean_segment_return"]) > 0
        fee_checks.append({"asset": asset, "summary": stress, "pass": fee_pass})
        timing_checks.append({"asset": asset, "summary": timing, "pass": timing_pass})

        r = cell["regime"]
        qualifying = [v for v in r.values() if v["events"] >= 100]
        positive_q = [v for v in qualifying if v["positive"]]
        regime_pass = len(qualifying) >= 2 and len(positive_q) >= 2
        regime_checks.append({"asset": asset, "regimes": r, "qualifying_regimes": len(qualifying), "positive_qualifying_regimes": len(positive_q), "pass": regime_pass})

        loo = cell["leave_one_segment_out"]
        base_comp = Decimal(baseline["compound_return"])
        sample_pass = base_comp > 0 and Decimal(loo["pass_fraction"]) >= Decimal("0.75")
        sample_checks.append({"asset": asset, "loo": loo, "pass": sample_pass})

        conc = cell["concentration"]
        dd = cell["drawdown_recovery"]
        conc_checks.append({"asset": asset, "metrics": conc, "pass": conc["pass"]})
        dd_checks.append({"asset": asset, "metrics": dd, "pass": dd["pass"]})

        transfer_pass = base_comp > 0 and Decimal(baseline["mean_segment_return"]) > 0
        transfer_checks.append({"asset": asset, "summary": baseline, "pass": transfer_pass})

        total_events += int(baseline["events"])
        total_segments += int(baseline["eligible_segments"])
        protocol_asset_pass.append(
            base_comp >= Decimal("0.10")
            and Decimal(baseline["mean_segment_return"]) > 0
            and dd["pass"]
        )

    dimensions["fee_slippage"] = {"checks": fee_checks, "pass": all(x["pass"] for x in fee_checks)}
    dimensions["timing"] = {"checks": timing_checks, "pass": all(x["pass"] for x in timing_checks)}
    dimensions["regime"] = {"checks": regime_checks, "pass": all(x["pass"] for x in regime_checks)}
    dimensions["sample_stability"] = {"checks": sample_checks, "pass": all(x["pass"] for x in sample_checks)}
    dimensions["concentration"] = {"checks": conc_checks, "pass": all(x["pass"] for x in conc_checks)}
    dimensions["drawdown_recovery"] = {"checks": dd_checks, "pass": all(x["pass"] for x in dd_checks)}
    dimensions["asset_transferability"] = {"checks": transfer_checks, "pass": all(x["pass"] for x in transfer_checks)}

    protocol = {
        "economic_significance_each_asset": all(protocol_asset_pass),
        "combined_completed_trades": total_events,
        "combined_eligible_segments": total_segments,
        "sample_support": total_events >= 300 and total_segments >= 20,
    }
    protocol["pass"] = protocol["economic_significance_each_asset"] and protocol["sample_support"]
    dimensions["protocol_eligibility"] = protocol

    substantive = [
        "parameter_neighborhood", "fee_slippage", "timing", "regime",
        "sample_stability", "concentration", "drawdown_recovery",
        "asset_transferability", "protocol_eligibility",
    ]
    dimensions["overall"] = {
        "pass": all(dimensions[name]["pass"] for name in substantive),
        "required": substantive,
    }
    return dimensions


def main():
    total_cells = sum(len(cartesian(g)) for g in GRID.values())
    if total_cells != 28:
        raise RuntimeError(f"registered cell count mismatch: {total_cells}")

    report = {
        "experiment_version": "gate2-cycle7-v1",
        "github_sha": os.environ.get("GITHUB_SHA", "UNKNOWN"),
        "checked_out_sha": os.environ.get("CHECKED_OUT_SHA", "UNKNOWN"),
        "preregistration": {"path": str(PREREG), "sha256": sha256_file(ROOT / PREREG)},
        "development_window": [START.isoformat(), END.isoformat()],
        "validation_or_oos_accessed": False,
        "registered_parameter_cell_count": total_cells,
        "assets": {},
        "decisions": {},
    }

    with tempfile.TemporaryDirectory(prefix="gate2-cycle7-") as td:
        root = Path(td)
        loaded = {}
        for symbol in ("BTCUSDT", "ETHUSDT"):
            scans, paths = [], []
            for year, month in months(START, END):
                url = archive_url(symbol, year, month)
                payload = fetch(url)
                checksum = fetch(checksum_url(url)).decode("utf-8")
                if not verify_sha256_bytes(payload, checksum):
                    raise RuntimeError(f"checksum mismatch: {url}")
                path = root / symbol / Path(url).name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(payload)
                scans.append(scan_archive(path, symbol, True))
                paths.append(path)
            manifest = build_manifest(symbol, scans, START, END)
            bars = []
            for path, scan in zip(paths, scans):
                bars.extend(parse_valid_bars(path, symbol, set(scan.valid_timestamps)))
            bars.sort(key=lambda x: x.timestamp)
            loaded[symbol] = {
                "manifest": manifest,
                "segments": continuous_segments(bars, manifest.continuity_breaks),
            }

        for symbol, asset in loaded.items():
            segments = asset["segments"]
            features_by_segment = [build_cycle7_feature_cache(segment) for segment in segments]
            out = {
                "dataset_identity": asset["manifest"].dataset_identity,
                "source_integrity": asset["manifest"].source_integrity,
                "certification": asset["manifest"].research_certification,
                "benchmarks": benchmark(segments, Decimal("0.001"), Decimal("0.0005")),
                "parameter_cells": {},
            }
            for hyp, grid in GRID.items():
                out["parameter_cells"][hyp] = []
                for n, params in enumerate(cartesian(grid)):
                    base_ds = details(segments, hyp, params, Decimal("0.001"), Decimal("0.0005"), 1, features_by_segment)
                    cell = {
                        "cell": f"parameter_{n:03d}",
                        "params": serial_params(params),
                        "baseline": {"summary": summarize(base_ds)},
                        "errors": [d["error"] for d in base_ds if d["error"]],
                        "fee_slippage": [],
                        "timing": [],
                        "regime": regime(base_ds, segments),
                        "leave_one_segment_out": leave_one_out(base_ds),
                        "concentration": concentration(base_ds),
                        "drawdown_recovery": drawdown_recovery(base_ds, segments),
                    }
                    for label, fee, slip in FEE_GRID:
                        ds = details(segments, hyp, params, fee, slip, 1, features_by_segment)
                        cell["fee_slippage"].append({
                            "fee_case": label,
                            "commission": str(fee),
                            "slippage": str(slip),
                            "summary": summarize(ds),
                        })
                    for delay in DELAYS:
                        ds = details(segments, hyp, params, Decimal("0.001"), Decimal("0.0005"), delay, features_by_segment)
                        cell["timing"].append({"delay_bars": delay, "summary": summarize(ds)})
                    out["parameter_cells"][hyp].append(cell)
            report["assets"][symbol] = out

        report["robustness"] = {}
        for hyp in GRID:
            assessment = assess(hyp, report)
            report["robustness"][hyp] = assessment
            report["decisions"][hyp] = "PROMOTE_TO_VALIDATION" if assessment["overall"]["pass"] else "REJECT"
        report["decisions"]["overall"] = "CANDIDATE_AVAILABLE" if any(v == "PROMOTE_TO_VALIDATION" for k, v in report["decisions"].items() if k != "overall") else "NO_DEVELOPMENT_PROMOTION"

    outdir = Path("gate2_cycle7_results")
    outdir.mkdir(exist_ok=True)
    (outdir / "cycle7_results.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print("Gate 2 Cycle 7 evidence generated")


if __name__ == "__main__":
    main()
