from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class ResearchResult:
    hypothesis_id: str
    strategy_id: str
    strategy_version: str
    dataset_identity: str
    dataset_start: str
    dataset_end: str
    timeframe: str
    parameters: dict[str, Any]
    transaction_cost_assumptions: Decimal
    slippage_assumptions: Decimal
    code_version: str
    metrics: dict[str, Any]
    conclusion: str
    research_decision: str

    def __post_init__(self) -> None:
        required = (self.hypothesis_id, self.strategy_id, self.strategy_version,
                    self.dataset_identity, self.dataset_start, self.dataset_end,
                    self.timeframe, self.code_version, self.conclusion,
                    self.research_decision)
        if any(not value for value in required):
            raise ValueError("required provenance fields cannot be empty")
        if self.transaction_cost_assumptions < 0 or self.slippage_assumptions < 0:
            raise ValueError("cost and slippage assumptions must be non-negative")

    def to_record(self) -> dict[str, Any]:
        record = self.__dict__.copy()
        record["transaction_cost_assumptions"] = str(self.transaction_cost_assumptions)
        record["slippage_assumptions"] = str(self.slippage_assumptions)
        return record
