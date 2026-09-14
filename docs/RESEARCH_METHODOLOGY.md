# Research Methodology

## Evidence hierarchy

Keep these categories separate:

- FACT — externally verifiable information.
- OBSERVATION — a measured pattern in data.
- HYPOTHESIS — a falsifiable proposed explanation or edge.
- MODEL — formal rules used to test a hypothesis.
- BACKTEST RESULT — output from a defined historical simulation.
- LIVE RESULT — observed trading result from paper/live execution.
- OPINION — judgment that is not itself evidence.

## Research loop

`Observation → Hypothesis → Research → Strategy Specification → Backtest → Validation → Robustness → Paper Trading → Deployment`

## Required controls

Research must explicitly consider look-ahead bias, data leakage, survivorship bias, overfitting, curve fitting, unrealistic fills, transaction costs, slippage, sample size, and multiple testing.

V0 does not claim to solve every validation problem; it establishes explicit inputs and boundaries so those controls can be added without changing the research record format.

## Cost discipline

Transaction costs and slippage are explicit inputs. A profitability evaluation must not silently assume zero costs or zero slippage.

## Reproducibility

Every experiment should record its hypothesis, strategy/version, dataset identity and date range, timeframe, parameters, cost/slippage assumptions, code/version identifier, metrics, conclusion, and research decision.
