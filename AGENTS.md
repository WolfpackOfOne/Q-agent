# AGENTS.md - AI Agent Guidelines for QuantConnect Workspace

## Purpose

This document provides guardrails and expectations for AI agents working in this QuantConnect workspace. It is **project-agnostic** and applies to any algorithm developed here.

For project-specific rules, check for `AGENTS.md` or `claude.md` files within individual project directories.

---

## Workspace Structure

```
Q-agent/
├── venv/                    # Shared Python virtual environment
├── Lean/                    # LEAN engine checkout (OUT OF SCOPE - do not edit)
├── AGENTS.md                # This file (workspace-level guidelines)
├── claude.md                # Workspace setup and CLI reference
├── Dockerfile               # Workspace runtime image (LEAN CLI + pipelines + marimo)
├── .dockerignore            # Build-context exclusions; mirrors .gitignore
├── .github/workflows/       # CI: tests, docs, secret-scan, docker (GHCR publish)
├── .claude/
│   ├── agents/              # Agent prompts (new-strategy-coder, new-pipeline-coder, ...)
│   └── skills/              # Project-scoped skills (/docker-workflow, /marimo-pair, ...)
├── infrastructure/          # Data pipelines & tooling (NOT algorithm code)
│   └── pipelines/
│       ├── crypto/              # CCXT crypto OHLCV pipeline
│       ├── edgar/               # SEC EDGAR fundamentals (edgartools)
│       ├── openbb/              # OpenBB Platform notes (interactive use)
│       ├── polymarket/          # Polymarket metadata and prices pipeline
│       ├── wrds/                # WRDS/CRSP pipeline
│       ├── yfinance/            # Yahoo Finance OHLCV pipeline
│       └── treasury_gov_rates/  # Treasury.gov daily par yield curve
├── References/              # Reference notes, papers, and repo index
└── MyProjects/              # Active strategy code lives here (each project is typically its own Git repo)
    ├── lean.json            # LEAN CLI configuration (shared, gitignored)
    ├── data/                # Local sample market data (gitignored; populate via `lean init`)
    ├── storage/             # ObjectStore artifacts (gitignored)
    ├── .claude/agents/      # Agent-specific guides (lean-cli.md, github-sync.md)
    ├── shared/              # Reusable signal atoms (never pushed to any project)
    │   └── signals/         # Pure Python signal files — symlinked into projects that need them
    └── <ProjectName>/       # Individual project repo
        ├── main.py          # Composition root (QCAlgorithm entry point)
        ├── config.json      # Cloud/local IDs (NOT committed)
        ├── AGENTS.md        # Project-specific agent rules (optional)
        ├── claude.md        # Project-specific documentation (optional)
        ├── docs/            # Detailed documentation (optional)
        └── ...              # Project modules (atoms, molecules, organisms)
```

### Key Assumptions

- Each project is a QuantConnect algorithm intended to run via LEAN CLI
- Each `MyProjects/<ProjectName>` directory should be treated as its own Git repository unless proven otherwise
- `infrastructure/pipelines/` subdirectories are workspace-managed pipeline code unless a nested `.git/` proves otherwise
- The `Lean/` directory is an engine checkout and is **out of scope for edits**
- All projects use the shared `venv/` Python environment
- A workspace-level Docker image is published to `ghcr.io/wolfpackofone/q-agent:latest` on every push to `main`. Use it as a reproducible runtime; do not bake credentials into derivative images. See `docs/docker.md` and `.claude/skills/docker-workflow/SKILL.md`.
- Project-level documentation takes precedence over workspace-level guidelines

---

## Finding Project Documentation

Before working on any project, check for these documentation files:

| File | Purpose |
|------|---------|
| `<Project>/AGENTS.md` | Project-specific agent rules and guardrails |
| `<Project>/claude.md` | Project overview, parameters, CLI commands |
| `<Project>/README.md` | General project documentation |
| `<Project>/docs/` | Detailed documentation folder |
| `<Project>/ARCHITECTURE.md` | System architecture and design |

