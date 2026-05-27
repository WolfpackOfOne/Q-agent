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

1. Create a feature branch
2. Make focused changes
3. Update documentation where appropriate
4. Ensure no secrets or credentials are committed
5. Open a pull request into `main`

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
