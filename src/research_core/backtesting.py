from dataclasses import dataclass
from decimal import Decimal

from .data_interfaces import MarketBar, validate_market_data


@dataclass(frozen=True)
class BacktestConfig:
    initial_capital: Decimal
    commission_rate: Decimal
    slippage_rate: Decimal
    execution_delay_bars: int = 1

    def __post_init__(self) -> None:
        if self.initial_capital <= 0:
            raise ValueError("initial_capital must be positive")
        if self.commission_rate < 0 or self.slippage_rate < 0:
            raise ValueError("commission_rate and slippage_rate must be non-negative")
        if self.execution_delay_bars not in (1, 2):
            raise ValueError("execution_delay_bars must be 1 or 2; same-bar execution is prohibited")


@dataclass(frozen=True)
class BacktestResult:
    equity: list[Decimal]
    positions: list[Decimal]
    trade_pnls: list[Decimal]
    transaction_costs: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal


def _execution_price(price: Decimal, slippage: Decimal, buying: bool) -> Decimal:
    return price * (Decimal("1") + slippage) if buying else price * (Decimal("1") - slippage)


def run_backtest(
    bars: list[MarketBar], target_positions: list[Decimal], config: BacktestConfig
) -> BacktestResult:
    """Run a deterministic causal spot simulation.

    A target generated from bar ``t`` is executed at the OPEN of bar
    ``t + execution_delay_bars``. Same-bar execution is prohibited. Buys pay
    upward slippage; sells receive downward slippage. Commission is
    proportional to gross fill value. Closed quantities are matched FIFO.
    """
    if len(bars) != len(target_positions):
        raise ValueError("bars and target_positions must have equal length")
    if not bars:
        return BacktestResult([], [], [], Decimal("0"), Decimal("0"), Decimal("0"))
    validate_market_data(bars)
    if any(p < 0 or p > 1 for p in target_positions):
        raise ValueError("spot target positions must be between 0 and 1")

    cash = config.initial_capital
    units = Decimal("0")
    lots: list[dict[str, Decimal]] = []
    equity_curve: list[Decimal] = []
    position_curve: list[Decimal] = []
    trade_pnls: list[Decimal] = []
    total_costs = Decimal("0")

    for i, bar in enumerate(bars):
        if i >= config.execution_delay_bars:
            units = sum((lot["units"] for lot in lots), Decimal("0"))
            target = target_positions[i - config.execution_delay_bars]
            current_equity_at_open = cash + units * bar.open
            current_notional = units * bar.open
            target_notional = current_equity_at_open * target
            delta_notional = target_notional - current_notional

            if delta_notional > 0:
                fill = _execution_price(bar.open, config.slippage_rate, buying=True)
                gross = delta_notional / (Decimal("1") + config.commission_rate)
                fee = delta_notional - gross
                qty = gross / fill
                cash -= delta_notional
                lots.append({"units": qty, "entry_cost": gross + fee})
                units = sum((lot["units"] for lot in lots), Decimal("0"))
                total_costs += fee
            elif delta_notional < 0 and units > 0:
                sell_fill = _execution_price(bar.open, config.slippage_rate, buying=False)

                if target == 0:
                    qty_to_sell = units
                    gross = qty_to_sell * sell_fill
                    fee = gross * config.commission_rate
                    cash += gross - fee
                    total_costs += fee

                    for lot in lots:
                        closed = lot["units"]
                        allocated_entry_cost = lot["entry_cost"]
                        allocated_exit_proceeds = closed * sell_fill - fee * (closed / qty_to_sell)
                        trade_pnls.append(allocated_exit_proceeds - allocated_entry_cost)

                    lots.clear()
                    units = Decimal("0")
                else:
                    qty_to_sell = min(units, -delta_notional / sell_fill)
                    gross = qty_to_sell * sell_fill
                    fee = gross * config.commission_rate
                    cash += gross - fee
                    total_costs += fee

                    remaining = qty_to_sell
                    while remaining > 0:
                        lot = lots[0]
                        closed = min(remaining, lot["units"])
                        allocated_entry_cost = lot["entry_cost"] * (closed / lot["units"])
                        allocated_exit_proceeds = closed * sell_fill - fee * (closed / qty_to_sell)
                        trade_pnls.append(allocated_exit_proceeds - allocated_entry_cost)
                        lot["units"] -= closed
                        lot["entry_cost"] -= allocated_entry_cost
                        remaining -= closed
                        if lot["units"] == 0:
                            lots.pop(0)

                    units = sum((lot["units"] for lot in lots), Decimal("0"))

        equity = cash + units * bar.close
        position_curve.append(units * bar.close / equity if equity > 0 else Decimal("0"))
        equity_curve.append(equity)

    final_close = bars[-1].close
    unrealized_pnl = sum(
        (lot["units"] * final_close - lot["entry_cost"] for lot in lots),
        Decimal("0"),
    )
    realized_pnl = sum(trade_pnls, Decimal("0"))
    return BacktestResult(
        equity_curve,
        position_curve,
        trade_pnls,
        total_costs,
        realized_pnl,
        unrealized_pnl,
    )
