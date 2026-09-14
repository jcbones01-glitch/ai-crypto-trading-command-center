from dataclasses import dataclass
from decimal import Decimal
from math import sqrt


@dataclass(frozen=True)
class PerformanceMetrics:
    total_return: Decimal
    win_rate: Decimal
    average_win: Decimal
    average_loss: Decimal
    expectancy: Decimal
    profit_factor: Decimal | None
    max_drawdown: Decimal
    sharpe: Decimal | None
    sortino: Decimal | None
    trade_count: int
    exposure: Decimal
    consecutive_losses: int
    recovery_periods: int


def calculate_metrics(equity: list[Decimal], trade_pnls: list[Decimal], exposure: Decimal = Decimal("0"), periods_per_year: int = 365) -> PerformanceMetrics:
    if not equity:
        raise ValueError("equity cannot be empty")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")

    initial = equity[0]
    final = equity[-1]
    if initial <= 0:
        raise ValueError("initial equity must be positive")

    wins = [x for x in trade_pnls if x > 0]
    losses = [x for x in trade_pnls if x < 0]
    avg_win = sum(wins, Decimal("0")) / Decimal(len(wins)) if wins else Decimal("0")
    avg_loss = sum(losses, Decimal("0")) / Decimal(len(losses)) if losses else Decimal("0")
    win_rate = Decimal(len(wins)) / Decimal(len(trade_pnls)) if trade_pnls else Decimal("0")
    expectancy = win_rate * avg_win + (Decimal("1") - win_rate) * avg_loss if trade_pnls else Decimal("0")
    gross_loss = -sum(losses, Decimal("0"))
    profit_factor = (sum(wins, Decimal("0")) / gross_loss) if gross_loss else None

    peak = initial
    max_dd = Decimal("0")
    for value in equity:
        peak = max(peak, value)
        if peak > 0:
            max_dd = max(max_dd, (peak - value) / peak)

    returns = [(equity[i] / equity[i - 1]) - Decimal("1") for i in range(1, len(equity)) if equity[i - 1] > 0]
    sharpe = sortino = None
    if returns:
        mean = sum(returns, Decimal("0")) / Decimal(len(returns))
        variance = sum((r - mean) ** 2 for r in returns) / Decimal(len(returns))
        stdev = Decimal(str(sqrt(float(variance))))
        if stdev > 0:
            sharpe = (mean / stdev) * Decimal(str(sqrt(periods_per_year)))
        downside = [min(r, Decimal("0")) for r in returns]
        downside_var = sum(r ** 2 for r in downside) / Decimal(len(downside))
        downside_dev = Decimal(str(sqrt(float(downside_var))))
        if downside_dev > 0:
            sortino = (mean / downside_dev) * Decimal(str(sqrt(periods_per_year)))

    max_consecutive_losses = current = 0
    for pnl in trade_pnls:
        current = current + 1 if pnl < 0 else 0
        max_consecutive_losses = max(max_consecutive_losses, current)

    return PerformanceMetrics(
        total_return=(final / initial) - Decimal("1"),
        win_rate=win_rate,
        average_win=avg_win,
        average_loss=avg_loss,
        expectancy=expectancy,
        profit_factor=profit_factor,
        max_drawdown=max_dd,
        sharpe=sharpe,
        sortino=sortino,
        trade_count=len(trade_pnls),
        exposure=exposure,
        consecutive_losses=max_consecutive_losses,
        recovery_periods=0,
    )
