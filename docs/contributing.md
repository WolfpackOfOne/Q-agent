# Contributing

Thank you for contributing to Q-agent.

This repository is an open-source educational and research workspace focused on quantitative finance, QuantConnect workflows, financial datasets, and systematic trading research.

## Goals

- Teach professional quantitative development workflows
- Encourage reproducible research
- Build reusable infrastructure for strategy research
- Maintain high-quality documentation and code standards

## Development Principles

- Keep architecture modular and composable
- Prefer pure functions for core calculations
- Document assumptions clearly
- Avoid hard-coded paths and credentials
- Keep notebooks reproducible
- Write code that students can learn from

## Pull Request Workflow

1. Create a feature branch (`main` is branch-protected — direct pushes are rejected)
2. Make focused changes
3. Update documentation where appropriate
4. Ensure no secrets or credentials are committed
5. Open a pull request into `main`
6. Wait for CI to pass: tests, secret-scan (gitleaks + personal-paths), docs (mkdocs build + linkcheck), and — if `Dockerfile` / `requirements*.txt` / `.dockerignore` change — the docker build

## Reproducible dev environment

You can develop against the host venvs (see [Getting Started](getting-started.md))
or against the prebuilt workspace image:

```bash
docker run --rm -it -v "$(pwd):/workspace" ghcr.io/wolfpackofone/q-agent:latest
```

The image is pinned to a specific `LEAN_VERSION` (visible on the image's GHCR
page) and matches the venvs used by CI, so smoke-test results are
reproducible across machines. See [Docker](docker.md) for the full workflow.

## Commit Style

Keep commit messages short and imperative:

```
Add WRDS sector pipeline
Refactor LEAN notebook utilities
Add Polymarket ingestion example
Improve ETF constituent documentation
```

## Prohibited Content

Do not commit:

- API keys, passwords, or tokens
- QuantConnect or WRDS credentials
- Large raw datasets
- Proprietary research material without permission

## Student Contributions

Students are encouraged to:

- Build research notebooks
- Add datasets and ingestion pipelines
- Improve documentation
- Create reproducible strategy examples
- Add testing and validation tools
