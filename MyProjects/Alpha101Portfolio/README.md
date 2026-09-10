# Alpha101Portfolio

Daily-rebalanced, dollar-neutral long/short equity strategy on the point-in-time
largest 300 US companies. The research notebook implements all 101 formulaic
alpha expressions from Zura Kakushadze, *101
Formulaic Alphas* (arXiv:1601.00991) — arithmetic formulas over daily open, high,
low, close and volume. Every session, long the top quintile by score and short the
bottom quintile, equal-weighted within each side, 100% total gross exposure.

The research — all 101 alpha implementations, an automated formula-verification
diagnostic, signal-decay analysis, selection, and one held-out test evaluation —
is in
[`infrastructure/marimo/notebooks/alpha101_portfolio.py`](../../infrastructure/marimo/notebooks/alpha101_portfolio.py).
The paper is at [`References/papers/101-formulaic-alphas/`](../../References/papers/101-formulaic-alphas/).

**Result**: across a 60/20/20 split of 2005–2024, the full 101-alpha model (90
pass a training-significance filter; 2 are flagged and excluded as degenerate
by an automated coverage check) has a held-out 2021–2024 daily information
coefficient of **0.0128 (t = 3.86)**, positive in every one of the four test
years, and a gross Sharpe of **1.50**. See [docs/strategy.md](docs/strategy.md)
for the full methodology and results.

## Quick Start

```bash
# Data (once; needs WRDS credentials)
cd infrastructure/pipelines/wrds && export WRDS_USERNAME=<user> && ./venv/bin/python scripts/run_broad_quarterly_pipeline.py

# Backtest (from the Q-agent workspace root)
source venv/bin/activate
cd MyProjects
bash ../scripts/lean-backtest.sh "Alpha101Portfolio"
```

## Documentation

- **Project Overview**: [claude.md](claude.md)
- **Architecture**: [docs/architecture.md](docs/architecture.md)
- **Strategy Logic & Results**: [docs/strategy.md](docs/strategy.md)
- **ObjectStore Schema**: [docs/objectstore.md](docs/objectstore.md)
- **Agent Instructions**: [AGENTS.md](AGENTS.md)

## Project Structure

```
Alpha101Portfolio/
├── main.py          # Algorithm entry point — universe from the score file, daily rebalance
├── models/          # Alpha (point-in-time score read), portfolio (quintile L/S), execution, logging
├── domain/          # Config, DTOs, signals/cross_sectional_rank.py (shared, symlinked)
├── data/            # alpha_scores.csv — notebook export, test window only (committed)
├── docs/            # Documentation
└── research/        # Marimo research notebooks
```

## Strategy Overview

| Aspect | Description |
|--------|--------------|
| Type | Cross-sectional equity long/short (price and volume signals) |
| Asset Class | US Equity |
| Universe | Point-in-time top 300 by market cap (409 tickers scored in the test window) |
| Signals | All 101 formulas implemented; 90 selected by training significance, 2 flagged and excluded as degenerate |
| Model | Ridge regression on cross-sectionally ranked alpha values |
| Long/Short split | Top quintile / bottom quintile entry, equal-weighted; held names stay until rank exits a wider 30%-ile band (turnover hysteresis) |
| Gross exposure | 100% (50% long / 50% short) |
| Rebalance | Daily, five minutes after the open |
| Transaction cost | 2 bps per side, explicit in `domain/config.py` |
| Backtest window | 2021-01-01 to 2024-12-31 (held-out test period) |
| Benchmark | SPY |

## ObjectStore Outputs

| File | Description |
|------|--------------|
| `alpha101_portfolio/daily_snapshots.csv` | Per-rebalance portfolio metrics |
| `alpha101_portfolio/positions.csv` | Position data |
| `alpha101_portfolio/trades.csv` | Trade history |

## Contributing

See [AGENTS.md](AGENTS.md) for guidelines on making changes to this project.
