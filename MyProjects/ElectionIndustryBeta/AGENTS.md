# ElectionIndustryBeta — Agent Instructions

For workspace-level guidelines, see `~/Documents/Q-agent/AGENTS.md`.

## Project Summary

- **Strategy**: long/short rotation across 19 US sector + industry ETFs, weighted by each ETF's rolling β to ΔP(Trump win probability) from Polymarket.
- **Architecture**: Atomic Structure (Composition Root → Organisms → Molecules → Atoms).
- **Entry Point**: `main.py` (`ElectionIndustryBeta`).
- **Trade rule**: scheduled daily 5 min after `SPY` open; market orders via `SetHoldings`.

## Architecture

```
main.py              # Composition Root — wires organisms, holds the scheduled handler
├── models/          # Organisms — domain orchestrators
│   ├── alpha.py     # ElectionBetaAlpha     — calls rolling_beta on history
│   ├── portfolio.py # ElectionBetaPortfolio — calls top_bottom_k_betaweighted
│   ├── execution.py # MarketOrderExecutor   — SetHoldings only
│   └── logger.py    # PortfolioLogger        — buffers + saves CSVs to ObjectStore
└── domain/          # Molecules + Atoms
    ├── config.py    # UNIVERSE, LOOKBACK, K, dates, ObjectStore namespace (ATOMS)
    ├── models.py    # Signal DTO, PositionState, … (ATOMS)
    └── signals/
        └── election_beta.py   # SYMLINK → MyProjects/shared/signals/election_beta.py
                                # Pure pandas/numpy. Edit the shared source, never the link.
```

## Strategy Invariants

Do not change without explicit approval:

1. **Signal math lives in `shared/signals/election_beta.py`** — pure pandas/numpy, no LEAN imports. Edits to `domain/signals/election_beta.py` (the symlink target) are forbidden — modify the shared file.
2. **Universe = 19 ETFs in `domain/config.UNIVERSE`** — exactly the notebook universe. Do not silently expand or drop tickers.
3. **Polymarket data is read from disk**, not fetched at runtime. The algorithm never makes HTTP calls. Refresh via `tools/refresh_trump_prob.py`.
4. **`SetHoldings` only.** No `MarketOrder`, no `LimitOrder`, no `SetAlpha`/`SetPortfolioConstruction` framework calls — see the LEAN gotcha in workspace `CLAUDE.md`.
5. **`SetWarmUp(timedelta(days=LOOKBACK + 10))`** must remain in `Initialize`.

## ObjectStore Keys

Stable contract — do not rename without a migration plan:

- `electionbeta/daily_snapshots.csv`
- `electionbeta/positions.csv`
- `electionbeta/trades.csv`

Schemas: see `docs/objectstore.md`.

## Development Workflow

```bash
cd ~/Documents/Q-agent
source venv/bin/activate            # or: source infrastructure/marimo/venv/bin/activate
cd MyProjects

# Refresh the Polymarket snapshot whenever you want fresher data
python ElectionIndustryBeta/tools/refresh_trump_prob.py

# Push + backtest
lean cloud push --project "ElectionIndustryBeta" --force
lean cloud backtest "ElectionIndustryBeta" --name "Description"
```

## Validation

```bash
cd ~/Documents/Q-agent/MyProjects/ElectionIndustryBeta
python -m py_compile main.py models/*.py domain/*.py domain/signals/*.py tools/*.py
```

## Layer Rules

| Layer | Can Import From |
|-------|-----------------|
| `domain/config.py`, `domain/models.py` | stdlib only |
| `domain/signals/*` (shared atoms) | pandas, numpy only |
| `models/*` | `AlgorithmImports`, `domain.*`, pandas/numpy |
| `main.py` | All layers |

Never import upward (e.g. `domain/` importing `models/`).

## Scope Guidance

- **Safe**: signal-math edits *inside* `shared/signals/election_beta.py`, tighter logging, documentation.
- **Ask first**: changing `LOOKBACK`, `K`, universe, ObjectStore keys, rebalance schedule.
- **Prohibited**: editing the symlink at `domain/signals/election_beta.py` directly, adding `SetAlpha`/`SetPortfolioConstruction`, committing `config.json`.
