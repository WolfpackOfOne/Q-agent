# Q-agent

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Security Policy](https://img.shields.io/badge/security-policy-blue.svg)](SECURITY.md)

Q-agent is an open-source teaching and research workspace for quantitative finance, QuantConnect, LEAN CLI workflows, and reproducible trading strategy development.

The project is designed for students, researchers, and practitioners who want to learn how professional quantitative research codebases are organized. It combines strategy scaffolding, agent guidelines, notebook workflows, dataset research ideas, and QuantConnect development practices in one workspace.

## What This Repository Is

This repository is a master workspace for:

- QuantConnect and LEAN CLI development
- Reproducible quantitative finance research
- Teaching students professional repository workflows
- Organizing research notebooks and strategy examples
- Building modular trading strategy prototypes
- Using AI coding agents safely and consistently

Individual strategy projects may live in their own repositories, while this repository provides the shared structure, documentation, templates, and workflow conventions.

## Who This Is For

- Masters students learning quantitative finance and systematic trading
- Students building public GitHub portfolios
- Researchers prototyping trading strategies
- Instructors teaching applied financial technology
- Developers learning QuantConnect and LEAN CLI workflows
- AI-assisted coding users who want a controlled project structure

## Repository Map

```text
Q-agent/
|-- README.md
|-- LICENSE
|-- CONTRIBUTING.md
|-- SECURITY.md
|-- CREDENTIALS.md
|-- AGENTS.md
|-- claude.md
|-- .env.example
|-- docs/
|   |-- getting-started.md
|   |-- project-map.md
|   |-- research-examples.md
|   |-- architecture.md
|   |-- release-checklist.md
|-- MyProjects/
|   |-- _template/
|   |-- .claude/agents/
|   |-- data/             # gitignored; populate via `lean init`
|   |-- storage/          # gitignored
|   |-- lean.json         # gitignored
|   |-- <ProjectName>/
|-- infrastructure/
|   |-- pipelines/        # crypto, edgar, polymarket, wrds, yfinance, ...
|-- References/
|   |-- books/
|   |-- papers/
|   |-- notes/
|   |-- repos/
|-- .github/
|   |-- pull_request_template.md
|   |-- workflows/
```

## Architecture Overview

Projects in this workspace follow an atomic structure:

```text
main.py
  |
  v
models/
  |
  v
domain/
  |
  v
pure functions, DTOs, config, validation, metrics
```

The goal is to keep the composition root thin, isolate orchestration logic, and place reusable business logic in testable modules.

See [docs/architecture.md](docs/architecture.md) for the full architecture guide.

## Getting Started

The fastest path is the Docker image — one command, no host venvs:

```bash
docker pull ghcr.io/wolfpackofone/q-agent:latest
docker run --rm -it -v "$(pwd):/workspace" ghcr.io/wolfpackofone/q-agent:latest
```

That image bundles the LEAN CLI, the infrastructure pipelines, and marimo.
Apple Silicon hosts add `--platform linux/amd64`.

For host-based setup (three separate Python venvs), see
[GETTING_STARTED.md](GETTING_STARTED.md). Full Docker instructions —
mounted dev workflow, credentials, building locally — live in
[docs/docker.md](docs/docker.md).

## Daily Workflow

```bash
cd ~/Documents/Q-agent
source venv/bin/activate
cd MyProjects
lean cloud push --project "<ProjectName>" --force
lean cloud backtest "<ProjectName>" --name "Description"
```

## Research Examples

One runnable notebook is included:

| Notebook | Data sources | Local data required |
|---|---|---|
| [Election & Industry Returns](infrastructure/marimo/notebooks/election_industry_returns.py) | Committed `trump_prob.csv` (Polymarket CLOB), yfinance sector ETFs (XLE, XLF, XLV, XLI, XLK, XLP, XLY, XLU, XLB, XLRE, XLC, XOP, ITA, KBE, IBB, ICLN, TAN, GDX, ITB) | No — committed CSV plus live yfinance. |

See [GETTING_STARTED.md](GETTING_STARTED.md) for how to run it. For broader research directions see [docs/research-examples.md](docs/research-examples.md).

## Documentation

| Document | Purpose |
|---|---|
| [GETTING_STARTED.md](GETTING_STARTED.md) | First-time setup and running the example notebooks |
| [docs/docker.md](docs/docker.md) | Docker image + GHCR workflow |
| [docs/project-map.md](docs/project-map.md) | Repository layout and responsibilities |
| [docs/research-examples.md](docs/research-examples.md) | Research project ideas |
| [docs/architecture.md](docs/architecture.md) | Atomic architecture guide |
| [docs/release-checklist.md](docs/release-checklist.md) | Public release checklist |
| [CREDENTIALS.md](CREDENTIALS.md) | All credentials/API keys used by the workspace |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution workflow |
| [SECURITY.md](SECURITY.md) | Security policy |

## Requirements

- Python 3.11+
- Git
- For the example notebooks: `pip install -r infrastructure/marimo/requirements.txt`
- For QuantConnect/LEAN work: QuantConnect account, LEAN CLI, Docker Desktop
- Optional: WRDS institutional access (one notebook section; skipped automatically if unavailable)

## Open Source License

This project is released under the MIT License. See [LICENSE](LICENSE).

## Important Disclaimer

This repository is for education and research. Nothing in this repository is investment advice. Trading strategies can lose money, and backtests may not reflect live trading results.
