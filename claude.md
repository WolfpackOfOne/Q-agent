<!--
claude_md:
  version: 2.0.0
  last_updated: 2026-04-02
  owners: [WolfpackOfOne]
  review_cadence: "monthly + after major architecture changes"
  changelog:
    - date: 2026-04-02
      change: "Full restructure per deep-research-report best practices"
    - date: 2026-03-30
      change: "Initial CLI reference version"
-->

# claude.md - QuantConnect Algorithm Workspace

## Purpose

Help Claude ship correct, safe algorithm changes in this QuantConnect LEAN workspace with minimal back-and-forth.

Success means:
- Changes are small and targeted to the request.
- Algorithms compile and backtest without errors.
- LEAN API gotchas are avoided proactively.
- No secrets or credentials are committed.

## Scope

Applies repo-wide. For project-specific rules, check `<ProjectName>/claude.md` or `<ProjectName>/docs/`.
Architecture guidelines live in `AGENTS.md`. Push detailed playbooks to skills rather than growing this file.

## Working style

- Be concise and direct.
- Prefer incremental steps; verify assumptions by reading code before suggesting changes.
- Ask clarifying questions only when blocked.
- For non-trivial changes, propose a brief plan before editing.

## Safety & guardrails

- Never introduce secrets (API keys, tokens, credentials) in code, logs, or docs.
- Never run destructive actions (dropping data, force-pushing, deleting projects) without explicit confirmation.
- Do not edit files inside `Lean/` (reference-only engine repo).
- Always activate the venv before running CLI commands: `source ~/Documents/Q-agent/venv/bin/activate`.
- **`main` is branch-protected on the workspace repo.** Direct pushes are rejected by GitHub policy (`GH013: Changes must be made through a pull request`). Always: branch → commit → push the branch → `gh pr create` → merge via the GitHub UI.
- **The workspace has two GitHub remotes — push to the right one.** `q-agent` (`WolfpackOfOne/Q-agent`) is the canonical workspace repo and what local `main` tracks. `origin` (`WolfpackOfOne/QuantConnect_Master`) is a separate, divergent repo and should not be the default target. When creating PRs with `gh`, always pass `--repo WolfpackOfOne/Q-agent`. Verify with `git remote -v` and `git branch -vv` before pushing.

## Prerequisites (first-time setup)

After `git clone`, these resources don't exist yet — create them once per machine:

| Resource | Why missing | Create with |
|---|---|---|
| `venv/` | Not checked in | `python3 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install lean` (see `docs/getting-started.md:22-32`) |
| `~/.lean/credentials` | User-specific auth | `lean login` (preferred — `docs/getting-started.md:35-40`, `CREDENTIALS.md:82-85`) |
| `MyProjects/lean.json` | Created on demand | `cd MyProjects && lean init` |
| `<Project>/config.json` | Per-project cloud IDs | `lean project-create` or first `lean cloud push` |
| Docker Desktop running | Required for `lean backtest` (not for cloud) | `open -a "Docker"` on macOS |

One-shot validator: `bash scripts/check-prereqs.sh`.

---

## Project map

```
Q-agent/
├── venv/                    # (created on first setup — see Prerequisites)
├── Lean/                    # LEAN engine repo (reference only, do not edit)
├── AGENTS.md                # Architecture guidelines
├── claude.md                # This file
├── scripts/check-prereqs.sh # Validates venv/lean/docker/creds
└── MyProjects/              # Algorithm projects
    ├── lean.json            # (created by `lean init`, gitignored)
    ├── data/                # Local market data (gitignored at workspace level)
    ├── storage/             # ObjectStore outputs (gitignored)
    ├── shared/              # Reusable signal atoms (TRACKED in this repo)
    │   ├── README.md        # Shared-library doc — read before adding a signal
    │   └── signals/         # Pure Python signal files
    ├── _template/           # Project scaffold
    ├── ElectionIndustryBeta/ # Reference example — bundled data + shared signal
    └── <ProjectName>/       # Individual project (typically its own Git repo)
        ├── main.py          # Algorithm entry point
        ├── config.json      # Cloud/local IDs (DO NOT COMMIT)
        ├── models/          # Algorithm modules
        ├── domain/          # Business logic
        │   └── signals/     # Symlinks → ../../../shared/signals/ (see below)
        ├── data/            # Bundled per-project data (CSV is committable here)
        ├── tools/           # One-off helpers (refresh scripts, etc.)
        ├── docs/            # Documentation
        └── research/        # Jupyter notebooks
```

## Commands & environment

