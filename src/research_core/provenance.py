from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from typing import Any, Mapping


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)
    return value


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_plain(item) for item in value]
    if isinstance(value, frozenset):
        return sorted(_plain(item) for item in value)
    return value


@dataclass(frozen=True)
class ResearchResult:
    hypothesis_id: str
    strategy_id: str
    strategy_version: str
    dataset_identity: str
    dataset_start: str
    dataset_end: str
    timeframe: str
    parameters: Mapping[str, Any]
    transaction_cost_assumptions: Decimal
    slippage_assumptions: Decimal
    code_version: str
    metrics: Mapping[str, Any]
    conclusion: str
    research_decision: str

    def __post_init__(self) -> None:
        required = (
            self.hypothesis_id, self.strategy_id, self.strategy_version,
            self.dataset_identity, self.dataset_start, self.dataset_end,
            self.timeframe, self.code_version, self.conclusion,
            self.research_decision,
        )
        if any(not value for value in required):
            raise ValueError("required provenance fields cannot be empty")
        if self.transaction_cost_assumptions < 0 or self.slippage_assumptions < 0:
            raise ValueError("cost and slippage assumptions must be non-negative")
        object.__setattr__(self, "parameters", _freeze(self.parameters))
        object.__setattr__(self, "metrics", _freeze(self.metrics))

    def to_record(self) -> dict[str, Any]:
        record = self.__dict__.copy()
        record["parameters"] = _plain(self.parameters)
        record["metrics"] = _plain(self.metrics)
        record["transaction_cost_assumptions"] = str(self.transaction_cost_assumptions)
        record["slippage_assumptions"] = str(self.slippage_assumptions)
        return record
