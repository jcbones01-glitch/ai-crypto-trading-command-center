# AI Crypto Trading Command Center

V0 is an evidence-driven research foundation for an eventual crypto trading system.

## Mission

Build from:

**EDGE → DATA → RULES → TEST → VALIDATE → PAPER TRADE → EXECUTE**

V0 deliberately stops before live trading. It provides standardized research methodology, strategy specifications, data contracts, deterministic backtesting, financial metrics, configuration, tests, and reproducible research provenance.

## Current scope

- Python package with minimal research components
- Explicit spot-market assumptions
- Explicit transaction costs and slippage
- Decimal-based monetary calculations where appropriate
- Deterministic configuration and backtesting primitives
- Reproducible experiment/provenance records
- Unit tests

## Explicitly excluded from V0

- Live trading or order submission
- Exchange authentication or API credentials
- Real-money execution
- Paper-trading connectivity
- Machine learning models
- AI agents
- Automated strategy self-modification
- Risk/execution infrastructure beyond research inputs and validation
- Databases, queues, web dashboards, or cloud infrastructure

## Development path

V0 — Research prototype  
V1 — Historical backtesting  
V2 — Robustness / out-of-sample validation  
V3 — Paper trading  
V4 — Live monitoring without execution  
V5 — Tiny controlled live trading  
V6 — Controlled scaling

There is no requirement to reach live trading.

## Research discipline

The project distinguishes **FACT, OBSERVATION, HYPOTHESIS, MODEL, BACKTEST RESULT, LIVE RESULT, and OPINION**. No strategy is considered profitable merely because a backtest produces a positive result.

See `docs/RESEARCH_METHODOLOGY.md` and `docs/STRATEGY_SPECIFICATION.md` for the governing conventions.

## Development

Requires Python 3.11+.

```bash
python -m pip install -e '.[dev]'
pytest
```

The repository currently contains no trading strategy and no live execution capability.