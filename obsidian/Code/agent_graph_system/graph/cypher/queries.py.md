---
path: "agent_graph_system/graph/cypher/queries.py"
hub: "Agent Graph System"
lines: 105
tags:
  - "code/python"
  - "areas/Agent-Graph-System"
  - "has/cypher"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py"
---
# queries.py

`agent_graph_system/graph/cypher/queries.py` · hub [[Hubs/Areas/Agent Graph System|Agent Graph System]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py)

## Purpose

Named Cypher queries for common GraphRAG retrieval patterns.

## Dependencies

**Imports (workspace):** [[Code/agent_graph_system/graph/backend.py|backend.py]]

**Imported by:** [[Code/agent_graph_system/api/app.py|app.py]], [[Code/agent_graph_system/graph/backend.py|backend.py]], [[Code/agent_graph_system/main.py|main.py]]

## CYPHER queries (8)

### notebooks_using_wrds · L8

**`notebooks_using_wrds()`** — line [8](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L8)

```cypher
MATCH (n:Notebook)-[:USES]->(d:Dataset)
WHERE d.source = 'WRDS'
RETURN n.name AS notebook, n.path AS path, d.name AS dataset, d.status AS data_status
ORDER BY n.name
```

### stale_strategy_dependencies · L19

**`stale_strategy_dependencies()`** — line [19](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L19)

```cypher
MATCH (s:Strategy)-[:USES|DEPENDS_ON]->(d:Dataset)
WHERE d.status = 'stale'
RETURN s.name AS strategy, s.status AS strategy_status, d.name AS stale_dataset, d.last_updated AS last_updated
ORDER BY d.last_updated
```

### backtest_lineage · L30

**`backtest_lineage()`** — line [30](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L30)

```cypher
MATCH (s:Strategy {name: $name})<-[:USED_BY]-(d:Dataset)
OPTIONAL MATCH (s)<-[:GENERATES]-(n:Notebook)-[:GENERATES]->(b:Backtest)
RETURN s.name AS strategy, d.name AS dataset, n.name AS notebook, b.run_id AS backtest_id,
       b.sharpe AS sharpe, b.cagr AS cagr
```

### active_deployments · L42

**`active_deployments()`** — line [42](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L42)

```cypher
MATCH (s:Strategy)-[r:DEPLOYS_TO]->(a:API)
WHERE r.environment IN ['live', 'paper']
RETURN s.name AS strategy, a.name AS broker, r.environment AS env, r.deployed_at AS deployed_at
ORDER BY r.deployed_at DESC
```

### pipeline_health · L53

**`pipeline_health()`** — line [53](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L53)

```cypher
MATCH (p:Pipeline)
OPTIONAL MATCH (p)-[:PRODUCES]->(d:Dataset)
RETURN p.name AS pipeline, p.status AS status, p.last_run AS last_run,
       collect(d.name) AS output_datasets
ORDER BY p.last_run
```

### dataset_dependency_graph · L66

**`dataset_dependency_graph()`** — line [66](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L66)

```cypher
MATCH (e)-[:USES|DEPENDS_ON]->(d:Dataset {name: $name})
RETURN labels(e)[0] AS entity_type, e.name AS entity, e.status AS status
ORDER BY entity_type, e.name
```

### full_strategy_context · L78

**`full_strategy_context()`** — line [78](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L78)

```cypher
MATCH path = (s:Strategy {name: $name})-[*1..2]-(connected)
RETURN DISTINCT
    labels(connected)[0] AS node_type,
    connected.name AS name,
    type(relationships(path)[-1]) AS via_relationship
ORDER BY node_type, name
```

### agent_task_graph · L93

**`agent_task_graph()`** — line [93](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L93)

```cypher
MATCH (a:Agent)-[r:MONITORS]->(target)
RETURN a.name AS agent, a.role AS role, labels(target)[0] AS watching_type,
       target.name AS watching, target.status AS target_status
ORDER BY a.name
```

## Functions

### `notebooks_using_wrds()`

```python
def notebooks_using_wrds() -> list[dict]
```
[line 6](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L6)

### `stale_strategy_dependencies()`

```python
def stale_strategy_dependencies() -> list[dict]
```
[line 17](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L17)

### `backtest_lineage()`

```python
def backtest_lineage(strategy_name: str) -> list[dict]
```
[line 28](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L28)

### `active_deployments()`

```python
def active_deployments() -> list[dict]
```
[line 40](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L40)

### `pipeline_health()`

```python
def pipeline_health() -> list[dict]
```
[line 51](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L51)

