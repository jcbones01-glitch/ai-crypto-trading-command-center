# Gate 2 — Causal Execution Contract

## Status

This document is the authoritative execution-timing contract for Gate 2 historical research.

## Timing rule

A signal is formed using information available through the close of bar `t`.

That signal is not executable at the same close. Its target position is applied at the OPEN of bar `t+1`.

The implementation therefore enforces exactly one bar of execution delay for bar-close signals.

## Prohibited behavior

The research engine must not execute a signal at the same bar close that produced the signal. A zero-bar execution delay is rejected by configuration.

## Price and cost treatment

Execution uses the next bar's open price. Directional slippage is applied to the execution price, and commission is charged on gross fill value.

No intrabar fill is assumed. No future high, low, close, or volume may influence an execution decision that was already made.

## Research implications

All Gate 2 hypothesis specifications that refer to a signal at bar close must be interpreted under this contract: signal at close of `t`, execution at open of `t+1`.

This contract supersedes any earlier shorthand that described close-based execution without explicitly stating the one-bar causal delay.

## Verification

The Gate 2 foundation workflow includes an automated causal-execution contract check, and the regression suite includes a test that distinguishes same-bar execution from next-bar-open execution.

## Scope

This contract applies to historical research only. It does not authorize paper trading, live trading, exchange connectivity, leverage, or autonomous capital deployment.
