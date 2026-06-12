# Agent Instructions — PassiveMarketInstabilityStrategy

## What this project is

A QuantConnect LEAN research strategy using passive-pressure diagnostics from the
passive market instability research notebook as a risk overlay signal.

## What agents should and should not do

**Do:**
- Treat every change to strategy logic (signals, thresholds, sizing, universe) as requiring explicit user review.
- Keep `main.py` thin. Put signal logic in `domain/signals/`, domain objects in `domain/models.py`.
- Preserve the data-quality language: ETF volume × return is a **proxy**, logistic passive share is an **estimate**.
- Reference the research notebook and `MyProjects/PassiveMarketInstability/src/` when updating signal logic.

**Do not:**
- Add live trading logic, brokerage credentials, or live execution assumptions.
- Silently change thresholds or sizing parameters — document the reasoning.
- Remove the research/backtest-only guardrails.

## Architecture

```
main.py                        ← composition root
domain/config.py               ← all strategy parameters
domain/models.py               ← DTOs
domain/signals/passive_pressure.py  ← pure Python signal logic (no LEAN)
models/alpha.py                ← passive-pressure diagnostic computation
models/portfolio.py            ← equal-weight + overlay
models/execution.py            ← SetHoldings wrapper
models/logger.py               ← Log output
```

## Related files

- `infrastructure/marimo/notebooks/passive_market_instability_extension.py`
- `MyProjects/PassiveMarketInstability/src/passive_market_instability/simulation.py`
- `docs/research-recipes/passive-market-instability-extension.md`
