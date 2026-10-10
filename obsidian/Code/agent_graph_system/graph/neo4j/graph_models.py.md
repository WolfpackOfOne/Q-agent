---
path: "agent_graph_system/graph/neo4j/graph_models.py"
hub: "Agent Graph System"
lines: 243
tags:
  - "code/python"
  - "areas/Agent-Graph-System"
  - "has/cypher"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py"
---
# graph_models.py

`agent_graph_system/graph/neo4j/graph_models.py` · hub [[Hubs/Areas/Agent Graph System|Agent Graph System]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py)

## Purpose

CRUD helpers for all ontology node and relationship types.

## Dependencies

**Imports (workspace):** [[Code/agent_graph_system/graph/backend.py|backend.py]], [[Code/agent_graph_system/graph/neo4j/driver.py|driver.py]], [[Code/agent_graph_system/ontology/policy.py|policy.py]]

**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#datetime|datetime]], [[Indexes/External packages#logging|logging]], [[Indexes/External packages#typing|typing]]

**Imported by:** [[Code/agent_graph_system/agents/base_agent.py|base_agent.py]], [[Code/agent_graph_system/agents/monitoring_agent.py|monitoring_agent.py]], [[Code/agent_graph_system/agents/research_agent.py|research_agent.py]], [[Code/agent_graph_system/agents/walkforward_agent.py|walkforward_agent.py]], [[Code/agent_graph_system/graph/backend.py|backend.py]], [[Code/agent_graph_system/ingestion/github/graph_writer.py|graph_writer.py]], [[Code/agent_graph_system/main.py|main.py]], [[Code/tests/agent_graph_system/test_context_pack.py|test_context_pack.py]], [[Code/tests/agent_graph_system/test_deployment_gate.py|test_deployment_gate.py]], [[Code/tests/agent_graph_system/test_latest_backtest.py|test_latest_backtest.py]], [[Code/tests/agent_graph_system/test_walkforward_agent.py|test_walkforward_agent.py]], [[Code/tests/agent_graph_system/test_walkforward_agent_phase2.py|test_walkforward_agent_phase2.py]]

## CYPHER queries (3)

### latest_backtest_for_strategy · L159

**`latest_backtest_for_strategy()`** — line [159](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L159) · assigned to `cypher`

```cypher
MATCH (b:Backtest)
WHERE (
    EXISTS { MATCH (:Strategy {name: $name})-[:HAS_BACKTEST]->(b) }
    OR b.strategy = $name
)
AND coalesce(b.status, 'completed') NOT IN ['failed', 'running']
RETURN b AS bt
ORDER BY coalesce(b.completed_at, b.run_date, b.created_at, b.updated_at, '') DESC
LIMIT 1
```

### latest_walkforward_for_strategy · L183

**`latest_walkforward_for_strategy()`** — line [183](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L183) · assigned to `cypher`

```cypher
MATCH (w:WalkforwardRun)
WHERE (
    EXISTS { MATCH (:Strategy {name: $name})-[:HAS_WALKFORWARD]->(w) }
    OR w.strategy = $name
)
AND coalesce(w.status, 'completed') = 'completed'
RETURN w AS wf
ORDER BY coalesce(w.created_at, w.updated_at, '') DESC
LIMIT 1
```

### latest_walkforward_for_backtest · L208

**`latest_walkforward_for_backtest()`** — line [208](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L208) · assigned to `cypher`

```cypher
MATCH (w:WalkforwardRun)-[:VALIDATES]->(b:Backtest {run_id: $bt})
WHERE coalesce(w.status, 'completed') = 'completed'
RETURN w AS wf
ORDER BY coalesce(w.created_at, w.updated_at, '') DESC
LIMIT 1
```

## Functions

### `upsert_dataset()`

```python
def upsert_dataset(name: str, source: str, status: str='fresh', **props) -> None
```
[line 18](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L18)

### `upsert_notebook()`

```python
def upsert_notebook(name: str, path: str, notebook_type: str='research', **props) -> None
```
[line 22](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L22)

