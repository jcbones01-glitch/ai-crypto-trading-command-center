from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when project configuration is invalid."""


def load_config(path: str | Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError("Unable to load configuration") from exc
    if not isinstance(data, dict):
        raise ConfigError("Configuration must be a mapping")

    market = data.get("market")
    backtest = data.get("backtest")
    if not isinstance(market, dict) or not isinstance(backtest, dict):
        raise ConfigError("market and backtest must be mappings")
    for key in ("type", "quote_currency"):
        if key not in market:
            raise ConfigError(f"Missing market.{key}")
    for key in ("initial_capital", "commission_rate", "slippage_rate"):
        if key not in backtest:
            raise ConfigError(f"Missing backtest.{key}")

    result = dict(data)
    result["backtest"] = dict(backtest)
    for key in ("initial_capital", "commission_rate", "slippage_rate"):
        try:
            result["backtest"][key] = Decimal(str(backtest[key]))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ConfigError(f"Invalid decimal: backtest.{key}") from exc
        if result["backtest"][key] < 0:
            raise ConfigError(f"backtest.{key} must be non-negative")

    if result["backtest"]["initial_capital"] <= 0:
        raise ConfigError("backtest.initial_capital must be positive")
    if str(market["type"]).lower() != "spot":
        raise ConfigError("V0 supports spot research only")
    return result
