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

The original V0 scope has since been extended with historical Development strategy experiments. No candidate is currently promoted and no live execution capability is authorized.
## Active research continuation

The completed HYP-0001–HYP-0025 OHLCV Development family remains closed with no promoted candidate. The research-foundation branch adds the certified AMS-V1 market-state vocabulary. The proposed next phase investigates return dependence without creating a strategy or accessing Validation/OOS.

Start with [repository reconciliation](docs/ADAPTIVE_MARKETS_RECONCILIATION_2026_09_19.md), [market-state protocol](docs/MARKET_STATE_RESEARCH_PROTOCOL.md), and the [execution-blocked preregistration draft](docs/MARKET_STATE_DEPENDENCE_PREREGISTRATION_V1.md). The draft needs independent statistical review and a complete freeze before any empirical run. Green software tests do not constitute research approval.