### `upsert_strategy()`

```python
def upsert_strategy(name: str, strategy_type: str, status: str='backtesting', **props) -> None
```
[line 26](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L26)

### `upsert_backtest()`

```python
def upsert_backtest(run_id: str, name: str, sharpe: float, drawdown: float, cagr: float, **props) -> None
```
[line 30](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L30)

### `upsert_walkforward_run()`

```python
def upsert_walkforward_run(run_id: str, strategy: str, **props) -> None
```
[line 40](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L40)

A walk-forward validation run for ``strategy``.

``status`` is one of ``completed`` | ``failed`` | ``insufficient_data``.
Pass ``provenance=`` (e.g. ``Provenance.declared(...)``) for computed runs.

### `upsert_walkforward_window()`

```python
def upsert_walkforward_window(window_id: str, run_id: str, **props) -> None
```
[line 54](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L54)

One train/test window belonging to a :func:`upsert_walkforward_run`.

### `upsert_repository()`

```python
def upsert_repository(name: str, url: str, branch: str='main', **props) -> None
```
[line 64](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L64)

### `upsert_pipeline()`

```python
def upsert_pipeline(name: str, pipeline_type: str, status: str='idle', **props) -> None
```
[line 68](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L68)

### `upsert_agent()`

```python
def upsert_agent(name: str, role: str, status: str='active', **props) -> None
```
[line 72](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L72)

### `upsert_security()`

```python
def upsert_security(ticker: str, name: str, asset_type: str='equity', sector: str='', **props) -> None
```
[line 76](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L76)

### `notebook_uses_dataset()`

```python
def notebook_uses_dataset(notebook: str, dataset: str, **props) -> None
```
[line 84](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L84)

### `strategy_uses_dataset()`

```python
def strategy_uses_dataset(strategy: str, dataset: str, **props) -> None
```
[line 88](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L88)

### `notebook_generates_backtest()`

```python
def notebook_generates_backtest(notebook: str, run_id: str, **props) -> None
```
[line 92](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L92)

### `strategy_has_backtest()`

```python
def strategy_has_backtest(strategy: str, run_id: str, **props) -> None
```
[line 96](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L96)

Link a Strategy to one of its Backtest runs (lineage for the gate).

### `strategy_has_walkforward()`

```python
def strategy_has_walkforward(strategy: str, run_id: str, **props) -> None
```
[line 101](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L101)

Link a Strategy to one of its WalkforwardRun results.

### `walkforward_run_has_window()`

```python
def walkforward_run_has_window(run_id: str, window_id: str, **props) -> None
```
[line 106](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L106)

Link a WalkforwardRun to one of its WalkforwardWindow nodes.

### `walkforward_validates_backtest()`

```python
def walkforward_validates_backtest(run_id: str, backtest_run_id: str, **props) -> None
```
[line 111](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L111)

A WalkforwardRun VALIDATES the Backtest it was computed against.

Lets the live deployment gate ask not just "is there a backtest?" but
"is there a walk-forward run validating it?".

### `strategy_deploys_to()`

```python
def strategy_deploys_to(strategy: str, api_name: str, environment: str='paper', *, enforce_gate: bool=True, **props) -> None
```
[line 120](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L120)

Write a Strategy -[DEPLOYS_TO]-> API edge.

For live environments this is gated by the enforced ``deployment_gate``
rule and is fail-closed: if the gate denies the write a
:class:`~agent_graph_system.ontology.policy.PolicyViolation` is raised and
no edge is written. Pass ``enforce_gate=False`` only for trusted backfills.

### `latest_backtest_for_strategy()`

```python
def latest_backtest_for_strategy(strategy: str) -> dict[str, Any] | None
```
[line 151](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L151)

Neo4j implementation of the latest-valid-backtest lookup.

Mirrors the local engine: linked via ``HAS_BACKTEST`` or a ``strategy``
property, excluding failed/running runs, ordered by recency.

### `latest_walkforward_for_strategy()`