### Documentation Examples in This Workspace

- **Project scaffold**: `MyProjects/_template/` — atomic structure layout with `main.py`, `domain/`, `models/`, `docs/`
- **Agent CLI guides**: `MyProjects/.claude/agents/lean-cli.md`

---

## Standard Architecture: Atomic Structure

All projects should follow **atomic structure** - a layered decomposition where small units do one job and compose upward.

### Layer Definitions

```
┌─────────────────────────────────────────────────────────────┐
│                    COMPOSITION ROOT                          │
│                      (main.py)                               │
│         QCAlgorithm facade, wires models together            │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                       ORGANISMS                              │
│            Domain orchestrators with state                   │
│     (alpha, portfolio, execution, logging, risk)             │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                       MOLECULES                              │
│              Single-domain business rules                    │
│   (signal math, constraint checks, tag parsing, Greeks)      │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                        ATOMS                                 │
│           Pure utilities, constants, data types              │
│        (enums, DTOs, config values, pure functions)          │
└─────────────────────────────────────────────────────────────┘
```

### Core Principles

1. **One-way dependency flow** - Lower layers never import from higher layers
2. **Explicit interfaces** - Clear contracts between layers
3. **Single responsibility** - Each unit does one job
4. **Pure functions for critical logic** - Signal math, risk calculations, constraint checks
5. **Composition over inheritance** - Wire together small units

### Directory Structure

```
<ProjectName>/
├── main.py              # COMPOSITION ROOT: QCAlgorithm, wires everything
├── models/              # ORGANISMS: domain orchestrators
│   ├── alpha.py         # Signal generation orchestrator
│   ├── portfolio.py     # Portfolio construction orchestrator
│   ├── execution.py     # Execution orchestrator
│   └── logger.py        # Logging facade (may delegate to focused loggers)
├── domain/              # MOLECULES + ATOMS
│   ├── signals/         # Signal math (pure functions)
│   │                    #   Files here may be symlinks → MyProjects/shared/signals/
│   │                    #   lean cloud push follows symlinks; QC sees real files
│   ├── constraints/     # Constraint checks (pure functions)
│   ├── models.py        # Data types, DTOs, enums
│   └── config.py        # Constants and defaults
└── infrastructure/      # External integrations (optional)
    ├── qc/              # QuantConnect adapters
    └── persistence/     # ObjectStore writers
```

### Why Atomic Structure?

**For AI-assisted development:**
- Smaller scoped files reduce ambiguity in prompts
- AI-generated diffs become local and reviewable
- Behavior-critical math sits in pure functions (testable, verifiable)
- Compare outputs at subsystem boundaries

**For algorithmic trading:**
- Natural fit to pipeline: signal → risk/portfolio → execution → logging
- Reproducibility of signals (pure functions)
- Explicit risk constraint ordering
- Deterministic order tagging and cancellation
- Clean attribution between model layers
- Stable logs and schemas for forensic analysis

### Layer Dependency Rules

| Layer | Can Import From | Cannot Import From |
|-------|-----------------|-------------------|
| Atoms | Python stdlib only | Molecules, Organisms, Root |
| Molecules | Atoms | Organisms, Root, QuantConnect* |
| Organisms | Molecules, Atoms | Root |
| Composition Root | All layers | - |

*Exception: Infrastructure adapters in `infrastructure/qc/` may import QuantConnect

---

## Rules for AI Agents

### General Principles

1. **Read project docs first** - Check for AGENTS.md, claude.md, docs/ before touching core logic
2. **Prefer small, incremental changes** - Avoid broad refactors unless explicitly requested
3. **Preserve atomic structure** - Respect layer boundaries and dependency flow
4. **Keep edits scoped** - Don't touch other projects or `Lean/`
5. **Ask clarifying questions** when changes affect strategy behavior

### Before Making Changes

- [ ] Read project-specific documentation (if it exists)
- [ ] Identify which layer the change belongs to
- [ ] Verify the change respects dependency flow
- [ ] Check if the change affects trading behavior
- [ ] Confirm the change scope matches the request

