# Architecture

## V0 pipeline

`Configuration -> Data Contract -> Strategy Specification -> Backtest Engine -> Metrics -> Research Provenance`

V0 is intentionally a research-only system. External connections and credential handling are outside scope.

## Design rule

Keep analysis, quantitative calculation, validation, and later operational components separated so each can be tested independently.
