# {{STRATEGY_NAME}} - {{BRIEF_DESCRIPTION}}

## Repository

- **GitHub URL:** {{GITHUB_URL}}
- **Default Branch:** main

## Project Overview

{{STRATEGY_DESCRIPTION}}

## Project Structure

```
{{PROJECT_NAME}}/
├── main.py                  # Composition root (QCAlgorithm)
├── models/                  # Organisms (orchestrators)
│   ├── alpha.py             # Signal generation
│   ├── portfolio.py         # Portfolio construction
│   ├── execution.py         # Order execution
│   └── logger.py            # ObjectStore logging
├── domain/                  # Molecules + Atoms
│   ├── config.py            # Configuration constants
│   ├── models.py            # DTOs, enums
│   └── signals/             # Project-local signals or symlinks to ../../../shared/signals/
├── data/                    # Bundled per-project CSV (committable; see AGENTS.md)
├── tools/                   # One-off refresh scripts (NOT imported by algorithm)
├── docs/                    # Documentation
│   ├── architecture.md      # System architecture
│   ├── strategy.md          # Strategy logic
│   └── objectstore.md       # Data schemas
├── research/                # Jupyter notebooks
├── config.json              # QC cloud config (DO NOT COMMIT)
└── claude.md                # This file
```

**Pattern choice**: this scaffold ships the `models/` files as QC framework subclasses (`AlphaModel` etc.) for production use. For **teaching/example** projects, demote them to plain helper classes called from a scheduled `_rebalance` method — see `AGENTS.md` § "Pattern Choice" and `MyProjects/ElectionIndustryBeta/` as a worked example.

## Strategy Parameters

### Signal Generation

| Parameter | Value | Description |
|-----------|-------|-------------|
| {{PARAM}} | {{VALUE}} | {{DESCRIPTION}} |

### Portfolio Construction

| Parameter | Value | Description |
|-----------|-------|-------------|
| {{PARAM}} | {{VALUE}} | {{DESCRIPTION}} |

### Execution

| Parameter | Value | Description |
|-----------|-------|-------------|
| {{PARAM}} | {{VALUE}} | {{DESCRIPTION}} |

## LEAN CLI Commands

### Setup (Run Once Per Terminal Session)

```bash
cd ~/Documents/Q-agent
source venv/bin/activate
cd MyProjects
```

### Push to Cloud

```bash
lean cloud push --project "{{PROJECT_NAME}}"
```

### Run Cloud Backtest

```bash
lean cloud backtest "{{PROJECT_NAME}}" --name "Description"
```

### Pull from Cloud

```bash
lean cloud pull --project "{{PROJECT_NAME}}"
```

### Full Workflow

```bash
cd ~/Documents/Q-agent
source venv/bin/activate
cd MyProjects
lean cloud push --project "{{PROJECT_NAME}}" --force
lean cloud backtest "{{PROJECT_NAME}}" --name "Test Run"
```

## ObjectStore Data

### Files Created

| File | Description |
|------|-------------|
| `{{objectstore_namespace}}/daily_snapshots.csv` | Daily portfolio metrics |
| `{{objectstore_namespace}}/positions.csv` | Position-level data |
| `{{objectstore_namespace}}/trades.csv` | Trade executions |

See `docs/objectstore.md` for full schema documentation.

### Reading in Research Notebook

```python
from io import StringIO
import pandas as pd

snapshots_str = qb.ObjectStore.Read("{{objectstore_namespace}}/daily_snapshots.csv")
df = pd.read_csv(StringIO(snapshots_str), parse_dates=['date'])
```

## Backtest Configuration

| Setting | Value |
|---------|-------|
| Start Date | {{START_DATE}} |
| End Date | {{END_DATE}} |
| Starting Cash | ${{STARTING_CASH}} |
| Benchmark | {{BENCHMARK}} |

## Git Version Control

### Files Tracked

- `main.py`, `models/*.py`, `domain/*.py`
- Documentation (`docs/`, `claude.md`, `README.md`)
- `.gitignore`

### Files NOT Tracked

- `config.json` (contains QC organization/cloud IDs)
- `backtests/` (regeneratable)
- `__pycache__/`

### Common Git Commands

```bash
git status
git add .
git commit -m "Description"
git push
```

## Common Issues

### "Cannot push - collaboration lock"

```bash
lean cloud push --project "{{PROJECT_NAME}}" --force
```

### "lean: command not found"

```bash
source ~/Documents/Q-agent/venv/bin/activate
```

### Data not available locally

Use cloud backtest instead - cloud has full data access.
