# Start Here

Choose the path that fits you best. Each one has a recommended reading order and a first action to take.

---

## I'm a student { #student }

You're learning quantitative finance, systematic trading, or financial technology. You may be comfortable with Python but haven't built a full research workflow before.

**Start with:**

1. [Why Q-agent Exists](why-q-agent.md) — understand what the project is and why it's structured this way
2. [Running Notebooks](notebooks.md) — run a real research notebook in under 10 minutes, no QuantConnect account needed
3. [Architecture](architecture.md) — learn the atomic layer pattern used in every strategy project
4. [Research Recipes](research-recipes.md) — browse research ideas you can build toward

**First action:** Run the Election & Industry Returns notebook. It pulls live data from public APIs and renders charts immediately.

```bash
git clone https://github.com/WolfpackOfOne/Q-agent.git
cd Q-agent
python -m venv infrastructure/marimo/venv
source infrastructure/marimo/venv/bin/activate
pip install -r infrastructure/marimo/requirements.txt
marimo run infrastructure/marimo/notebooks/election_industry_returns.py --port 2719
```

---

## I want to build a strategy { #strategy }

You want to write a systematic trading strategy, backtest it with real data, and iterate on the research.

**Start with:**

1. [Golden Path](golden-path.md) — follow one hypothesis from raw data to a diagnosed backtest end to end
2. [LEAN & QuantConnect Setup](getting-started.md) — install the LEAN CLI and connect your QuantConnect account
3. [Architecture](architecture.md) — understand the atomic layer pattern before writing code
4. [Data Pipelines Overview](pipelines/index.md) — know what local data is available
5. [Agent Workflows](agent-workflows.md) — use Claude Code to accelerate strategy development safely

**First action:** Create a project using the `_template` directory and run your first cloud backtest.

```bash
source ~/Documents/Q-agent/venv/bin/activate
cd ~/Documents/Q-agent/MyProjects
cp -r _template MyFirstStrategy
lean cloud push --project "MyFirstStrategy" --force
lean cloud backtest "MyFirstStrategy" --name "baseline"
```

---

## I want to add a pipeline { #pipeline }

You have a data source — an API, a CSV feed, a database — and want to make it available for local notebooks and LEAN backtests.

**Start with:**

1. [Data Pipelines Overview](pipelines/index.md) — understand the existing pipeline conventions and output format
2. Look at an existing pipeline for reference: `infrastructure/pipelines/crypto/` is the cleanest example
3. The `new-pipeline-coder` agent in `.claude/agents/` will scaffold the full pipeline structure for you

**First action:** Ask Claude Code to scaffold a new pipeline.

```
claude "Create a new pipeline for [your data source] following the pattern
in infrastructure/pipelines/crypto/"
```

**Output format:** All pipelines write LEAN-compatible CSV files to `infrastructure/pipelines/<name>/data/`. See [Pipelines Overview](pipelines/index.md) for the schema.

---

## I want to use agents { #agents }

You want to use Claude Code or other AI agents to work on strategies, pipelines, and notebooks — safely and consistently.

**Start with:**

1. [Agent Workflows](agent-workflows.md) — see what an AI-assisted session looks like in practice
2. Read `AGENTS.md` in the repo root — architecture guidelines that keep agent output safe
3. Read `claude.md` — workspace-specific rules, gotchas, and memory system documentation

**Key patterns:**
- Always activate the venv before running commands: `source ~/Documents/Q-agent/venv/bin/activate`
- Use `lean cloud push --force` after agent edits to validate in the cloud
- Agent memory lives in `.claude/memory/` — durable learnings persist across sessions

**First action:** Open the project in Claude Code and ask it to explain the architecture.

```bash
cd ~/Documents/Q-agent
claude "Walk me through the architecture of this workspace"
```

---

## I want to contribute { #contribute }

You want to improve the project — add a pipeline, write a notebook, improve documentation, or fix a bug.

**Start with:**

1. [Contributing](contributing.md) — contribution workflow and standards
2. [Project Map](project-map.md) — understand where everything lives
3. Look at open issues on GitHub for ideas

**Good first contributions:**
- Add a research recipe (see [Research Recipes](research-recipes.md))
- Write a pipeline page for a data source that isn't documented yet
- Record a real terminal walkthrough to replace one of the synthetic recordings
- Add a notebook that demonstrates a research idea from [Research Examples](research-examples.md)

**First action:** Fork the repo, create a feature branch, and open a PR.

```bash
git checkout -b feature/my-contribution
# make your changes
git push origin feature/my-contribution
# open a PR on GitHub
```
