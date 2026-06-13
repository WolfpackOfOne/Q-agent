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
- **Multi-arch Docker image** — the published manifest supports both `linux/amd64` and `linux/arm64`, so Apple Silicon hosts can pull natively. See [Docker](docker.md).
- **Workflow-first documentation site** — mkdocs at <https://wolfpackofone.github.io/Q-agent/> with linkcheck on every PR.
- **Personal-paths CI scanner** — `.github/workflows/secret-scan.yml` blocks PRs that leak host home directories.
- **Pipeline maturity table** — the data-pipeline catalog distinguishes stable, committed-data, and experimental pipelines.

---

# Near-Term Priorities

## Documentation Hardening

- close remaining docs-to-code consistency gaps
- keep the Golden Path and ElectionIndustryBeta workflow synchronized
- maintain pipeline maturity labels
- improve agent workflow examples
- keep onboarding commands copy-pasteable

## Repo Hygiene / Public Launch

Tracked in [#73](https://github.com/WolfpackOfOne/Q-agent/issues/73):

- issue templates
- stronger PR template
- CODEOWNERS
- CODE_OF_CONDUCT
- label and milestone taxonomy
- README status badges
- dependency policy

## Docker Followups

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

Tracked research feature issues:

- [#52](https://github.com/WolfpackOfOne/Q-agent/issues/52) — passive instability research-to-strategy workflow
- [#62](https://github.com/WolfpackOfOne/Q-agent/issues/62) — walk-forward analysis and bootstrap validation

---

# Pipeline Expansion

Potential future pipelines:

- FRED
- SEC insider filings
- options datasets
- futures term structure data
- macroeconomic indicators

Experimental pipelines already present but still maturing:

- `treasury_gov_rates`
- `fixed_income`
- `macro_rates`

---

# Agent-Native Development

Future goals:

- reproducible Claude Code workflows
- notebook generation workflows
- research assistant tooling
- AI-safe refactoring standards
- project-level AGENTS.md conventions
- graph-backed context packs and retrieval workflows

Graph-system roadmap issues:

- [#54](https://github.com/WolfpackOfOne/Q-agent/issues/54) — hybrid property-graph-first architecture
- [#67](https://github.com/WolfpackOfOne/Q-agent/issues/67) — stale-fact cleanup for merge-only re-ingest

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
