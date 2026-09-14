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
        required_text = (
            self.strategy_id, self.version, self.hypothesis_id, self.market,
            self.timeframe, self.entry_rules, self.exit_rules, self.stop_rules,
            self.target_rules, self.position_sizing, self.research_status,
        )
        if any(not value.strip() for value in required_text):
            raise ValueError("required strategy fields cannot be empty")
        if self.market.lower() != "spot":
            raise ValueError("V0 supports spot strategies only")
        if not self.asset_universe or any(not asset.strip() for asset in self.asset_universe):
            raise ValueError("asset_universe must contain non-empty assets")
        if self.transaction_cost_assumptions < 0 or self.slippage_assumptions < 0:
            raise ValueError("cost and slippage assumptions must be non-negative")
        structured = (*self.applicable_market_regimes, *self.assumptions, *self.invalidation_criteria)
        if any(not value.strip() for value in structured):
            raise ValueError("structured strategy fields cannot contain empty values")
