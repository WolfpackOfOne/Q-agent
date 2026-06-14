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
- **Re-ingest is merge-only; staleness is a read-time + prune-time concern.**
  Each ingest run stamps a `run_ts` (provenance `last_seen` + `last_ingest_run`
  on the `Project`/`Paper` parent). Read paths must filter to the parent's
  current marker via `ontology.provenance.is_current` — see
  `graph/context_pack.py` and `ingestion/papers/graph_writer.paper_sections`.
  The **only** deletion path is `engine.prune_stale` behind the explicit
  `prune` CLI command (dry-run by default, `--apply` to delete); never call it
  from ingest, and don't add other deletion paths without discussion. Prune is
  local-backend-only (a known Neo4j parity gap).

## Validate before committing

```bash
pip install -r requirements-dev.txt        # from repo root
python -m pytest tests/agent_graph_system/ -q
find agent_graph_system -name "*.py" | xargs python -m py_compile
```

Golden fixture for ingestion/context-pack tests: `MyProjects/ElectionIndustryBeta`.

## Quick CLI

```bash
python -m agent_graph_system.main ingest-project MyProjects/ElectionIndustryBeta
python -m agent_graph_system.main context-pack MyProjects/ElectionIndustryBeta --format md
python -m agent_graph_system.main ingest-paper 2401.12345
python -m agent_graph_system.main prune project ElectionIndustryBeta   # dry-run; add --apply to delete
python -m agent_graph_system.main status
```