```python
def latest_walkforward_for_strategy(strategy: str) -> dict[str, Any] | None
```
[line 175](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L175)

Neo4j implementation of the latest-completed-walkforward lookup.

Mirrors :func:`latest_backtest_for_strategy`: linked via ``HAS_WALKFORWARD``
or a ``strategy`` property, restricted to completed runs, newest first.

### `latest_walkforward_for_backtest()`

```python
def latest_walkforward_for_backtest(backtest_run_id: str) -> dict[str, Any] | None
```
[line 199](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L199)

Latest completed walk-forward run that VALIDATES a specific backtest.

Mirrors the local engine: only runs linked by ``VALIDATES`` to this exact
backtest qualify, so the gate cannot accept a run that validated an older
backtest. ``validates_backtest`` is returned alongside the run properties.

### `repository_contains_notebook()`

```python
def repository_contains_notebook(repo: str, notebook: str, **props) -> None
```
[line 224](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L224)

### `pipeline_produces_dataset()`

```python
def pipeline_produces_dataset(pipeline: str, dataset: str, **props) -> None
```
[line 228](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L228)

### `dataset_feeds_strategy()`

```python
def dataset_feeds_strategy(dataset: str, strategy: str, valid_from: str='', valid_to: str='', **props) -> None
```
[line 232](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L232)

### `agent_monitors()`

