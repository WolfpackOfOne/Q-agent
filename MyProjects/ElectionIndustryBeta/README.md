# ElectionIndustryBeta

Example QuantConnect strategy for the Q-agent workspace.

**Idea.** Each US sector / industry ETF has a measurable sensitivity (β) to daily changes in Polymarket's Trump 2024 win probability. We estimate that β on a rolling 60-day window, long the 3 highest-β ETFs, short the 3 lowest, and rebalance with market orders every trading day.

**Universe.** 19 ETFs — `XLE XLF XLV XLI XLK XLP XLY XLU XLB XLRE XLC XOP ITA KBE IBB ICLN TAN GDX ITB`.

**Signal source.** [`infrastructure/marimo/notebooks/election_industry_returns.py`](../../infrastructure/marimo/notebooks/election_industry_returns.py) — replication of Winterhalter (2025).

**Data.** Polymarket Trump YES-token daily probability, snapshotted into `data/trump_prob.csv` by `tools/refresh_trump_prob.py`. The algorithm never makes HTTP calls.

**Reusable signal.** β math lives in [`MyProjects/shared/signals/election_beta.py`](../shared/signals/election_beta.py) (pure Python). This project consumes it via the symlink `domain/signals/election_beta.py`.

## Quick start

```bash
cd ~/Documents/Q-agent
source venv/bin/activate
cd MyProjects/ElectionIndustryBeta

# Bundle a fresh Polymarket snapshot
python tools/refresh_trump_prob.py

# Push + backtest
cd ..
lean cloud push --project "ElectionIndustryBeta" --force
lean cloud backtest "ElectionIndustryBeta" --name "v1 baseline"
```

See [`claude.md`](claude.md) for the full reference and [`AGENTS.md`](AGENTS.md) for invariants.