---

## Safe Change Guidelines

### Safe Actions (No Approval Needed)

- Changes to files explicitly requested
- Documentation updates describing current behavior
- Research notebook edits when asked
- Bug fixes with clear, limited scope
- Adding logging or debug output
- Refactoring within a single layer (not crossing boundaries)

### Requires Explicit Approval

- Changes to risk parameters, position sizing, or exposure limits
- Modifications to signal generation or entry/exit logic
- Changes to data subscriptions or universe selection
- Cross-layer refactoring or architectural changes
- Any change that could alter live trading behavior
- Changes to ObjectStore keys or data schemas

### Preserving Atomic Structure

When making changes:
- **Atoms** should remain pure (no side effects, no external dependencies)
- **Molecules** should contain single-domain logic only
- **Organisms** orchestrate but don't implement business math
- **Composition Root** (main.py) should stay thin - just wiring

---

## Prohibited Actions

1. **Never edit `Lean/`** or engine files
2. **Never modify shared configuration** without explicit instruction:
   - `MyProjects/lean.json`
   - `MyProjects/<Project>/config.json`
3. **Never change generated artifacts** unless asked:
   - `backtests/`
   - `__pycache__/`
   - `infrastructure/pipelines/*/lean-data/`
   - `infrastructure/pipelines/*/data/raw/`
   - `MyProjects/storage/`
   - `MyProjects/data/`
4. **Never introduce live trading actions** or brokerage credentials without explicit approval
5. **Never commit secrets** or environment-specific files
6. **Never change ObjectStore keys** without explicit migration plan
7. **Never violate layer dependencies** (e.g., atoms importing from organisms)

---

## Testing & Validation

### Validation Methods

1. **Syntax check** (quick, local):
   ```bash
   python -m py_compile main.py
   python -m py_compile models/*.py domain/*.py
   ```

2. **Local backtest** (requires Docker Desktop running):
   ```bash
   # For the 30-stock equity universe: pull fresh WRDS data first (see infrastructure/pipelines/wrds/claude.md)
   # Ensure lean.json data-folder points to infrastructure/pipelines/wrds/lean-data or "data"
   cd ~/Documents/Q-agent && source venv/bin/activate && cd MyProjects
   lean backtest "<ProjectName>"
   ```

3. **Cloud backtest** (authoritative, full data):
   ```bash
   lean cloud push --project "<ProjectName>" --force
   lean cloud backtest "<ProjectName>" --name "Description"
   ```

4. **Research notebook debugging** (when a notebook fails inside `lean research`):
   ```bash
   # Find the active research container
   docker ps --format 'table {{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}'

   # Inspect saved outputs/errors already embedded in the notebook file
   python - <<'PY'
   import json
   from pathlib import Path
   nb = json.loads(Path('MyProjects/<ProjectName>/research/<notebook>.ipynb').read_text())
   for i, cell in enumerate(nb.get('cells', [])):
       if cell.get('cell_type') != 'code':
           continue
       for out in cell.get('outputs', []):
           if out.get('output_type') == 'error':
               print(f'CELL {i}:', out.get('ename'), out.get('evalue'))
   PY

   # Run the notebook headlessly inside the running research container
   docker exec <container_id> sh -lc \
     'cd /LeanCLI && jupyter nbconvert --to notebook --execute "research/<notebook>.ipynb" --output "/tmp/<notebook>.executed.ipynb"'
   ```

   Notes:
   - The live Jupyter kernel and headless `nbconvert` path are not always equivalent in LEAN research containers. If `nbconvert` fails earlier than the browser session, inspect the running container logs with `docker logs <container_id>`.
   - For hard-to-reproduce notebook issues, run code directly inside the active research container with `docker exec <container_id> sh -lc 'python - <<\"PY\" ... PY'` so the working directory, mounted `/LeanCLI` project, `/Storage`, and `/Lean/Launcher/bin/Debug` paths match the live environment.
   - Prefer this container-based validation over guessing from the notebook JSON alone when debugging `QuantBook()`, ObjectStore access, or LEAN startup/configuration issues.

