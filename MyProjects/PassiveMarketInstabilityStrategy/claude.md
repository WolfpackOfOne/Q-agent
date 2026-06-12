# Claude Code — PassiveMarketInstabilityStrategy

## Context

Research scaffold for the passive market instability risk-overlay strategy.
Signal logic lives in `domain/signals/passive_pressure.py` (pure Python, no LEAN).

## Key constraints

- Research and backtest only — no live trading additions.
- Signal thresholds and sizing in `domain/config.py` require explicit review before change.
- ETF volume × return is a proxy; document any replacement data source clearly.

## Run a local validation backtest

```bash
lean cloud push --project "PassiveMarketInstabilityStrategy"
lean cloud backtest "PassiveMarketInstabilityStrategy" --name "validation"
```
