"""Turn target weights into paper orders, and the monthly command-line entry point.

Default is a DRY RUN: it prints the plan and places nothing.  `--submit`
places orders on the Alpaca PAPER account only.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Mapping, Sequence

from .config import BENCHMARK, LOOKBACK_MONTHS, MIN_TRADE_DOLLARS, UNIVERSE
from .strategy import target_weights


@dataclass(frozen=True)
class PlannedOrder:
    symbol: str
    side: str  # "buy" or "sell"
    notional: float


def plan_orders(
    weights: Mapping[str, float],
    equity: float,
    current_values: Mapping[str, float],
    min_trade: float = MIN_TRADE_DOLLARS,
) -> list[PlannedOrder]:
    """Sells first (to free cash), then buys.  Ignores tiny adjustments."""
    if equity <= 0:
        raise ValueError("account equity must be positive")
    sells: list[PlannedOrder] = []
    buys: list[PlannedOrder] = []
    for symbol in sorted(set(weights) | set(current_values)):
        target = equity * float(weights.get(symbol, 0.0))
        diff = target - float(current_values.get(symbol, 0.0))
        if abs(diff) < min_trade:
            continue
        order = PlannedOrder(symbol, "buy" if diff > 0 else "sell", round(abs(diff), 2))
        (buys if diff > 0 else sells).append(order)
    return sells + buys


def build_plan(broker, universe: Sequence[str] = UNIVERSE) -> dict:
    closes = broker.monthly_closes(list(universe) + [BENCHMARK], months=LOOKBACK_MONTHS + 2)
    weights = target_weights(closes, universe)
    account = broker.account()
    values = broker.position_values()
    orders = plan_orders(weights, float(account["equity"]), values)
    pending = [
        {"symbol": o.get("symbol"), "side": o.get("side"), "notional": o.get("notional"), "status": o.get("status")}
        for o in broker.open_orders()
    ]
    return {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "paper_only": True,
        "equity": float(account["equity"]),
        "weights": weights,
        "current_values": values,
        "pending_orders": pending,
        "orders": [asdict(o) for o in orders],
    }


def run(broker, submit: bool) -> dict:
    """Build the plan and, if asked, submit it.

    Refuses to submit while earlier orders are still open: until they fill,
    positions look empty and the same buys would be placed twice.
    """
    plan = build_plan(broker)
    plan["submitted"] = False
    if submit and plan["pending_orders"]:
        plan["blocked"] = "earlier orders are still pending; nothing placed. Try again after they fill."
    elif submit:
        for order in plan["orders"]:
            broker.submit_notional_order(order["symbol"], order["side"], order["notional"])
        plan["submitted"] = True
    return plan


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Monthly paper-trading rebalance (fake money only).")
    parser.add_argument("--submit", action="store_true", help="place PAPER orders (default: dry run)")
    args = parser.parse_args(argv)

    from .broker import PaperBroker  # imported here so tests need no network

    plan = run(PaperBroker.from_env(), args.submit)
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 2 if "blocked" in plan else 0  # a red run makes "nothing placed" obvious


if __name__ == "__main__":
    raise SystemExit(main())
