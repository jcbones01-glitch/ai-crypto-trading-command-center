from decimal import Decimal

import pytest

from research_core.strategy_specification import StrategySpecification


def test_strategy_specification_requires_core_identity() -> None:
    spec = StrategySpecification(
        "S-001", "V0.1", "H-001", "spot", ("BTC",), "1h",
        "entry", "exit", "stop", "target", "fixed", Decimal("0.001"), Decimal("0.0005")
    )
    assert spec.strategy_id == "S-001"


def test_empty_asset_universe_rejected() -> None:
    with pytest.raises(ValueError):
        StrategySpecification(
            "S-001", "V0.1", "H-001", "spot", (), "1h",
            "entry", "exit", "stop", "target", "fixed", Decimal("0.001"), Decimal("0.0005")
        )