### `dataset_dependency_graph()`

```python
def dataset_dependency_graph(dataset_name: str) -> list[dict]
```
[line 63](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L63)

All notebooks and strategies that depend on a given dataset.

### `full_strategy_context()`

```python
def full_strategy_context(strategy_name: str) -> list[dict]
```
[line 75](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L75)

GraphRAG: retrieve everything connected to a strategy within 2 hops.

### `agent_task_graph()`

```python
def agent_task_graph() -> list[dict]
```
[line 90](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L90)

Which agent monitors which pipelines and datasets.

### `create_indexes()`

```python
def create_indexes() -> None
```
[line 102](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/cypher/queries.py#L102)

## Source

> [!example]- agent_graph_system/graph/cypher/queries.py (105 lines)
> ```python
> """Named Cypher queries for common GraphRAG retrieval patterns."""
>
> from agent_graph_system.graph.backend import query
>
>
> def notebooks_using_wrds() -> list[dict]:
>     return query(
>         """
>         MATCH (n:Notebook)-[:USES]->(d:Dataset)
>         WHERE d.source = 'WRDS'
>         RETURN n.name AS notebook, n.path AS path, d.name AS dataset, d.status AS data_status
>         ORDER BY n.name
>         """
>     )
>
>
> def stale_strategy_dependencies() -> list[dict]:
>     return query(
>         """
>         MATCH (s:Strategy)-[:USES|DEPENDS_ON]->(d:Dataset)
>         WHERE d.status = 'stale'
>         RETURN s.name AS strategy, s.status AS strategy_status, d.name AS stale_dataset, d.last_updated AS last_updated
>         ORDER BY d.last_updated
>         """
>     )
>
>
> def backtest_lineage(strategy_name: str) -> list[dict]:
>     return query(
>         """
>         MATCH (s:Strategy {name: $name})<-[:USED_BY]-(d:Dataset)
>         OPTIONAL MATCH (s)<-[:GENERATES]-(n:Notebook)-[:GENERATES]->(b:Backtest)
>         RETURN s.name AS strategy, d.name AS dataset, n.name AS notebook, b.run_id AS backtest_id,
>                b.sharpe AS sharpe, b.cagr AS cagr
>         """,
>         name=strategy_name,
>     )
>
>
> def active_deployments() -> list[dict]:
>     return query(
>         """
>         MATCH (s:Strategy)-[r:DEPLOYS_TO]->(a:API)
>         WHERE r.environment IN ['live', 'paper']
>         RETURN s.name AS strategy, a.name AS broker, r.environment AS env, r.deployed_at AS deployed_at
>         ORDER BY r.deployed_at DESC
>         """
>     )
>
>
> def pipeline_health() -> list[dict]:
>     return query(
>         """
>         MATCH (p:Pipeline)
>         OPTIONAL MATCH (p)-[:PRODUCES]->(d:Dataset)
>         RETURN p.name AS pipeline, p.status AS status, p.last_run AS last_run,
>                collect(d.name) AS output_datasets
>         ORDER BY p.last_run
>         """
>     )
>
>
> def dataset_dependency_graph(dataset_name: str) -> list[dict]:
>     """All notebooks and strategies that depend on a given dataset."""
>     return query(
>         """
>         MATCH (e)-[:USES|DEPENDS_ON]->(d:Dataset {name: $name})
>         RETURN labels(e)[0] AS entity_type, e.name AS entity, e.status AS status
>         ORDER BY entity_type, e.name
>         """,
>         name=dataset_name,
>     )
>
>
> def full_strategy_context(strategy_name: str) -> list[dict]:
>     """GraphRAG: retrieve everything connected to a strategy within 2 hops."""
>     return query(
>         """
>         MATCH path = (s:Strategy {name: $name})-[*1..2]-(connected)
>         RETURN DISTINCT
>             labels(connected)[0] AS node_type,
>             connected.name AS name,
>             type(relationships(path)[-1]) AS via_relationship
>         ORDER BY node_type, name
>         """,
>         name=strategy_name,
>     )
>
>
> def agent_task_graph() -> list[dict]:
>     """Which agent monitors which pipelines and datasets."""
>     return query(
>         """
>         MATCH (a:Agent)-[r:MONITORS]->(target)
>         RETURN a.name AS agent, a.role AS role, labels(target)[0] AS watching_type,
>                target.name AS watching, target.status AS target_status
>         ORDER BY a.name
>         """
>     )
>
>
> def create_indexes() -> None:
>     from agent_graph_system.graph.backend import create_indexes as _ci
>     _ci()
> ```