```bash
# Session setup
cd ~/Documents/Q-agent && source venv/bin/activate && cd MyProjects

# Cloud workflow
lean cloud push --project "<Project>" --force
lean cloud backtest "<Project>" --name "Test"
lean cloud pull --project "<Project>"

# Local workflow
lean backtest "<Project>"
lean research "<Project>"
```

Validation: `python -m py_compile main.py models/*.py`

## LEAN API gotchas

These are hard-won lessons. Follow them as imperative rules:

- **Always call `SetWarmUp` in `Initialize`** with the longest lookback the strategy needs. Omitting it means `IsReady` stays `False` and no trades fire until enough history accumulates organically.
- **`DateRules.MonthStart(n)` treats `n` as a Symbol, not a day offset.** Use `DateRules.MonthStart()` for the first trading day, or `DateRules.MonthStart("SPY", 5)` for a day offset.
- **Avoid the `SetAlpha` + `SetPortfolioConstruction` + coarse universe pattern** in teaching/example projects. Use direct `SetHoldings` calls in a scheduled `_rebalance` method instead. The `_template/` scaffold has `models/{alpha,portfolio,execution}.py` set up as framework subclasses (`AlphaModel` etc.) for production use; for teaching, demote them to plain helper classes that `_rebalance` calls directly. See `MyProjects/ElectionIndustryBeta/` for a worked example.
- **Pyright warnings on LEAN PascalCase API are false positives.** `AlgorithmImports` resolves at runtime. Suppress with `# type: ignore` if needed; backtests compile fine.

## Shared signals library

`MyProjects/shared/signals/` is the canonical source for reusable signal atoms (pure Python, no `AlgorithmImports`). Projects consume them via symlinks — `lean cloud push` follows symlinks and uploads the file content, so QC cloud sees a normal file. `shared/` itself is never inside any project directory and is never pushed.

Read `MyProjects/shared/README.md` before adding a new shared signal.

**One-time setup per project** (run from inside the project directory):
```bash
mkdir -p domain/signals
ln -s ../../../shared/signals/my_signal.py domain/signals/my_signal.py
```

The target path is **three `..` deep** because symlink targets resolve relative to the symlink's location (`<Project>/domain/signals/`), not the cwd. Two `..` produces a dangling link.

**Rules:**
- Signal files in `shared/signals/` must be pure Python (no LEAN imports, no QC types).
- Edit `shared/signals/` — never the symlink copy inside a project.
- All projects that need a signal get their own symlink; no project gets signals it doesn't use.
- Verify the link after creation: `ls -la domain/signals/<name>.py` should show `-> ../../../shared/signals/<name>.py`.

**Local backtests need an extra Docker mount.** `lean backtest` mounts only the project directory into the container, so the symlink target (which lives outside the project) dangles. Use the wrapper:

```bash
bash scripts/lean-backtest.sh "<ProjectName>"
```

which appends `--extra-docker-config '{"volumes": {"<workspace>/MyProjects/shared": {"bind": "/shared", "mode": "ro"}}}'` so the relative `../../../shared/...` resolves correctly inside the container. Cloud backtests (`lean cloud push` + `lean cloud backtest`) are unaffected — `lean cloud push` resolves the symlink at upload time.

## Bundled per-project data

Per-project data (small CSVs that ship with the algorithm) lives at `<Project>/data/*.csv` and **is committable** — distinct from the workspace-level `MyProjects/data/` which is gitignored. The pattern is:

```
<Project>/
├── data/
│   └── <name>.csv          # committed, uploaded by lean cloud push, read in Initialize
└── tools/
    └── refresh_<name>.py   # one-off fetcher — NOT called by the algorithm
```

The algorithm reads `<Project>/data/*.csv` from disk in `Initialize` — no runtime HTTP calls. The fetcher in `tools/` is run manually whenever you want a fresher snapshot. Worked example: `ElectionIndustryBeta/{data/trump_prob.csv, tools/refresh_trump_prob.py}`.

**Resolve the path relative to `__file__`, not cwd.** LEAN's runtime working directory differs between local Docker (cwd = `/LeanCLI`) and cloud (cwd varies), so a plain relative path like `pd.read_csv("data/trump_prob.csv")` is not reliable. Use:

```python
import os
here = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(here, "data", "trump_prob.csv"), parse_dates=["date"])
```

For robustness across environments, also fall back to `self.ObjectStore.Read(...)` if the disk read fails; pre-populate via `lean cloud object-store set "<key>" <local-path>`.