### Atomic Structure Verification

- Compare outputs at subsystem boundaries
- Verify pure functions produce deterministic results
- Check that layer dependencies flow downward only
- Confirm ObjectStore schemas remain stable

---

## Style & Conventions

### Code Style

- Follow existing style within each project
- Mirror naming conventions already in use
- Keep QCAlgorithm entry points consistent (`Initialize`, `OnData`, scheduled handlers)

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `CompositeAlphaModel`, `PositionTracker` |
| Functions/Methods | snake_case | `calculate_signal`, `check_constraint` |
| Constants | UPPER_SNAKE_CASE | `MAX_EXPOSURE`, `TARGET_DELTA` |
| Private methods | _leading_underscore | `_internal_helper` |
| Pure functions | Verb phrases | `compute_greeks`, `parse_order_tag` |

### Standard Imports

```python
from AlgorithmImports import *  # QuantConnect standard (composition root only)
```

### Logging

- Use clear, minimal logging output
- Avoid noisy logs unless debugging is requested
- Use appropriate log levels: `Debug()`, `Log()`, `Error()`

---

## ObjectStore Conventions

ObjectStore persists data during backtests for research analysis.

### Best Practices

- Each project uses its own namespace (e.g., `projectname/`)
- Do not change existing keys without a migration plan
- Document schemas in each project's `docs/objectstore.md` (or equivalent)
- Keep schemas stable - add columns, don't rename/remove

### Common Pattern

```python
# Writing CSV data
self.ObjectStore.Save("namespace/filename.csv", csv_string)

# Reading in research notebook
from io import StringIO
import pandas as pd

data_str = qb.ObjectStore.Read("namespace/filename.csv")
df = pd.read_csv(StringIO(data_str), parse_dates=['date'])
```

---

## Git & Version Control

### Repository Boundary

- The workspace root and each `MyProjects/<ProjectName>` may have different `.git` directories
- `infrastructure/` is currently tracked by the workspace repo; do not treat its pipeline folders as submodules unless `git rev-parse --show-toplevel` from that folder says otherwise
- Before running `git status`, `git add`, `git commit`, `git push`, or `git pull`, confirm which repository owns the files you are touching
- For strategy work, default to running Git commands from inside the project directory, not from the workspace root
- Do not assume that changes under `MyProjects/` belong to the workspace-level repository
- Shared assets under `MyProjects/.claude/`, `MyProjects/data/`, and `MyProjects/storage/` may be governed by the workspace repository instead of a project repo

### Workspace Remote — `main` Is Branch-Protected

The workspace repo has TWO git remotes on disk and direct pushes to `main` are blocked by GitHub policy.

| Remote | URL | Use |
|---|---|---|
| `q-agent` | `WolfpackOfOne/Q-agent` | **Canonical workspace repo.** Local `main` tracks `q-agent/main`. This is the PR target. |
| `origin` | `WolfpackOfOne/QuantConnect_Master` | A separate, divergent repo. Do **not** push to its `main`. |

Direct `git push q-agent main` is rejected:
```
remote: error: GH013: Repository rule violations found for refs/heads/main.
remote: - Changes must be made through a pull request.
```

The required workflow:
```bash
git checkout -b feature/<descriptive-name>
# ... commits ...
git push -u q-agent feature/<descriptive-name>
gh pr create --repo WolfpackOfOne/Q-agent --base main --head feature/<descriptive-name> --title "..." --body "..."
# Merge via the GitHub UI (or `gh pr merge --merge` once CI passes)
```

If a rebase puts work onto local `main` by accident, the recovery is:
```bash
git branch feature/<name> HEAD          # park the work on a feature branch
git reset --hard q-agent/main           # main back to the protected HEAD
git checkout feature/<name>
git push -u q-agent feature/<name>
```
Never `git push --force` to `main` even with the `--force-with-lease` cushion — the branch protection rejects it regardless.

