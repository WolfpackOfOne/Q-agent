---
path: "agent_graph_system/rag/retriever.py"
hub: "Agent Graph System"
lines: 85
tags:
  - "code/python"
  - "areas/Agent-Graph-System"
  - "has/cypher"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/rag/retriever.py"
---
# retriever.py

`agent_graph_system/rag/retriever.py` · hub [[Hubs/Areas/Agent Graph System|Agent Graph System]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/rag/retriever.py)

## Purpose

GraphRAG retriever: semantic search + graph traversal combined.

## Dependencies

**Imports (workspace):** [[Code/agent_graph_system/embeddings/embedder.py|embedder.py]], [[Code/agent_graph_system/graph/backend.py|backend.py]]

**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#logging|logging]], [[Indexes/External packages#typing|typing]]

**Imported by:** [[Code/agent_graph_system/agents/research_agent.py|research_agent.py]], [[Code/agent_graph_system/api/app.py|app.py]], [[Code/agent_graph_system/main.py|main.py]]

## CYPHER queries (4)

### graphrag_query · L35

**`graphrag_query()`** — line [35](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/rag/retriever.py#L35) · assigned to `rows`

f-string placeholders: `{graph_hops}`, `{name_key}`, `{node_type}`

```cypher
MATCH path = (seed:{node_type} {{{name_key}: $name}})-[*1..{graph_hops}]-(neighbour)
RETURN DISTINCT
    labels(seed)[0]     AS seed_type,
    seed.name           AS seed_name,
    type(relationships(path)[-1]) AS rel,
    labels(neighbour)[0] AS neighbour_type,
    neighbour.name      AS neighbour_name,
    neighbour.status    AS neighbour_status
LIMIT 50
```

### stale_impact_report · L59

**`stale_impact_report()`** — line [59](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/rag/retriever.py#L59) · assigned to `stale`

```cypher
MATCH (d:Dataset) WHERE d.status = 'stale' RETURN d.name AS name, d.source AS source
```

### stale_impact_report · L64

**`stale_impact_report()`** — line [64](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/rag/retriever.py#L64) · assigned to `rows`

```cypher
MATCH (e)-[:USES|DEPENDS_ON|FEEDS]->(d:Dataset {name: $name})
RETURN labels(e)[0] AS type, e.name AS name, e.status AS status
```

### strategy_readiness · L77

**`strategy_readiness()`** — line [77](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/rag/retriever.py#L77) · assigned to `deps`

```cypher
MATCH (s:Strategy {name: $name})-[:USES|DEPENDS_ON]->(d)
RETURN labels(d)[0] AS dep_type, d.name AS dep_name, d.status AS status
```

## Functions

### `graphrag_query()`

```python
def graphrag_query(question: str, n_semantic: int=5, graph_hops: int=2) -> dict[str, Any]
```
[line 14](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/rag/retriever.py#L14)

Two-phase retrieval:
  1. Semantic: find closest nodes by embedding similarity.
  2. Graph: traverse the ontology from those seed nodes to gather context.
Returns a dict with 'semantic_hits' and 'graph_context'.

### `stale_impact_report()`

```python
def stale_impact_report() -> dict[str, Any]
```
[line 57](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/rag/retriever.py#L57)

Identify stale datasets and list every downstream entity they affect.

### `strategy_readiness()`

```python
def strategy_readiness(strategy_name: str) -> dict[str, Any]
```
[line 74](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/rag/retriever.py#L74)

Check if a strategy's full dependency chain is healthy.

## Source

> [!example]- agent_graph_system/rag/retriever.py (85 lines)
> ```python
> """GraphRAG retriever: semantic search + graph traversal combined."""
>
> from __future__ import annotations
>
> import logging
> from typing import Any
>
> from agent_graph_system.embeddings.embedder import search
> from agent_graph_system.graph.backend import query
>
> log = logging.getLogger(__name__)
>
>
> def graphrag_query(question: str, n_semantic: int = 5, graph_hops: int = 2) -> dict[str, Any]:
>     """
>     Two-phase retrieval:
>       1. Semantic: find closest nodes by embedding similarity.
>       2. Graph: traverse the ontology from those seed nodes to gather context.
>     Returns a dict with 'semantic_hits' and 'graph_context'.
>     """
>     semantic_hits = search(question, n_results=n_semantic)
>
>     seed_nodes: list[tuple[str, str]] = []
>     for hit in semantic_hits:
>         meta = hit.get("metadata", {})
>         node_type = meta.get("node_type", "")
>         node_name = meta.get("node_name", "")
>         if node_type and node_name:
>             seed_nodes.append((node_type, node_name))
>
>     graph_context: list[dict] = []
>     for node_type, node_name in seed_nodes:
>         name_key = "ticker" if node_type == "Security" else "run_id" if node_type == "Backtest" else "name"
>         rows = query(
>             f"""
>             MATCH path = (seed:{node_type} {{{name_key}: $name}})-[*1..{graph_hops}]-(neighbour)
>             RETURN DISTINCT
>                 labels(seed)[0]     AS seed_type,
>                 seed.name           AS seed_name,
>                 type(relationships(path)[-1]) AS rel,
>                 labels(neighbour)[0] AS neighbour_type,
>                 neighbour.name      AS neighbour_name,
>                 neighbour.status    AS neighbour_status
>             LIMIT 50
>             """,
>             name=node_name,
>         )
>         graph_context.extend(rows)
>
>     return {
>         "question": question,
>         "semantic_hits": semantic_hits,
>         "graph_context": graph_context,
>     }
>
>
> def stale_impact_report() -> dict[str, Any]:
>     """Identify stale datasets and list every downstream entity they affect."""
>     stale = query("MATCH (d:Dataset) WHERE d.status = 'stale' RETURN d.name AS name, d.source AS source")
>     impact: dict[str, list] = {}
>     for ds in stale:
>         ds_name = ds["name"]
>         rows = query(
>             """
>             MATCH (e)-[:USES|DEPENDS_ON|FEEDS]->(d:Dataset {name: $name})
>             RETURN labels(e)[0] AS type, e.name AS name, e.status AS status
>             """,
>             name=ds_name,
>         )
>         impact[ds_name] = rows
>     return {"stale_datasets": stale, "downstream_impact": impact}
>
>
> def strategy_readiness(strategy_name: str) -> dict[str, Any]:
>     """Check if a strategy's full dependency chain is healthy."""
>     deps = query(
>         """
>         MATCH (s:Strategy {name: $name})-[:USES|DEPENDS_ON]->(d)
>         RETURN labels(d)[0] AS dep_type, d.name AS dep_name, d.status AS status
>         """,
>         name=strategy_name,
>     )
>     is_ready = all(d.get("status") in (None, "fresh", "active") for d in deps)
>     return {"strategy": strategy_name, "dependencies": deps, "ready": is_ready}
> ```
