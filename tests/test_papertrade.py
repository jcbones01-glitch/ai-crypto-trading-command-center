import pytest

from papertrade.backtest import run_backtest
from papertrade.broker import PaperBroker, PaperOnlyError
from papertrade.config import PAPER_TRADING_BASE_URL, UNIVERSE
from papertrade.rebalance import PlannedOrder, build_plan, plan_orders, run
from papertrade.strategy import is_uptrend, target_weights


def test_uptrend_rule():
    assert is_uptrend([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    assert not is_uptrend([10, 9, 8, 7, 6, 5, 4, 3, 2, 1])


def test_uptrend_needs_enough_history():
    with pytest.raises(ValueError):
        is_uptrend([1, 2, 3])


def test_target_weights_equal_share_or_cash():
    up = list(range(1, 11))
    down = list(range(10, 0, -1))
    weights = target_weights({"A": up, "B": down}, ["A", "B"])
    assert weights == {"A": 0.5, "B": 0.0}


def test_plan_sells_before_buys_and_skips_tiny_trades():
    orders = plan_orders(
        {"A": 0.5, "B": 0.0},
        equity=10_000,
        current_values={"A": 4_990, "B": 3_000},
    )
    assert orders == [PlannedOrder("B", "sell", 3000.0)]


def test_broker_refuses_live_endpoint():
    with pytest.raises(PaperOnlyError):
        PaperBroker("k", "s", base_url="https://api.alpaca.markets")


def test_broker_requires_keys():
    with pytest.raises(PaperOnlyError):
        PaperBroker("", "")


class FakeBroker:
    def __init__(self, pending=()):
        self.base_url = PAPER_TRADING_BASE_URL
        self.pending = list(pending)
        self.submitted = []

    def monthly_closes(self, symbols, months):
        return {s: list(range(1, 13)) for s in symbols}

    def account(self):
        return {"equity": "100000"}

    def position_values(self):
        return {}

    def open_orders(self):
        return self.pending

    def submit_notional_order(self, symbol, side, notional):
        self.submitted.append((symbol, side, notional))


def test_build_plan_all_uptrend_buys_equal_weights():
    plan = build_plan(FakeBroker())
    assert plan["paper_only"] is True
    assert plan["pending_orders"] == []
    assert len(plan["orders"]) == len(UNIVERSE)
    assert all(o["side"] == "buy" and o["notional"] == 20000.0 for o in plan["orders"])


def test_submit_blocked_while_orders_pending():
    broker = FakeBroker(pending=[{"symbol": "SPY", "side": "buy", "notional": "20000", "status": "accepted"}])
    plan = run(broker, submit=True)
    assert plan["submitted"] is False
    assert "blocked" in plan
    assert broker.submitted == []
    clean = FakeBroker()
    assert run(clean, submit=True)["submitted"] is True
    assert len(clean.submitted) == len(UNIVERSE)


def test_backtest_moves_to_cash_in_downtrend():
    rising = [100 + i for i in range(24)]
    falling = [200 - 5 * i for i in range(24)]
    result = run_backtest({"A": falling, "BM": falling}, ["A"], "BM")
    assert result["strategy_total_return"] > result["benchmark_total_return"]
    result_up = run_backtest({"A": rising, "BM": rising}, ["A"], "BM")
    assert result_up["strategy_total_return"] > 0