```python
def agent_monitors(agent: str, target_label: str, target_name_key: str, target_name: str, **props) -> None
```
[line 241](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/graph_models.py#L241)

## Source

> [!example]- agent_graph_system/graph/neo4j/graph_models.py (243 lines)
> ```python
> """CRUD helpers for all ontology node and relationship types."""
>
> from __future__ import annotations
>
> import logging
> from datetime import datetime
> from typing import Any
>
> from agent_graph_system.graph.backend import merge_node, merge_relationship, query  # noqa: F401
>
> log = logging.getLogger(__name__)
>
>
> # ---------------------------------------------------------------------------
> # Entity-specific helpers
> # ---------------------------------------------------------------------------
>
> def upsert_dataset(name: str, source: str, status: str = "fresh", **props) -> None:
>     merge_node("Dataset", "name", name, {"source": source, "status": status, **props})
>
>
> def upsert_notebook(name: str, path: str, notebook_type: str = "research", **props) -> None:
>     merge_node("Notebook", "name", name, {"path": path, "notebook_type": notebook_type, **props})
>
>
> def upsert_strategy(name: str, strategy_type: str, status: str = "backtesting", **props) -> None:
>     merge_node("Strategy", "name", name, {"strategy_type": strategy_type, "status": status, **props})
>
>
> def upsert_backtest(run_id: str, name: str, sharpe: float, drawdown: float, cagr: float, **props) -> None:
>     merge_node("Backtest", "run_id", run_id, {
>         "name": name,
>         "sharpe": sharpe,
>         "max_drawdown": drawdown,
>         "cagr": cagr,
>         **props,
>     })
>
>
> def upsert_walkforward_run(run_id: str, strategy: str, **props) -> None:
>     """A walk-forward validation run for ``strategy``.
>
>     ``status`` is one of ``completed`` | ``failed`` | ``insufficient_data``.
>     Pass ``provenance=`` (e.g. ``Provenance.declared(...)``) for computed runs.
>     """
>     provenance = props.pop("provenance", None)
>     merge_node(
>         "WalkforwardRun", "run_id", run_id,
>         {"strategy": strategy, **props},
>         provenance=provenance,
>     )
>
>
> def upsert_walkforward_window(window_id: str, run_id: str, **props) -> None:
>     """One train/test window belonging to a :func:`upsert_walkforward_run`."""
>     provenance = props.pop("provenance", None)
>     merge_node(
>         "WalkforwardWindow", "window_id", window_id,
>         {"run_id": run_id, **props},
>         provenance=provenance,
>     )
>
>
> def upsert_repository(name: str, url: str, branch: str = "main", **props) -> None:
>     merge_node("Repository", "name", name, {"url": url, "branch": branch, **props})
>
>
> def upsert_pipeline(name: str, pipeline_type: str, status: str = "idle", **props) -> None:
>     merge_node("Pipeline", "name", name, {"pipeline_type": pipeline_type, "status": status, **props})
>
>
> def upsert_agent(name: str, role: str, status: str = "active", **props) -> None:
>     merge_node("Agent", "name", name, {"role": role, "status": status, **props})
>
>
> def upsert_security(ticker: str, name: str, asset_type: str = "equity", sector: str = "", **props) -> None:
>     merge_node("Security", "ticker", ticker, {"name": name, "asset_type": asset_type, "sector": sector, **props})
>
>
> # ---------------------------------------------------------------------------
> # Relationship helpers
> # ---------------------------------------------------------------------------
>
> def notebook_uses_dataset(notebook: str, dataset: str, **props) -> None:
>     merge_relationship("Notebook", "name", notebook, "USES", "Dataset", "name", dataset, props)
>
>
> def strategy_uses_dataset(strategy: str, dataset: str, **props) -> None:
>     merge_relationship("Strategy", "name", strategy, "USES", "Dataset", "name", dataset, props)
>
>
> def notebook_generates_backtest(notebook: str, run_id: str, **props) -> None:
>     merge_relationship("Notebook", "name", notebook, "GENERATES", "Backtest", "run_id", run_id, props)
>
>
> def strategy_has_backtest(strategy: str, run_id: str, **props) -> None:
>     """Link a Strategy to one of its Backtest runs (lineage for the gate)."""
>     merge_relationship("Strategy", "name", strategy, "HAS_BACKTEST", "Backtest", "run_id", run_id, props)
>
>
> def strategy_has_walkforward(strategy: str, run_id: str, **props) -> None:
>     """Link a Strategy to one of its WalkforwardRun results."""
>     merge_relationship("Strategy", "name", strategy, "HAS_WALKFORWARD", "WalkforwardRun", "run_id", run_id, props)
>
>
> def walkforward_run_has_window(run_id: str, window_id: str, **props) -> None:
>     """Link a WalkforwardRun to one of its WalkforwardWindow nodes."""
>     merge_relationship("WalkforwardRun", "run_id", run_id, "HAS_WINDOW", "WalkforwardWindow", "window_id", window_id, props)
>
>
> def walkforward_validates_backtest(run_id: str, backtest_run_id: str, **props) -> None:
>     """A WalkforwardRun VALIDATES the Backtest it was computed against.
>
>     Lets the live deployment gate ask not just "is there a backtest?" but
>     "is there a walk-forward run validating it?".
>     """
>     merge_relationship("WalkforwardRun", "run_id", run_id, "VALIDATES", "Backtest", "run_id", backtest_run_id, props)
>
>
> def strategy_deploys_to(
>     strategy: str,
>     api_name: str,
>     environment: str = "paper",
>     *,
>     enforce_gate: bool = True,
>     **props,
> ) -> None:
>     """Write a Strategy -[DEPLOYS_TO]-> API edge.
>
>     For live environments this is gated by the enforced ``deployment_gate``
>     rule and is fail-closed: if the gate denies the write a
>     :class:`~agent_graph_system.ontology.policy.PolicyViolation` is raised and
>     no edge is written. Pass ``enforce_gate=False`` only for trusted backfills.
>     """
>     if enforce_gate:
>         from agent_graph_system.ontology.policy import PolicyViolation, check_deployment_gate
>
>         decision = check_deployment_gate(strategy, environment)
>         if not decision.allowed:
>             log.warning(
>                 "Blocked DEPLOYS_TO %s->%s (%s): %s",
>                 strategy, api_name, decision.code, decision.message,
>             )
>             raise PolicyViolation(decision)
>
>     merge_relationship("Strategy", "name", strategy, "DEPLOYS_TO", "API", "name", api_name, {
>         "environment": environment, **props
>     })
>
>
> def latest_backtest_for_strategy(strategy: str) -> dict[str, Any] | None:
>     """Neo4j implementation of the latest-valid-backtest lookup.
>
>     Mirrors the local engine: linked via ``HAS_BACKTEST`` or a ``strategy``
>     property, excluding failed/running runs, ordered by recency.
>     """
>     from agent_graph_system.graph.neo4j.driver import session
>
>     cypher = """
>         MATCH (b:Backtest)
>         WHERE (
>             EXISTS { MATCH (:Strategy {name: $name})-[:HAS_BACKTEST]->(b) }
>             OR b.strategy = $name
>         )
>         AND coalesce(b.status, 'completed') NOT IN ['failed', 'running']
>         RETURN b AS bt
>         ORDER BY coalesce(b.completed_at, b.run_date, b.created_at, b.updated_at, '') DESC
>         LIMIT 1
>     """
>     with session() as s:
>         record = s.run(cypher, name=strategy).single()
>         return dict(record["bt"]) if record else None
>
>
> def latest_walkforward_for_strategy(strategy: str) -> dict[str, Any] | None:
>     """Neo4j implementation of the latest-completed-walkforward lookup.
>
>     Mirrors :func:`latest_backtest_for_strategy`: linked via ``HAS_WALKFORWARD``
>     or a ``strategy`` property, restricted to completed runs, newest first.
>     """
>     from agent_graph_system.graph.neo4j.driver import session
>
>     cypher = """
>         MATCH (w:WalkforwardRun)
>         WHERE (
>             EXISTS { MATCH (:Strategy {name: $name})-[:HAS_WALKFORWARD]->(w) }
>             OR w.strategy = $name
>         )
>         AND coalesce(w.status, 'completed') = 'completed'
>         RETURN w AS wf
>         ORDER BY coalesce(w.created_at, w.updated_at, '') DESC
>         LIMIT 1
>     """
>     with session() as s:
>         record = s.run(cypher, name=strategy).single()
>         return dict(record["wf"]) if record else None
>
>
> def latest_walkforward_for_backtest(backtest_run_id: str) -> dict[str, Any] | None:
>     """Latest completed walk-forward run that VALIDATES a specific backtest.
>
>     Mirrors the local engine: only runs linked by ``VALIDATES`` to this exact
>     backtest qualify, so the gate cannot accept a run that validated an older
>     backtest. ``validates_backtest`` is returned alongside the run properties.
>     """
>     from agent_graph_system.graph.neo4j.driver import session
>
>     cypher = """
>         MATCH (w:WalkforwardRun)-[:VALIDATES]->(b:Backtest {run_id: $bt})
>         WHERE coalesce(w.status, 'completed') = 'completed'
>         RETURN w AS wf
>         ORDER BY coalesce(w.created_at, w.updated_at, '') DESC
>         LIMIT 1
>     """
>     with session() as s:
>         record = s.run(cypher, bt=backtest_run_id).single()
>         if not record:
>             return None
>         wf = dict(record["wf"])
>         wf["validates_backtest"] = backtest_run_id
>         return wf
>
>
> def repository_contains_notebook(repo: str, notebook: str, **props) -> None:
>     merge_relationship("Repository", "name", repo, "CONTAINS", "Notebook", "name", notebook, props)
>
>
> def pipeline_produces_dataset(pipeline: str, dataset: str, **props) -> None:
>     merge_relationship("Pipeline", "name", pipeline, "PRODUCES", "Dataset", "name", dataset, props)
>
>
> def dataset_feeds_strategy(dataset: str, strategy: str, valid_from: str = "", valid_to: str = "", **props) -> None:
>     extra: dict[str, Any] = {**props}
>     if valid_from:
>         extra["valid_from"] = valid_from
>     if valid_to:
>         extra["valid_to"] = valid_to
>     merge_relationship("Dataset", "name", dataset, "FEEDS", "Strategy", "name", strategy, extra)
>
>
> def agent_monitors(agent: str, target_label: str, target_name_key: str, target_name: str, **props) -> None:
>     merge_relationship("Agent", "name", agent, "MONITORS", target_label, target_name_key, target_name, props)
> ```
