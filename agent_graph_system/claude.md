# claude.md — agent_graph_system

## Purpose

Knowledge-graph layer over the workspace: ingests repos / QuantConnect projects
into a typed graph, enforces write-time safety rules, tracks provenance on every
fact, and builds per-project context packs for agents.

Full reference: [`README.md`](README.md). This file is the working guide.

## Scope

This subsystem is **separate from the LEAN algorithm workflow**. It has its own
deps (`requirements.txt`) and its own tests (`tests/agent_graph_system/`). Don't
mix its concerns into project `main.py`/`models/` code.

## Core invariant — honesty over enforcement

**Metadata must never imply a safety guarantee the code doesn't provide.**

- A rule is a hard, write-blocking gate **only** when `status: enforced` **and**
  `severity: blocking` (`Rule.is_hard_gate`). Anything else is documentation —
  `validate_rules()` warns if `blocking` is paired with a non-enforced status.
- The `deployment_gate` is **fail-closed**: a missing/failing/below-threshold
  backtest denies a live `DEPLOYS_TO` write. It only gates *live* environments.
- Low-confidence / `learned` facts are surfaced **separately**, never blended
  into authoritative ones.

If you add a "rule", do not wire enforcement unless you also set its status to
`enforced`; otherwise leave it `documented`/`proposed` and say so.

## Working rules

- **Local backend is the source of truth.** `merge_node`/`merge_relationship`
  live in `graph/local/engine.py`; `backend.py` re-exports them. The Neo4j branch
  is a stub without a server — don't assume parity; if you add a write-path
  feature, note the Neo4j gap rather than pretending it works.
- **Stamp provenance on new facts.** Pass `provenance=Provenance.extracted(...)`
  (or `.declared(...)`) to `merge_node`/`merge_relationship`. Set a sub-1.0
  `confidence` for anything heuristic (resolved-from-constant, regex, inferred).
- **Keep parsers pure.** `ingestion/quantconnect/parser.py` does AST + path work
  and returns plain dicts — no graph imports. Graph writes belong in
  `graph_writer.py`.
- **Namespace per-project nodes.** `File`/`ResearchNotebook` are keyed
  `{project}/{rel}` (with `rel_path` for display) so projects don't collide.
- **Re-ingest is merge-only.** Each run stamps a `run_ts` (`last_seen` +
  Project `last_ingest_run`); context packs filter to the current run so stale
  facts drop out. Don't add node deletion without discussing it.

## Validate before committing

```bash
pip install -r requirements-dev.txt        # from repo root
python -m pytest tests/agent_graph_system/ -q
python -m py_compile agent_graph_system/**/*.py
```

Golden fixture for ingestion/context-pack tests: `MyProjects/ElectionIndustryBeta`.

## Quick CLI

```bash
python -m agent_graph_system.main ingest-project MyProjects/ElectionIndustryBeta
python -m agent_graph_system.main context-pack MyProjects/ElectionIndustryBeta --format md
python -m agent_graph_system.main status
```
