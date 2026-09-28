"""Monthly report: the paper account versus simply holding SPY.

Both are measured from the close of TRACKING_START, on the days both have a
value.  Read-only: it places nothing.  In GitHub Actions the report is also
written to the run's summary page.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Sequence

from .config import BENCHMARK, TRACKING_START


def _max_drawdown(values: Sequence[float]) -> float:
    peak, worst = values[0], 0.0
    for v in values:
        peak = max(peak, v)
        worst = min(worst, v / peak - 1)
    return worst


def compare(
    account: Sequence[tuple[str, float]],
    benchmark: Sequence[tuple[str, float]],
    start: str = TRACKING_START,
) -> dict:
    acct = {d: v for d, v in account if d >= start and v > 0}
    bench = {d: v for d, v in benchmark if d >= start and v > 0}
    days = sorted(set(acct) & set(bench))
    if len(days) < 2:
        return {"start": start, "trading_days": len(days), "status": "not enough data yet"}
    a = [acct[d] for d in days]
    b = [bench[d] for d in days]
    acct_ret = a[-1] / a[0] - 1
    bench_ret = b[-1] / b[0] - 1
    return {
        "start": days[0],
        "end": days[-1],
        "trading_days": len(days),
        "status": "ok",
        "account_start": a[0],
        "account_end": a[-1],
        "account_return": acct_ret,
        "benchmark_return": bench_ret,
        "difference": acct_ret - bench_ret,
        "account_max_drawdown": _max_drawdown(a),
        "benchmark_max_drawdown": _max_drawdown(b),
    }


def render_markdown(result: dict, benchmark: str = BENCHMARK) -> str:
    lines = ["## Paper account vs. just holding " + benchmark, ""]
    if result["status"] != "ok":
        lines.append(f"Not enough data yet ({result['trading_days']} trading day(s) since {result['start']}).")
        return "\n".join(lines) + "\n"
    pct = lambda x: f"{x * 100:+.2f}%"  # noqa: E731
    lines += [
        f"From **{result['start']}** to **{result['end']}** ({result['trading_days']} trading days).",
        "",
        f"| | Paper account (trend rule) | Just holding {benchmark} |",
        "|---|---|---|",
        f"| Return | {pct(result['account_return'])} | {pct(result['benchmark_return'])} |",
        f"| Worst drop from a high | {pct(result['account_max_drawdown'])} | {pct(result['benchmark_max_drawdown'])} |",
        "",
        f"Account value: ${result['account_start']:,.2f} → ${result['account_end']:,.2f}. "
        f"Difference vs. {benchmark}: **{pct(result['difference'])}**.",
        "",
        "_How to read this: a few months of results mostly reflect luck. The trend rule is "
        "expected to lag in strong rising markets and to help mainly in big crashes. Judge it "
        "over years, not months. Paper fills are idealized._",
    ]
    return "\n".join(lines) + "\n"


def build_report(broker) -> dict:
    result = compare(broker.daily_equity(), broker.daily_closes(BENCHMARK, TRACKING_START))
    result["time_utc"] = datetime.now(timezone.utc).isoformat()
    result["paper_only"] = True
    return result


def main() -> int:
    from .broker import PaperBroker  # imported here so tests need no network

    result = build_report(PaperBroker.from_env())
    print(json.dumps(result, indent=2, sort_keys=True))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(render_markdown(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
