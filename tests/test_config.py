from decimal import Decimal

from research_core.config.loader import load_config


def test_config_loads_decimal_values() -> None:
    config = load_config("config/default.yaml")
    assert config["market"]["type"] == "spot"
    assert config["backtest"]["commission_rate"] == Decimal("0.0010")
    assert config["backtest"]["slippage_rate"] == Decimal("0.0005")
