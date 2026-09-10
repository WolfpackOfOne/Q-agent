# FundamentalsPortfolio

Quarterly-rebalanced, dollar-neutral long/short equity strategy on the
point-in-time largest 1,000 US companies. Each stock is scored by a
gradient-boosted trees model on cross-sectionally ranked quarterly
financial-statement features (Compustat via WRDS, linked to CRSP); every
calendar quarter, long the top decile by score and short the bottom
decile, equal-weighted within each side, 100% total gross exposure (50%
long / 50% short).

The research — data pipeline, cleaning, feature admission, model fit, and
export of point-in-time scores — is in
[`infrastructure/marimo/notebooks/fundamentals_portfolio.py`](../../infrastructure/marimo/notebooks/fundamentals_portfolio.py);
this project executes the exported scores in LEAN.

**Result (held-out 2022–2023 test window)**: test IC 0.078 (t = 4.0),
positive in all 7 quarters; notebook Sharpe 1.53 at 3.0% vol, +8.2% over
the window, max drawdown −0.7%. LEAN reproduces it: +8.7% net (4.3%/yr at
3.6% vol, max drawdown −3.5%), Sharpe 0.55 after LEAN's risk-free
adjustment (≈ 1.2 raw). See [docs/strategy.md](docs/strategy.md).

## Quick Start

```bash
# Data (once; ~15 min, needs WRDS credentials)
cd infrastructure/pipelines/wrds && export WRDS_USERNAME=<user> && caffeinate -dims ./venv/bin/python scripts/run_broad_quarterly_pipeline.py

# Activate environment (from the Q-agent workspace root)
source venv/bin/activate
cd MyProjects

# Local backtest — use the shared-signal wrapper, not plain `lean backtest`
bash ../scripts/lean-backtest.sh "FundamentalsPortfolio"
```

## Documentation

- **Project Overview**: [claude.md](claude.md)
- **Architecture**: [docs/architecture.md](docs/architecture.md)
- **Strategy Logic & Results**: [docs/strategy.md](docs/strategy.md)
- **ObjectStore Schema**: [docs/objectstore.md](docs/objectstore.md)
- **Agent Instructions**: [AGENTS.md](AGENTS.md)

## Project Structure

```
FundamentalsPortfolio/
├── main.py          # Algorithm entry point — universe from the score file, quarterly rebalance
├── models/          # Alpha (point-in-time score read), portfolio (decile L/S), execution, logging
├── domain/          # Config, DTOs, signals/cross_sectional_rank.py (shared, symlinked)
├── data/            # fundamental_scores.csv — notebook export, test window only (committed)
├── docs/            # Documentation
└── research/        # Marimo research notebooks
```

## Strategy Overview

| Aspect | Description |
|--------|--------------|
| Type | Cross-sectional equity long/short (fundamental factor) |
| Asset Class | US Equity |
| Universe | Point-in-time top 1,000 by market cap (1,081 tickers scored in the test window) |
| Features | 8 financial-statement ratios selected by statistical significance, cross-sectionally ranked |
| Model | Gradient-boosted decision trees |
| Long/Short split | Top decile / bottom decile by score, equal-weighted |
| Gross exposure | 100% (50% long / 50% short) |
| Rebalance | Quarterly (first trading day of Jan/Apr/Jul/Oct) |
| Backtest window | 2022-01-01 to 2023-12-31 (held-out test period) |
| Benchmark | SPY |

## ObjectStore Outputs

| File | Description |
|------|--------------|
| `fundamentals_portfolio/daily_snapshots.csv` | Per-rebalance portfolio metrics |
| `fundamentals_portfolio/positions.csv` | Position data |
| `fundamentals_portfolio/trades.csv` | Trade history |

## Contributing

See [AGENTS.md](AGENTS.md) for guidelines on making changes to this project.
