from decimal import Decimal

import pytest

from research_core.strategy_specification import StrategySpecification


def make_strategy(**overrides):
    values = dict(
        strategy_id="S-001", version="V0.1", hypothesis_id="H-001", market="spot",
        asset_universe=("BTC",), timeframe="1h", entry_rules="entry",
        exit_rules="exit", stop_rules="stop", target_rules="target",
        position_sizing="fixed", transaction_cost_assumptions=Decimal("0.001"),
        slippage_assumptions=Decimal("0.0005"),
    )
    values.update(overrides)
    return StrategySpecification(**values)


def test_valid_spot_strategy():
    assert make_strategy().market == "spot"


def test_spot_only_constraint_and_required_fields():
    with pytest.raises(ValueError): make_strategy(market="perpetual")
    with pytest.raises(ValueError): make_strategy(asset_universe=())
    with pytest.raises(ValueError): make_strategy(entry_rules=" ")


def test_structured_fields_and_costs_are_validated():
    with pytest.raises(ValueError): make_strategy(transaction_cost_assumptions=Decimal("-0.001"))
    with pytest.raises(ValueError): make_strategy(slippage_assumptions=Decimal("-0.001"))
    with pytest.raises(ValueError): make_strategy(applicable_market_regimes=("",))
