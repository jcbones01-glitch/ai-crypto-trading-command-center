from __future__ import annotations

import json
import math
import os
import sys
import tempfile
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gate2_next_cycle_experiments import (
    START,
    END,
    continuous_segments,
    fetch,
    months,
    parse_valid_bars,
    sha256_file,
)
from research_core.data_ingestion import archive_url, checksum_url, verify_sha256_bytes
from research_core.data_quality import scan_archive
from research_core.data_quality_treatment_v2 import build_manifest
from research_core.market_state import STATE_DEFINITION_VERSION, MarketState, build_market_states

PREREG = Path("docs/GATE2_CYCLE8_MARKET_STATE_PREREGISTRATION_V1.md")
ROOT = Path(__file__).resolve().parents[1]

VOL_LABELS = ("VOL_LOW", "VOL_NORMAL", "VOL_HIGH")
ACTIVITY_LABELS = ("ACTIVITY_LOW", "ACTIVITY_NORMAL", "ACTIVITY_HIGH")
TREND_LABELS = ("TREND_BEAR", "TREND_NEUTRAL", "TREND_BULL")


def nearest_rank_percentile(values: list[int], p: Decimal) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    rank = max(1, math.ceil(float(p) * len(ordered)))
    return ordered[rank - 1]


def occupancy(states: list[MarketState], attr: str, labels: tuple[str, ...]) -> dict:
    available = [getattr(state, attr) for state in states if getattr(state, attr) is not None]
    counts = Counter(available)
    denominator = len(available)
    return {
        "available_observations": denominator,
        "labels": {
            label: {
                "count": counts.get(label, 0),
                "fraction": str(
                    Decimal(counts.get(label, 0)) / Decimal(denominator)
                    if denominator
                    else Decimal("0")
                ),
            }
            for label in labels
        },
    }


def composite_occupancy(states: list[MarketState]) -> dict:
    complete = [state.composite for state in states if state.complete]
    counts = Counter(complete)
    denominator = len(complete)
    return {
        "available_observations": denominator,
        "states": {
            "|".join(key): {
                "count": count,
                "fraction": str(Decimal(count) / Decimal(denominator)) if denominator else "0",
            }
            for key, count in sorted(counts.items())
        },
    }


def transition_summary(states_by_segment: list[list[MarketState]], attr: str) -> dict:
    counts: dict[str, Counter] = defaultdict(Counter)
    for states in states_by_segment:
        for left, right in zip(states, states[1:]):
            a = getattr(left, attr)
            b = getattr(right, attr)
            if a is None or b is None:
                continue
            counts[a][b] += 1

    out = {}
    for source in sorted(counts):
        total = sum(counts[source].values())
        out[source] = {
            "outgoing": total,
            "destinations": {
                dest: {
                    "count": count,
                    "probability": str(Decimal(count) / Decimal(total)) if total else "0",
                }
                for dest, count in sorted(counts[source].items())
            },
        }
    return out


def composite_transition_summary(states_by_segment: list[list[MarketState]]) -> dict:
    counts: dict[str, Counter] = defaultdict(Counter)
    for states in states_by_segment:
        for left, right in zip(states, states[1:]):
            if not left.complete or not right.complete:
                continue
            a = "|".join(left.composite)
            b = "|".join(right.composite)
            counts[a][b] += 1

    out = {}
    for source in sorted(counts):
        total = sum(counts[source].values())
        out[source] = {
            "outgoing": total,
            "destinations": {
                dest: {
                    "count": count,
                    "probability": str(Decimal(count) / Decimal(total)) if total else "0",
                }
                for dest, count in sorted(counts[source].items())
            },
        }
    return out


def dwell_summary(states_by_segment: list[list[MarketState]], attr: str, labels: tuple[str, ...]) -> dict:
    runs: dict[str, list[int]] = {label: [] for label in labels}
    for states in states_by_segment:
        current = None
        length = 0
        for state in states:
            label = getattr(state, attr)
            if label is None:
                if current is not None:
                    runs[current].append(length)
                current, length = None, 0
                continue
            if label == current:
                length += 1
            else:
                if current is not None:
                    runs[current].append(length)
                current, length = label, 1
        if current is not None:
            runs[current].append(length)

    return {
        label: {
            "runs": len(lengths),
            "median_run_length": str(Decimal(str(__import__("statistics").median(lengths)))) if lengths else "0",
            "p90_run_length_nearest_rank": nearest_rank_percentile(lengths, Decimal("0.90")),
            "max_run_length": max(lengths) if lengths else 0,
        }
        for label, lengths in runs.items()
    }


