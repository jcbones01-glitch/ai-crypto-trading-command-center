from dataclasses import dataclass
from decimal import Decimal

from .data_interfaces import MarketBar


@dataclass(frozen=True)
class BacktestConfig:
    initial_capital: Decimal
    commission_rate: Decimal
    slippage_rate: Decimal

    def __post_init__(self) -> None:
        if self.initial_capital <= 0:
            raise ValueError("initial_capital must be positive")
        if self.commission_rate < 0 or self.slippage_rate < 0:
            raise ValueError("commission_rate and slippage_rate must be non-negative")


@dataclass(frozen=True)
class BacktestResult:
    equity: list[Decimal]
    trade_pnls: list[Decimal]


def run_backtest(bars: list[MarketBar], target_positions: list[Decimal], config: BacktestConfig) -> BacktestResult:
    """Run a deterministic close-to-close spot simulation.

    target_positions are fractions of equity invested in the asset, from 0 to 1.
    A position change is executed at the current close with explicit proportional
    commission and slippage. No look-ahead is used: position[i] is applied to
    the return from bar i to bar i+1.
    """
    if len(bars) != len(target_positions):
        raise ValueError("bars and target_positions must have equal length")
    if not bars:
        return BacktestResult([], [])
    if any(p < 0 or p > 1 for p in target_positions):
        raise ValueError("spot target positions must be between 0 and 1")

    equity = config.initial_capital
    previous_position = Decimal("0")
    equity_curve = [equity]
    trade_pnls: list[Decimal] = []

    for i in range(len(bars) - 1):
        position = target_positions[i]
        if position != previous_position:
            turnover = abs(position - previous_position)
            cost_rate = config.commission_rate + config.slippage_rate
            equity -= equity * turnover * cost_rate
            trade_pnls.append(equity * (position - previous_position))
        price_return = (bars[i + 1].close / bars[i].close) - Decimal("1")
        equity += equity * position * price_return
        equity_curve.append(equity)
        previous_position = position

    return BacktestResult(equity_curve, trade_pnls)
