# Architecture

ElectionIndustryBeta follows the workspace-standard **atomic structure** described in `~/Documents/Q-agent/AGENTS.md`.

## Layer map

```
┌───────────────────────────────────────────────┐
│            COMPOSITION ROOT                    │
│                  main.py                       │
│   ElectionIndustryBeta(QCAlgorithm)            │
│   - subscribes 19 ETFs                         │
│   - loads bundled Trump-probability CSV        │
│   - schedules _rebalance daily                 │
└─────────────────────┬─────────────────────────┘
                      │
┌─────────────────────▼─────────────────────────┐
│                 ORGANISMS (models/)            │
│  ElectionBetaAlpha     compute_signals(...)    │
│  ElectionBetaPortfolio to_targets(...)         │
│  MarketOrderExecutor   execute(...)            │
│  PortfolioLogger       save_all() → ObjectStore│
└─────────────────────┬─────────────────────────┘
                      │
┌─────────────────────▼─────────────────────────┐
│              MOLECULES + ATOMS                 │
│  domain/config.py    UNIVERSE, LOOKBACK, K …   │
│  domain/models.py    DTOs, enums               │
│  domain/signals/election_beta.py               │
│      → SYMLINK to MyProjects/shared/signals/   │
│      rolling_beta + top_bottom_k_betaweighted  │
│      (pure pandas/numpy)                       │
└───────────────────────────────────────────────┘
```

## Layer dependency rules

| Layer | Imports allowed |
|---|---|
| Atoms (`domain/config.py`, `domain/models.py`) | stdlib only |
| Atoms (signals, pure math) | pandas, numpy |
| Organisms (`models/*`) | `AlgorithmImports`, `domain.*`, pandas |
| Composition root (`main.py`) | All layers |

Dependencies must flow downward only. Atoms know nothing about LEAN.

## Why this layout?

- **Signal reuse**: the β math is decoupled from QuantConnect. The same `shared/signals/election_beta.py` could power a different project tomorrow without copy-paste.
- **Testable atoms**: `rolling_beta` and `top_bottom_k_betaweighted` run under a plain venv — see the unit test in the project history (verification step 1 of the plan).
- **Predictable LEAN surface**: only the composition root and `models/` ever import `AlgorithmImports`. If LEAN's API changes, the blast radius is bounded.

## Why no AlphaModel / PortfolioConstructionModel / ExecutionModel?

Workspace `CLAUDE.md` calls out:
> Avoid the `SetAlpha` + `SetPortfolioConstruction` + coarse universe pattern in teaching projects. Use direct `SetHoldings` calls in a `_rebalance` method instead.

So the classes in `models/` are plain helpers, not LEAN framework subclasses. The scheduled `_rebalance` in `main.py` walks alpha → portfolio → execution → logger directly.

## Symlink mechanics

`domain/signals/election_beta.py` is a relative symlink to `../../../shared/signals/election_beta.py`. `lean cloud push` follows symlinks and uploads the *content* — QC cloud never sees the link, so the cloud build behaves the same as a local clone. `git` records the symlink itself, so collaborators get the same wiring after `git clone`.

Rules:

- Edit the shared file, never the link.
- Do not create symlinks that point outside `MyProjects/shared/`.