### Files to Commit

- `main.py` and all algorithm modules
- Documentation files (README.md, AGENTS.md, claude.md, docs/)
- `.gitignore`
- `requirements.txt` (if present)

### Files NOT to Commit

- `config.json` (contains organization-id, cloud-id)
- `backtests/` (regeneratable)
- `__pycache__/`
- `.DS_Store`
- Any file with `token`, `secret`, `key`, `password` in name

### Commit Message Style

Use descriptive, imperative messages:
```bash
# Good
git commit -m "Add momentum filter to signal molecule"
git commit -m "Extract constraint logic to domain layer"

# Bad
git commit -m "updates"
git commit -m "fixed stuff"
```

---

## Three-System Sync

Projects may sync across three independent systems:

| System | Location | Sync Command |
|--------|----------|--------------|
| Local Git | Project-specific `.git/` (usually inside `MyProjects/<ProjectName>/`) | `git push` / `git pull` |
| GitHub | Remote repo | (via git) |
| QC Cloud | Cloud project | `lean cloud push` / `lean cloud pull` |

**Important**: Git and QC Cloud are independent. Sync both if changes should appear everywhere.

See `MyProjects/.claude/agents/github-sync.md` for detailed workflows.

---

## Proposing Larger Changes

For changes beyond simple fixes:

1. **Provide a design note**:
   - Intent: What problem does this solve?
   - Scope: Which layers/files will be touched?
   - Behavior changes: What will work differently?

2. **Propose incremental steps**:
   - Break into smaller, testable changes
   - Include validation checkpoints
   - Verify at subsystem boundaries

3. **Update documentation**:
   - Reflect behavior changes in project docs
   - Update architecture docs if structure changes

---

## Creating a New Project

When setting up a new QuantConnect project with atomic structure:

### Recommended Directory Structure

```
<ProjectName>/
├── main.py                  # Composition root
├── models/                  # Organisms
│   ├── __init__.py
│   ├── alpha.py
│   ├── portfolio.py
│   ├── execution.py
│   └── logger.py
├── domain/                  # Molecules + Atoms
│   ├── __init__.py
│   ├── models.py            # DTOs, enums
│   ├── config.py            # Constants, defaults
│   └── <feature>/           # Feature-specific molecules
├── docs/                    # Documentation
│   ├── architecture.md
│   ├── strategy.md
│   └── objectstore.md
├── research/                # Jupyter notebooks
├── AGENTS.md                # Project-specific agent rules
├── claude.md                # Project overview
└── README.md
```

### Using Shared Signals

`MyProjects/shared/signals/` holds reusable signal atoms that can be shared across projects without duplicating code. Projects consume them via symlinks.

**How it works:** `lean cloud push` follows symlinks when walking the project directory and uploads the file content to QC cloud. The file appears as a normal file on QC — it never sees the symlink. `shared/` itself lives outside every project directory and is never pushed.

**One-time setup** (run from inside the project directory):
```bash
mkdir -p domain/signals
ln -s ../../../shared/signals/my_signal.py domain/signals/my_signal.py
```

The target is **three `..` deep** — symlink targets resolve relative to the symlink's *location* (`<Project>/domain/signals/`), not the cwd. Two `..` produces a dangling link that fails at import time. Verify with `ls -la domain/signals/my_signal.py`.

See `MyProjects/shared/README.md` for the full convention and the bundled-data pattern that often pairs with it.

**Rules for agents:**
- Signal files in `shared/signals/` must be pure Python — no `from AlgorithmImports import *`, no LEAN types
- When a project needs a shared signal, create the symlink; do not copy the file
- When editing a shared signal, edit `shared/signals/` — never the symlink copy inside a project
- Do not create symlinks that point outside `MyProjects/shared/` (keeps paths predictable)
- Always use **relative** symlink targets, never absolute