**Index alignment when joining bundled data against LEAN bars.** `self.History(...)` returns a multi-index with timezone-aware bar-end timestamps (e.g. `2024-10-15 16:00:00-04:00` for daily US equity). A CSV parsed with `parse_dates=["date"]` from `YYYY-MM-DD` strings produces tz-naive midnight Timestamps. Joining the two with `pd.DataFrame.join(..., how="inner")` silently produces **zero overlapping rows**. Normalise the History index at the boundary:

```python
closes = bars["close"].unstack(level=0)
idx = pd.to_datetime(closes.index)
try:
    idx = idx.tz_localize(None)  # strip tz if present
except (TypeError, AttributeError):
    pass
closes.index = idx.normalize()    # collapse to midnight
```

Then join freely against any calendar-date-indexed CSV. Pure-Python signal atoms in `shared/signals/` stay format-agnostic and don't need to know about timezones.

## Coding conventions

- Never add `Co-Authored-By` tags to commit messages.
- Make the smallest correct change; avoid drive-by refactors.
- Do not add new dependencies without asking first.
- Keep changes localized to the task at hand.
- For new projects, use the `new-strategy-coder` agent (see `.claude/agents/new_strategy_coder.md`).
- Document all ObjectStore keys in `docs/objectstore.md`.

## Troubleshooting

| Error | Fix |
|---|---|
| `lean: command not found` | `source ~/Documents/Q-agent/venv/bin/activate`; if venv missing, follow `docs/getting-started.md:22-32` |
| `lean.json not found` | `cd MyProjects && lean init` (creates it; gitignored) |
| collaboration lock | add `--force` to `lean cloud push` |
| `is not a Lean project` | directory has no `config.json` — use `lean project-create` |
| No data in local backtest | use cloud: `lean cloud backtest "<ProjectName>"` |
| Docker errors | make sure Docker Desktop is running |

## Data sources

- **Local (yfinance)**: Any ticker Yahoo Finance covers — free, no credentials. See `infrastructure/pipelines/yfinance/`. Run `python scripts/run_pipeline.py --tickers AAPL SPY` from that directory.
- **Local (WRDS/CRSP)**: Full 30-stock equity universe + SPY + SGOV daily data (1998-present). See `infrastructure/pipelines/wrds/claude.md`.
- **Local WRDS (additional entitlements)**: Broader access via `--profile <additional>` — adds OptionMetrics European options (full, 2002–2023, daily + tick) and IBES analyst earnings estimates (1980–2026, 35M rows). US options, RavenPack, 13F ownership, and short interest are denied. No extraction pipelines built yet for additional-entitlement sources.
- **Cloud**: Authoritative. Full equity history, options chains, alternative data. Use for final results.
- **New pipeline**: Use the `new-pipeline-coder` agent to add any new data source. It always outputs LEAN-format files.

## ObjectStore

- Write in algorithm: `self.ObjectStore.Save("namespace/file.csv", csv_string)`
- Read in notebook: `qb.ObjectStore.Read("namespace/file.csv")`

## Project Memory

This workspace uses hook-based memory in `.claude/memory/`.

Memory files:
- `.claude/memory/commands.md`
- `.claude/memory/lean-gotchas.md`
- `.claude/memory/data-pipelines.md`
- `.claude/memory/objectstore.md`
- `.claude/memory/decisions.md`
- `.claude/memory/teaching-style.md`

Do not store secrets in memory files.

When you discover a durable command, data source rule, LEAN gotcha, ObjectStore schema note, or decision, prefer updating the appropriate memory file instead of bloating this `claude.md`.

Automatic extraction writes candidates to `.claude/memory/pending.md`. Review that file manually before promoting entries to durable memory.

## Resources

- **First-time setup**: `docs/getting-started.md`
- **Architecture guidelines**: `AGENTS.md`
- **Shared signals library**: `MyProjects/shared/README.md`
- **Worked example project**: `MyProjects/ElectionIndustryBeta/` (bundled data + shared signal + teaching pattern)
- **New project bootstrap**: `.claude/agents/new_strategy_coder.md`
- **New data pipeline**: `.claude/agents/new-pipeline-coder.md`
- **LEAN CLI guide**: `MyProjects/.claude/agents/lean-cli.md`
- **GitHub sync**: `MyProjects/.claude/agents/github-sync.md`
- **References library**: `References/index.md` (books, repos, papers, notes)
- **QuantConnect docs**: https://www.quantconnect.com/docs

## Maintenance protocol

- If you discover a repeated mistake or missing context, propose a small update to this file.
- Prefer moving detailed playbooks into skills rather than growing this file.
- Keep this file under ~150 lines when possible.
- Path-specific rules belong in `.claude/rules/`, not here.
