---
path: "agent_graph_system/graph/backend.py"
hub: "Agent Graph System"
lines: 45
tags:
  - "code/python"
  - "areas/Agent-Graph-System"
  - "has/cypher"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/backend.py"
---
# backend.py

`agent_graph_system/graph/backend.py` · hub [[Hubs/Areas/Agent Graph System|Agent Graph System]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/backend.py)

## Purpose

Graph backend selector.
Set GRAPH_BACKEND=neo4j to use a live Neo4j server.
Defaults to the local networkx engine (no server required).

## Dependencies

**Imports (workspace):** [[Code/agent_graph_system/graph/cypher/queries.py|queries.py]], [[Code/agent_graph_system/graph/local/engine.py|engine.py]], [[Code/agent_graph_system/graph/neo4j/driver.py|driver.py]], [[Code/agent_graph_system/graph/neo4j/graph_models.py|graph_models.py]]

**Imports (external):** [[Indexes/External packages#logging|logging]], [[Indexes/External packages#os|os]]

**Imported by:** [[Code/agent_graph_system/agents/monitoring_agent.py|monitoring_agent.py]], [[Code/agent_graph_system/agents/orchestration_agent.py|orchestration_agent.py]], [[Code/agent_graph_system/agents/research_agent.py|research_agent.py]], [[Code/agent_graph_system/agents/walkforward_agent.py|walkforward_agent.py]], [[Code/agent_graph_system/api/app.py|app.py]], [[Code/agent_graph_system/graph/cypher/queries.py|queries.py]], [[Code/agent_graph_system/graph/neo4j/graph_models.py|graph_models.py]], [[Code/agent_graph_system/ingestion/papers/graph_writer.py|graph_writer.py]], [[Code/agent_graph_system/ingestion/quantconnect/graph_writer.py|graph_writer.py]], [[Code/agent_graph_system/main.py|main.py]], [[Code/agent_graph_system/ontology/policy.py|policy.py]], [[Code/agent_graph_system/rag/retriever.py|retriever.py]], [[Code/tests/agent_graph_system/test_deployment_gate.py|test_deployment_gate.py]], [[Code/tests/agent_graph_system/test_walkforward_agent.py|test_walkforward_agent.py]], [[Code/tests/agent_graph_system/test_walkforward_agent_phase2.py|test_walkforward_agent_phase2.py]]

## CYPHER queries (2)

### graph_stats · L33

**`graph_stats()`** — line [33](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/backend.py#L33) · assigned to `nodes`

```cypher
MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count ORDER BY count DESC
```

### graph_stats · L34

**`graph_stats()`** — line [34](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/backend.py#L34) · assigned to `rels`

```cypher
MATCH ()-[r]->() RETURN type(r) AS rel, count(*) AS count ORDER BY count DESC
```

## Source

> [!example]- agent_graph_system/graph/backend.py (45 lines)
> ```python
> """
> Graph backend selector.
> Set GRAPH_BACKEND=neo4j to use a live Neo4j server.
> Defaults to the local networkx engine (no server required).
> """
>
> import os
>
> _backend = os.getenv("GRAPH_BACKEND", "local").lower()
>
> if _backend == "neo4j":
>     from agent_graph_system.graph.neo4j.driver import verify_connectivity
>     if not verify_connectivity():
>         import logging
>         logging.getLogger(__name__).warning(
>             "GRAPH_BACKEND=neo4j but Neo4j unreachable — falling back to local engine"
>         )
>         from agent_graph_system.graph.local.engine import (  # noqa: F401
>             merge_node, merge_relationship, query, create_indexes, graph_stats,
>             latest_backtest_for_strategy, latest_walkforward_for_strategy,
>             latest_walkforward_for_backtest,
>         )
>     else:
>         from agent_graph_system.graph.neo4j.graph_models import (  # noqa: F401
>             merge_node, merge_relationship, latest_backtest_for_strategy,
>             latest_walkforward_for_strategy, latest_walkforward_for_backtest,
>         )
>         from agent_graph_system.graph.neo4j.driver import query  # noqa: F401
>         from agent_graph_system.graph.cypher.queries import create_indexes  # noqa: F401
>
>         def graph_stats():
>             from agent_graph_system.graph.neo4j.driver import query as q
>             nodes = q("MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count ORDER BY count DESC")
>             rels = q("MATCH ()-[r]->() RETURN type(r) AS rel, count(*) AS count ORDER BY count DESC")
>             return {
>                 "node_counts": {r["label"]: r["count"] for r in nodes},
>                 "rel_counts": {r["rel"]: r["count"] for r in rels},
>             }
> else:
>     from agent_graph_system.graph.local.engine import (  # noqa: F401
>         merge_node, merge_relationship, query, create_indexes, graph_stats,
>         latest_backtest_for_strategy, latest_walkforward_for_strategy,
>         latest_walkforward_for_backtest,
>     )
> ```
