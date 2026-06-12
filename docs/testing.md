# Testing

Q-agent's testing strategy is intentionally narrow: cover the **workspace-level infrastructure** that every project depends on, and let `lean cloud backtest` serve as the integration test for strategy-specific logic.

## Scope

Tests live in this repository to protect the shared contracts. They do **not** validate individual strategy math, signal-specific behavior, or anything under `MyProjects/<ProjectName>/`.

### In scope

1. **LEAN data format compliance** — outputs of `infrastructure/pipelines/`
2. **QuantConnect integration contracts** — config files and CLI smoke tests
3. **Repository hygiene** — no committed secrets, `.gitignore` enforcement, symlink integrity
4. **Template validity** — `MyProjects/_template/` remains a usable starting point

### Out of scope

- Strategy logic in any `MyProjects/<ProjectName>/` directory
- Project-specific signals, position sizing, or rebalancing rules
- The `agent_graph_system/` module (separate concern, separate tests)
- Live backtest results — covered by `lean cloud backtest`

### Gray area: `shared/signals/`

The `MyProjects/shared/signals/` library contains pure-Python signal atoms reused across projects. It is workspace infrastructure, not project code. **Decision pending** on whether to include unit tests for these atoms.

## Framework

- **pytest** as the test runner
- **pytest-cov** for coverage reporting
- **pytest-mock** for lightweight mocking
- Markers: `@pytest.mark.integration` for anything needing live services (Neo4j, Chroma, QuantConnect cloud)

Configuration lives in `pyproject.toml` under `[tool.pytest.ini_options]`. Dev dependencies live in `requirements-dev.txt`.

## Test surface

### 1. LEAN data format compliance

Verify that every pipeline in `infrastructure/pipelines/` writes files matching LEAN's expected format.

Assertions per pipeline:

- Column order matches LEAN spec
- Date format is `yyyyMMdd HH:mm`
- Equity prices are scaled by 10000
- Zip archive structure is `{ticker}.zip` containing `{date}_{ticker}_{resolution}_{market}.csv`
- Trade vs. quote schemas use the correct columns

Method: feed each pipeline a small synthetic dataframe and assert the bytes of the output file match the LEAN spec.

### 2. QuantConnect integration contracts

Validate the artifacts that surround the LEAN CLI — not the CLI's network calls themselves.

- Every `MyProjects/<X>/config.json` is valid JSON with required keys (`project-id`, `algorithm-language`)
- `lean.json` (when present) has a valid structure
- Smoke test: `lean --version` succeeds in the CI environment

### 3. Repository hygiene

Defend the public/private boundary between Q-agent and the private QuantConnect workspace.

- No secret patterns (API keys, tokens, `.env` content, AWS keys) appear in tracked files
- `.gitignore` excludes `lean.json`, `data/`, `storage/`, `.env`, and other sensitive paths
- Every `MyProjects/<X>/domain/signals/*.py` symlink resolves to a real file under `MyProjects/shared/signals/`

### 4. Template validity

Ensure `MyProjects/_template/` stays a working scaffold.

- Required structure exists: `main.py`, `models/`, `domain/`
- `python -m py_compile` succeeds on every `.py` file in the template
- A fresh copy can be initialized without manual fixes

## Directory layout

```
Q-agent/
├── pyproject.toml              # [tool.pytest.ini_options]
├── requirements-dev.txt        # pytest, pytest-cov, pytest-mock
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # shared fixtures
│   ├── lean_format/
│   │   ├── test_yfinance_writer.py
│   │   ├── test_wrds_writer.py
│   │   └── ...
│   ├── qc_integration/
│   │   ├── test_config_schema.py
│   │   └── test_lean_cli_smoke.py
│   ├── hygiene/
│   │   ├── test_no_secrets.py
│   │   ├── test_gitignore.py
│   │   └── test_signal_symlinks.py
│   └── template/
│       └── test_template_structure.py
```

The `agent_graph_system/` knowledge-graph subsystem is tested separately under `tests/agent_graph_system/` (ontology rules, deployment gate, provenance, QuantConnect ingestion, context packs). It uses its own fixtures (`conftest.py`) and an isolated in-memory graph. See `agent_graph_system/README.md`.

## Continuous integration

A GitHub Actions workflow at `.github/workflows/tests.yml` runs the default (non-integration) test suite on every pull request.

- Python versions: 3.10, 3.11, 3.12
- Steps: install `requirements-dev.txt`, run `pytest -m "not integration"`
- Upload coverage report as a build artifact

Integration tests requiring live services are excluded from CI and run locally only.

## Running tests locally

```bash
cd ~/Documents/Q-agent
source venv/bin/activate
pip install -r requirements-dev.txt

# Fast unit tests only
pytest

# Including integration tests
pytest -m ""

# With coverage
pytest --cov=infrastructure --cov-report=term-missing
```

## Adding new tests

When you add a new pipeline, a new template file, or a new repository convention, add a corresponding test under the matching directory above. Do **not** add tests for changes inside `MyProjects/<ProjectName>/` — those belong with the project, or are validated by a backtest.
