# PassiveMarketInstabilityStrategy

Research-only QuantConnect strategy extending the passive market instability
research notebook (`infrastructure/marimo/notebooks/passive_market_instability_extension.py`).

## What it does

Equal-weight broad US equity ETFs (SPY, QQQ, IWM, MDY, VTI) with a
**passive-pressure risk overlay**. The overlay reduces gross exposure when the
ETF flow-pressure proxy signals elevated passive-share fragility.

The signal derives from Green, Krishnan, and Sturm's SDE model:

```
dS(t) = κ(1 − p(t))(F(t) − S(t)) dt + σ√(F(t)S(t)) dW
```

When passive share p(t) is high, mean reversion weakens. This strategy uses
ETF volume × return as a flow-pressure proxy and reduces exposure when that
proxy is elevated — treating it as a risk signal, not an alpha signal.

## Guardrails

- Research and backtest only. No live trading logic.
- ETF volume × return is a proxy, not an official flow series.
- Passive share is a logistic estimate (Haddad et al. calibration), not official data.
- The overlay is a research scaffold — threshold and scale parameters require
  explicit review before treating as strategy logic.

## Running a backtest

```bash
lean cloud push --project "PassiveMarketInstabilityStrategy"
lean cloud backtest "PassiveMarketInstabilityStrategy"
```

## Related

- Research notebook: `infrastructure/marimo/notebooks/passive_market_instability_extension.py`
- Source library: `MyProjects/PassiveMarketInstability/src/`
- Research doc: `docs/research-recipes/passive-market-instability-extension.md`
