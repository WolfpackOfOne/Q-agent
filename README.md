# Q-agent

[![Tests](https://github.com/WolfpackOfOne/Q-agent/actions/workflows/tests.yml/badge.svg)](https://github.com/WolfpackOfOne/Q-agent/actions/workflows/tests.yml)
[![Docs](https://github.com/WolfpackOfOne/Q-agent/actions/workflows/docs.yml/badge.svg)](https://github.com/WolfpackOfOne/Q-agent/actions/workflows/docs.yml)
[![Security](https://github.com/WolfpackOfOne/Q-agent/actions/workflows/secret-scan.yml/badge.svg)](https://github.com/WolfpackOfOne/Q-agent/actions/workflows/secret-scan.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Q-agent is an open-source teaching and research workspace for quantitative
finance, QuantConnect, LEAN CLI workflows, and reproducible trading-strategy
development.

It gives students a professional repository structure, runnable research
examples, data-pipeline patterns, strategy scaffolding, automated checks, and
guardrails for AI-assisted development.

## Start here

- **New student:** follow [GETTING_STARTED.md](GETTING_STARTED.md).
- **Browse the course documentation:** visit the
  [Q-agent documentation site](https://wolfpackofone.github.io/Q-agent/).
- **Contribute to Q-agent:** read [CONTRIBUTING.md](CONTRIBUTING.md) and work
  through a personal fork.
- **Create your own strategy repository:** render the tested scaffold:

  ```bash
  python scripts/create_strategy.py MyFirstStrategy
  ```

Individual student strategies normally live in their own repositories. This
central repository accepts shared infrastructure, reusable signals,
documentation, tests, and instructor-approved example strategies.

## Reproducible Docker environment

For the course baseline, use the immutable release image rather than the moving
`latest` development tag:

```bash
docker pull ghcr.io/wolfpackofone/q-agent:v0.1.0
docker run --rm -it -v "$(pwd):/workspace" \
  ghcr.io/wolfpackofone/q-agent:v0.1.0
```

The image supports both `linux/amd64` and `linux/arm64`, including Apple Silicon,
without a `--platform` override. The `latest` tag follows `main` and is intended
for testing upcoming changes.

Host installs use `constraints-course.txt` to pin direct course dependencies.
The versioned container is the authoritative fully resolved environment.

See [docs/docker.md](docs/docker.md) for mounted development, credentials,
pipelines, notebooks, and LEAN limitations.

## Repository map

```text
Q-agent/
├── .github/              # PR policy, issue forms, ownership, CI and security
├── docs/                 # Published student and contributor documentation
├── infrastructure/       # Shared pipelines and marimo notebooks
├── MyProjects/
│   ├── _template/        # Rendered by scripts/create_strategy.py
│   ├── shared/           # Reusable pure-Python signals
│   └── ...               # Instructor-approved examples only
├── References/           # Curated research notes and source index
├── scripts/              # Scaffolding, policy checks, and LEAN helpers
├── tests/                # Workspace, graph, template, and hygiene tests
├── AGENTS.md              # Repository-wide AI agent guardrails
├── CREDENTIALS.md         # Credential setup without secret values
└── SECURITY.md            # Private reporting and security controls
```

Projects follow an atomic dependency flow:

```text
main.py → models/ → domain/ → pure functions, DTOs, and configuration
```

See [docs/architecture.md](docs/architecture.md) for the complete model.

## Included research example

The Election & Industry Returns notebook combines a committed Polymarket
probability fixture with live yfinance ETF prices:

```bash
python -m venv infrastructure/marimo/venv
source infrastructure/marimo/venv/bin/activate
python -m pip install -r infrastructure/marimo/requirements.txt
marimo run infrastructure/marimo/notebooks/election_industry_returns.py --port 2719
```

Windows PowerShell activation:
`infrastructure\marimo\venv\Scripts\Activate.ps1`.

## Requirements

- Python 3.11 or 3.12
- Git
- Docker Desktop for the container or local LEAN workflow
- A QuantConnect account for cloud or LEAN strategy work
- Optional institutional credentials only for the pipelines that document them

Never commit credentials, account identifiers, private data, generated
backtests, or large datasets. See [CREDENTIALS.md](CREDENTIALS.md) and
[SECURITY.md](SECURITY.md).

## License and disclaimer

Q-agent is released under the [MIT License](LICENSE). It is for education and
research, not investment advice. Trading strategies can lose money, and
backtests may not represent live results.