def summarize_asset(segments, states_by_segment) -> dict:
    states = [state for segment_states in states_by_segment for state in segment_states]
    complete = [state for state in states if state.complete]
    total = len(states)

    unavailable = {
        "volatility_state_unavailable": sum(state.volatility_state is None for state in states),
        "activity_state_unavailable": sum(state.activity_state is None for state in states),
        "trend_state_unavailable": sum(state.trend_state is None for state in states),
        "complete_state_unavailable": sum(not state.complete for state in states),
        "continuity_segment_count": len(segments),
    }

    return {
        "total_certified_bars": total,
        "complete_state_observations": len(complete),
        "complete_state_fraction": str(Decimal(len(complete)) / Decimal(total)) if total else "0",
        "first_complete_timestamp": complete[0].timestamp.isoformat() if complete else None,
        "last_complete_timestamp": complete[-1].timestamp.isoformat() if complete else None,
        "unavailable": unavailable,
        "occupancy": {
            "volatility": occupancy(states, "volatility_state", VOL_LABELS),
            "activity": occupancy(states, "activity_state", ACTIVITY_LABELS),
            "trend": occupancy(states, "trend_state", TREND_LABELS),
            "composite": composite_occupancy(states),
        },
        "transitions": {
            "volatility": transition_summary(states_by_segment, "volatility_state"),
            "activity": transition_summary(states_by_segment, "activity_state"),
            "trend": transition_summary(states_by_segment, "trend_state"),
            "composite": composite_transition_summary(states_by_segment),
        },
        "dwell": {
            "volatility": dwell_summary(states_by_segment, "volatility_state", VOL_LABELS),
            "activity": dwell_summary(states_by_segment, "activity_state", ACTIVITY_LABELS),
            "trend": dwell_summary(states_by_segment, "trend_state", TREND_LABELS),
        },
    }


def synchronized_agreement(btc_states_by_segment, eth_states_by_segment) -> dict:
    btc = {
        state.timestamp: state
        for states in btc_states_by_segment
        for state in states
        if state.complete
    }
    eth = {
        state.timestamp: state
        for states in eth_states_by_segment
        for state in states
        if state.complete
    }
    common = sorted(set(btc) & set(eth))
    n = len(common)

    def fraction(predicate) -> str:
        if not n:
            return "0"
        count = sum(predicate(btc[ts], eth[ts]) for ts in common)
        return str(Decimal(count) / Decimal(n))

    return {
        "synchronized_complete_state_observations": n,
        "volatility_state_agreement_fraction": fraction(
            lambda a, b: a.volatility_state == b.volatility_state
        ),
        "activity_state_agreement_fraction": fraction(
            lambda a, b: a.activity_state == b.activity_state
        ),
        "trend_state_agreement_fraction": fraction(
            lambda a, b: a.trend_state == b.trend_state
        ),
        "composite_state_agreement_fraction": fraction(
            lambda a, b: a.composite == b.composite
        ),
    }


def main() -> None:
    report = {
        "experiment_version": "gate2-cycle8-market-state-v1",
        "state_definition_version": STATE_DEFINITION_VERSION,
        "github_sha": os.environ.get("GITHUB_SHA", "UNKNOWN"),
        "checked_out_sha": os.environ.get("CHECKED_OUT_SHA", "UNKNOWN"),
        "preregistration": {
            "path": str(PREREG),
            "sha256": sha256_file(ROOT / PREREG),
        },
        "development_window": [START.isoformat(), END.isoformat()],
        "validation_or_oos_accessed": False,
        "strategy_pnl_calculated": False,
        "strategy_signals_generated": False,
        "assets": {},
        "cross_asset_agreement": {},
        "status": "STATE_LAYER_INVALID",
    }

    with tempfile.TemporaryDirectory(prefix="gate2-cycle8-state-") as td:
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
            bars.sort(key=lambda bar: bar.timestamp)
            segments = continuous_segments(bars, manifest.continuity_breaks)
            states_by_segment = [build_market_states(segment) for segment in segments]

            summary = summarize_asset(segments, states_by_segment)
            report["assets"][symbol] = {
                "dataset_identity": manifest.dataset_identity,
                "source_integrity": manifest.source_integrity,
                "certification": manifest.research_certification,
                **summary,
            }
            loaded[symbol] = states_by_segment

        report["cross_asset_agreement"] = synchronized_agreement(
            loaded["BTCUSDT"], loaded["ETHUSDT"]
        )

        both_nonzero = all(
            report["assets"][symbol]["complete_state_observations"] > 0
            for symbol in ("BTCUSDT", "ETHUSDT")
        )
        sync_nonzero = (
            report["cross_asset_agreement"]["synchronized_complete_state_observations"] > 0
        )
        if (
            both_nonzero
            and sync_nonzero
            and report["validation_or_oos_accessed"] is False
            and report["strategy_pnl_calculated"] is False
            and report["strategy_signals_generated"] is False
        ):
            report["status"] = "STATE_LAYER_READY"

    output = Path("gate2_cycle8_market_state_results")
    output.mkdir(exist_ok=True)
    (output / "cycle8_market_state.json").write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"Cycle 8 market-state evidence generated: {report['status']}")


if __name__ == "__main__":
    main()
