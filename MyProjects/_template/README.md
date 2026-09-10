# {{STRATEGY_NAME}}

{{STRATEGY_DESCRIPTION}}

> Do not copy this directory directly: it contains template tokens. From the
> Q-agent repository root, render a complete copy with
> `python scripts/create_strategy.py {{PROJECT_NAME}}`.

## Quick Start

```bash
# Activate environment
cd /path/to/Q-agent
source venv/bin/activate
cd MyProjects

# Run cloud backtest
lean cloud push --project "{{PROJECT_NAME}}" --force
lean cloud backtest "{{PROJECT_NAME}}" --name "Test"
```

## Documentation

- **Project Overview**: [claude.md](claude.md)
- **Architecture**: [docs/architecture.md](docs/architecture.md)
- **Strategy Logic**: [docs/strategy.md](docs/strategy.md)
- **ObjectStore Schema**: [docs/objectstore.md](docs/objectstore.md)
- **Agent Instructions**: [AGENTS.md](AGENTS.md)

## Project Structure

```
{{PROJECT_NAME}}/
├── main.py          # Algorithm entry point
├── models/          # Alpha, portfolio, execution, logging
├── domain/          # Business logic, DTOs, config
├── docs/            # Documentation
└── research/        # Jupyter notebooks
```

## Strategy Overview

| Aspect | Description |
|--------|-------------|
| Type | {{STRATEGY_TYPE}} |
| Asset Class | {{ASSET_CLASS}} |
| Rebalance | {{REBALANCE_FREQUENCY}} |

## Key Parameters

| Parameter | Value |
|-----------|-------|
| {{PARAM_1}} | {{VALUE_1}} |
| {{PARAM_2}} | {{VALUE_2}} |

## ObjectStore Outputs

| File | Description |
|------|-------------|
| `{{objectstore_namespace}}/daily_snapshots.csv` | Daily portfolio metrics |
| `{{objectstore_namespace}}/positions.csv` | Position data |
| `{{objectstore_namespace}}/trades.csv` | Trade history |

## Contributing

See [AGENTS.md](AGENTS.md) for guidelines on making changes to this project.