**Local backtests require an extra Docker mount.** `lean backtest` mounts only the project dir into Docker, so a symlink whose target lives outside the project (e.g. `../../../shared/...`) dangles inside the container. The wrapper `scripts/lean-backtest.sh` adds the necessary `--extra-docker-config` volume mount; use it instead of `lean backtest` directly. Cloud backtests are unaffected — `lean cloud push` resolves symlinks at upload time and inlines the file content.

### Bundled Per-Project Data

Some projects need to ship a small CSV alongside the algorithm (e.g. an alt-data snapshot, a static config). The convention:

```
<Project>/
├── data/                # tracked, committed
│   └── <name>.csv       # bundled snapshot — uploaded by `lean cloud push`, read in Initialize
└── tools/               # tracked
    └── refresh_<name>.py  # one-off fetcher run manually; NOT imported by the algorithm
```

Important: `MyProjects/data/` (workspace level) is gitignored, but `MyProjects/<Project>/data/*.csv` IS committable — the per-project `data/` is treated as bundled algorithm input, not regenerable local cache. The project's own `.gitignore` should *not* exclude `data/`.

The algorithm reads the CSV from disk in `Initialize` — no runtime HTTP calls. Refresh by running `python tools/refresh_<name>.py` manually, then re-pushing. Worked example: `MyProjects/ElectionIndustryBeta/{data/trump_prob.csv, tools/refresh_trump_prob.py}`.

**Path resolution:** use a `__file__`-relative path, not a plain relative path. LEAN's cwd at runtime differs between local Docker and cloud, so `pd.read_csv("data/foo.csv")` is not reliable. Use:
```python
import os
here = os.path.dirname(os.path.abspath(__file__))
pd.read_csv(os.path.join(here, "data", "foo.csv"), parse_dates=["date"])
```
For belt-and-suspenders, fall back to `self.ObjectStore.Read("data/foo.csv")` (pre-populate via `lean cloud object-store set ...`).

**Index alignment with LEAN bars:** `self.History(...)` returns timezone-aware bar-end timestamps (`2024-10-15 16:00:00-04:00`); a parsed CSV produces tz-naive midnight Timestamps. Inner-joining the two silently yields zero overlap. Normalise the History index at the LEAN boundary to tz-naive midnight before joining — keeps pure-Python signal atoms format-agnostic. Worked example: `MyProjects/ElectionIndustryBeta/main.py::_recent_returns`.

### Documentation Checklist

Create these files to help agents work effectively:

1. **`claude.md`** - Project overview:
   - Strategy summary and key parameters
   - Project structure map
   - LEAN CLI commands
   - ObjectStore keys and schemas

2. **`AGENTS.md`** (optional) - Project-specific rules:
   - Strategy invariants (rules that must not change)
   - Core business logic boundaries
   - Layer-specific notes

3. **`docs/`** folder:
   - `architecture.md` - Layer breakdown
   - `strategy.md` - Signal/portfolio/execution logic
   - `objectstore.md` - Data output schemas

---

## Quick Reference

| Action | Safe? | Notes |
|--------|-------|-------|
| Fix typo in documentation | Yes | |
| Add logging statement | Yes | |
| Refactor within one layer | Yes | If scope is clear |
| Fix obvious bug | Yes | If clearly scoped |
| Move code between layers | **Ask** | Affects architecture |
| Change strategy parameter | **Ask** | Affects trading behavior |
| Add new data subscription | **Ask** | May affect costs/performance |
| Change ObjectStore keys | **No** | Requires migration plan |
| Modify config.json | **No** | Without explicit instruction |
| Edit Lean/ directory | **No** | Out of scope |

---

## Additional Resources

- **Project scaffold**: `MyProjects/_template/` — reference atomic structure layout
- **LEAN CLI guide**: `MyProjects/.claude/agents/lean-cli.md`
- **GitHub sync workflow**: `MyProjects/.claude/agents/github-sync.md`
- **References library**: `References/index.md` — books, papers, repos (vollib, ffn, FinancePy, optlib, …), notes
- **QuantConnect Docs**: https://www.quantconnect.com/docs
- **LEAN CLI Docs**: https://www.quantconnect.com/docs/v2/lean-cli
