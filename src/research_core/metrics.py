from dataclasses import dataclass
from decimal import Decimal


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
    recovery_periods: int | None


def _recovery_periods(equity: list[Decimal]) -> int | None:
    peak = equity[0]
    drawdown_seen = False
    recovery = 0
    for value in equity[1:]:
        if value >= peak:
            if drawdown_seen:
                return recovery
            peak = value
            continue
        drawdown_seen = True
        recovery += 1
    return None if drawdown_seen else 0


def calculate_metrics(
    equity: list[Decimal],
    trade_pnls: list[Decimal],
    positions: list[Decimal] | None = None,
    periods_per_year: int = 365,
) -> PerformanceMetrics:
    """Calculate metrics from an equity curve and genuine realized trade P&Ls.

    ``exposure`` is average absolute portfolio exposure when positions are
    supplied. Recovery is the number of periods from the drawdown trough until
    the prior equity peak is recovered; an unrecovered drawdown returns None.
    """
    if not equity:
        raise ValueError("equity cannot be empty")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    if positions is not None and len(positions) != len(equity):
        raise ValueError("positions and equity must have equal length")
    if positions is not None and any(p < 0 or p > 1 for p in positions):
        raise ValueError("positions must be between 0 and 1")

    initial, final = equity[0], equity[-1]
    if initial <= 0:
        raise ValueError("initial equity must be positive")

    wins = [x for x in trade_pnls if x > 0]
    losses = [x for x in trade_pnls if x < 0]
    count = len(trade_pnls)
    avg_win = sum(wins, Decimal("0")) / Decimal(len(wins)) if wins else Decimal("0")
    avg_loss = sum(losses, Decimal("0")) / Decimal(len(losses)) if losses else Decimal("0")
    win_rate = Decimal(len(wins)) / Decimal(count) if count else Decimal("0")
    loss_rate = Decimal(len(losses)) / Decimal(count) if count else Decimal("0")
    expectancy = win_rate * avg_win + loss_rate * avg_loss if count else Decimal("0")
    gross_loss = -sum(losses, Decimal("0"))
    profit_factor = sum(wins, Decimal("0")) / gross_loss if gross_loss else None

    peak = initial
    max_dd = Decimal("0")
    for value in equity:
        peak = max(peak, value)
        if peak > 0:
            max_dd = max(max_dd, (peak - value) / peak)

    returns = [(equity[i] / equity[i - 1]) - Decimal("1") for i in range(1, len(equity))]
    sharpe = sortino = None
    if returns:
        mean = sum(returns, Decimal("0")) / Decimal(len(returns))
        variance = sum((r - mean) ** 2 for r in returns) / Decimal(len(returns))
        stdev = variance.sqrt()
        if stdev > 0:
            sharpe = mean / stdev * Decimal(periods_per_year).sqrt()
        downside_squares = [r * r for r in returns if r < 0]
        if downside_squares:
            downside_dev = (sum(downside_squares, Decimal("0")) / Decimal(len(returns))).sqrt()
            if downside_dev > 0:
                sortino = mean / downside_dev * Decimal(periods_per_year).sqrt()

    current = max_consecutive_losses = 0
    for pnl in trade_pnls:
        current = current + 1 if pnl < 0 else 0
        max_consecutive_losses = max(max_consecutive_losses, current)

    exposure = (
        sum((abs(p) for p in positions), Decimal("0")) / Decimal(len(positions))
        if positions else Decimal("0")
    )
    return PerformanceMetrics(
        total_return=final / initial - Decimal("1"),
        win_rate=win_rate,
        average_win=avg_win,
        average_loss=avg_loss,
        expectancy=expectancy,
        profit_factor=profit_factor,
        max_drawdown=max_dd,
        sharpe=sharpe,
        sortino=sortino,
        trade_count=count,
        exposure=exposure,
        consecutive_losses=max_consecutive_losses,
        recovery_periods=_recovery_periods(equity),
    )
