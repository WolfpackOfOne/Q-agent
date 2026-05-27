# {{STRATEGY_NAME}} - Agent Instructions

This file defines project-specific instructions for AI agents working on this strategy.

For workspace-level guidelines, see `~/Documents/Q-agent/AGENTS.md`.

## Project Summary

- **Strategy**: {{STRATEGY_DESCRIPTION}}
- **Architecture**: Atomic Structure (Composition Root → Organisms → Molecules → Atoms)
- **Entry Point**: `main.py` ({{STRATEGY_CLASS}})

## Architecture

```
main.py              # Composition Root - wires models together
├── models/          # Organisms - domain orchestrators
│   ├── alpha.py     # Signal generation
│   ├── portfolio.py # Portfolio construction
│   ├── execution.py # Order execution
│   └── logger.py    # ObjectStore logging
├── domain/          # Molecules + Atoms - pure business logic
│   ├── config.py    # Constants (ATOMS)
│   ├── models.py    # DTOs, enums (ATOMS)
│   └── signals/     # Optional — symlinks to ../../../shared/signals/<name>.py
├── data/            # Optional — bundled per-project CSV (committable)
└── tools/           # Optional — one-off refresh scripts (NOT imported by algorithm)
```

## Pattern Choice — Framework vs Direct SetHoldings

This template ships `models/{alpha,portfolio,execution}.py` as framework subclasses (`AlphaModel`, `PortfolioConstructionModel`, `ExecutionModel`). That's the right shape for production strategies that need the full QC alpha-streaming + insight lifecycle.

**For teaching / example projects, demote them to plain helper classes** called directly from a scheduled `_rebalance(self)` method in `main.py`. This is the workspace-wide rule from `~/Documents/Q-agent/CLAUDE.md` — the QC framework lifecycle (with coarse universe) is hard to follow when explaining a strategy. Direct `SetHoldings` keeps the wiring obvious.

- **Production pattern (this template default)**: classes subclass `AlphaModel` / `PortfolioConstructionModel` / `ExecutionModel`; wired via `SetAlpha` / `SetPortfolioConstruction` / `SetExecution`.
- **Teaching pattern**: same files, same layer roles, but classes are plain Python (no `AlphaModel` parent). `main.py::_rebalance` calls `alpha.compute_signals(...)` → `portfolio.to_targets(...)` → `executor.execute(...)` → `SetHoldings(...)`. Worked example: `MyProjects/ElectionIndustryBeta/`.

Both keep the atomic structure; only the integration with QC's lifecycle differs.

## Strategy Invariants

These rules must NOT change without explicit approval:

1. {{INVARIANT_1}}
2. {{INVARIANT_2}}
3. {{INVARIANT_3}}

## ObjectStore Keys

Keep these keys stable unless migration is explicitly requested:

- `{{objectstore_namespace}}/daily_snapshots.csv`
- `{{objectstore_namespace}}/positions.csv`
- `{{objectstore_namespace}}/trades.csv`

## Development Workflow

```bash
cd ~/Documents/Q-agent
source venv/bin/activate
cd MyProjects
lean cloud push --project "{{PROJECT_NAME}}" --force
lean cloud backtest "{{PROJECT_NAME}}" --name "Description"
```

## Validation

Before handing off code changes:

```bash
python -m py_compile main.py models/*.py domain/*.py
```

Then provide a cloud backtest command (or run one if requested).

## Scope Guidance

- **Safe**: Changes within a single layer that don't affect trading behavior
- **Ask First**: Cross-layer changes, strategy parameter changes, ObjectStore schema changes
- **Prohibited**: Changes to `config.json`, violating layer dependencies

## Layer Rules

| Layer | Can Import From |
|-------|-----------------|
| `domain/` | Python stdlib only |
| `models/` | `domain/`, `AlgorithmImports` |
| `main.py` | All layers |

Never import from a higher layer (e.g., `domain/` importing from `models/`).
