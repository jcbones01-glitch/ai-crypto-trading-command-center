from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class StrategySpecification:
    strategy_id: str
    version: str
    hypothesis_id: str
    market: str
    asset_universe: tuple[str, ...]
    timeframe: str
    entry_rules: str
    exit_rules: str
    stop_rules: str
    target_rules: str
    position_sizing: str
    transaction_cost_assumptions: Decimal
    slippage_assumptions: Decimal
    applicable_market_regimes: tuple[str, ...] = field(default_factory=tuple)
    assumptions: tuple[str, ...] = field(default_factory=tuple)
    invalidation_criteria: tuple[str, ...] = field(default_factory=tuple)
    research_status: str = "research"

    def __post_init__(self) -> None:
        if not self.strategy_id or not self.version or not self.hypothesis_id:
            raise ValueError("strategy_id, version, and hypothesis_id are required")
        if not self.asset_universe:
            raise ValueError("asset_universe cannot be empty")
        if self.transaction_cost_assumptions < 0 or self.slippage_assumptions < 0:
            raise ValueError("cost and slippage assumptions must be non-negative")
