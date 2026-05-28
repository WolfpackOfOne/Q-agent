# Q-agent Roadmap

## Vision

Q-agent aims to become a reproducible, AI-compatible quantitative research workspace built around:

- pipelines
- notebooks
- LEAN strategies
- reusable signals
- ObjectStore diagnostics
- educational workflows

---

# Recently Shipped

- **Docker / GHCR image** ([#20](https://github.com/WolfpackOfOne/Q-agent/issues/20), [#25](https://github.com/WolfpackOfOne/Q-agent/pull/25)). Public image at `ghcr.io/wolfpackofone/q-agent:latest` bundles LEAN CLI + infrastructure pipelines + marimo. CI builds on every PR, publishes on every push to `main`. See [Docker](docker.md).
- **Workflow-first documentation site** — mkdocs at <https://wolfpackofone.github.io/Q-agent/> with linkcheck on every PR.
- **Personal-paths CI scanner** — `.github/workflows/secret-scan.yml` blocks PRs that leak host home directories.

---

# Near-Term Priorities

## Documentation Hardening

- canonical workflows
- workflow-first navigation
- pipeline catalog
- agent workflows
- reproducibility improvements
- onboarding clarity

## Docker Followups

- multi-arch image (`linux/arm64` so Apple Silicon hosts can pull natively) — [#26](https://github.com/WolfpackOfOne/Q-agent/issues/26)
- support `lean backtest` (local) inside the container — [#27](https://github.com/WolfpackOfOne/Q-agent/issues/27)

---

## Research Workflows

Current focus areas:

- prediction markets
- ETF sensitivity analysis
- macro event research
- volatility targeting
- systematic portfolio construction
- ObjectStore diagnostics

---

# Pipeline Expansion

Potential future pipelines:

- Treasury.gov
- FRED
- SEC insider filings
- options datasets
- futures term structure data
- macroeconomic indicators

---

# Agent-Native Development

Future goals:

- reproducible Claude Code workflows
- notebook generation workflows
- research assistant tooling
- AI-safe refactoring standards
- project-level AGENTS.md conventions

---

# Educational Goals

Q-agent is designed to support:

- graduate quantitative finance education
- systematic trading instruction
- reproducible portfolio projects
- AI-assisted software engineering workflows

---

# Long-Term Direction

Potential future positioning:

- canonical open-source educational quant workspace
- AI-compatible quantitative development environment
- reproducible LEAN research ecosystem
- bridge between academic and operational quant workflows
