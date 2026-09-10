# NewsSentimentAlpha

Daily long/short equity portfolio ranked by a financial-media news-tone
z-score signal (GDELT), magnitude-weighted, rebalanced daily across a
10-stock universe.

**Result**: parameters were selected using a train (2017-18) / validate
(2019) / test (2020-21) split. The held-out test backtest — real LEAN
execution, zero commissions, trimmed to 2020-01 – 2021-04 where GDELT
coverage of this universe is actually dense — scores **Sharpe 0.907**.
See [docs/strategy.md](docs/strategy.md) § "Validation Methodology" for
the full process.

## Quick Start

```bash
# Activate environment
cd ~/Documents/Q-agent
source venv/bin/activate
cd MyProjects

# Local backtest — use the shared-signal-aware wrapper (not plain `lean backtest`)
bash ~/Documents/Q-agent/scripts/lean-backtest.sh "NewsSentimentAlpha"

# Local research environment
lean research "NewsSentimentAlpha"
```

Cloud commands (optional, not required for local development):

```bash
lean cloud push --project "NewsSentimentAlpha" --force
lean cloud backtest "NewsSentimentAlpha" --name "Test"
```

## Documentation

- **Project Overview**: [claude.md](claude.md)
- **Architecture**: [docs/architecture.md](docs/architecture.md)
- **Strategy Logic**: [docs/strategy.md](docs/strategy.md)
- **ObjectStore Schema**: [docs/objectstore.md](docs/objectstore.md)
- **Agent Instructions**: [AGENTS.md](AGENTS.md)

## Project Structure

```
NewsSentimentAlpha/
├── main.py          # Algorithm entry point — daily rebalance, 1-trading-day signal lag
├── models/           # Alpha (exact-date lookup), portfolio (ranking), execution, logging
├── domain/           # Business logic, DTOs, config, signals/news_tone.py (shared, symlinked)
├── data/             # Bundled per-project CSV — sentiment_panel.csv
├── tools/            # refresh_sentiment.py — regenerate the bundled CSV
├── docs/             # Documentation
├── research/          # Marimo research notebooks (empty for now)
└── Manually_Backtested_Results/  # Drop QC-website backtest downloads here for offline analysis
```

## Strategy Overview

| Aspect | Description |
|--------|-------------|
| Type | Cross-sectional long/short, news-tone factor, magnitude-weighted |
| Asset Class | US Equities |
| Universe | GS, AAPL, JPM, BA, HD, IBM, VZ, V, NKE, CSCO |
| Rebalance | Daily |
| Backtest Window | 2020-01-01 to 2021-04-30 (held-out test period, trimmed to dense GDELT coverage) |
| Gross Exposure | 100% (50% long / 50% short) |
| Sharpe Ratio | 0.907 |

## Data Sources

| Source | Status |
|--------|--------|
| WRDS/CRSP daily equity prices | Local, ready — `infrastructure/pipelines/wrds/lean-data/equity/usa/daily/{ticker}.zip` |
| GDELT financial-media news-tone z-score panel | Bundled — `data/sentiment_panel.csv`, regenerate via `tools/refresh_sentiment.py` |

## ObjectStore Outputs

| File | Description |
|------|-------------|
| `news_sentiment_alpha/daily_snapshots.csv` | Daily portfolio metrics |
| `news_sentiment_alpha/positions.csv` | Position data |
| `news_sentiment_alpha/trades.csv` | Trade history |

## Contributing

See [AGENTS.md](AGENTS.md) for guidelines on making changes to this project.
