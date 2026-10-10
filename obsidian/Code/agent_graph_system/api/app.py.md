---
path: "agent_graph_system/api/app.py"
hub: "Agent Graph System"
lines: 119
tags:
  - "code/python"
  - "areas/Agent-Graph-System"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/api/app.py"
---
# app.py

`agent_graph_system/api/app.py` · hub [[Hubs/Areas/Agent Graph System|Agent Graph System]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/api/app.py)

## Purpose

FastAPI application — REST interface to the graph and agents.

## Dependencies

**Imports (workspace):** [[Code/agent_graph_system/agents/coding_agent.py|coding_agent.py]], [[Code/agent_graph_system/agents/monitoring_agent.py|monitoring_agent.py]], [[Code/agent_graph_system/agents/orchestration_agent.py|orchestration_agent.py]], [[Code/agent_graph_system/graph/backend.py|backend.py]], [[Code/agent_graph_system/graph/cypher/queries.py|queries.py]], [[Code/agent_graph_system/rag/retriever.py|retriever.py]]

**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#fastapi|fastapi]], [[Indexes/External packages#logging|logging]], [[Indexes/External packages#os|os]], [[Indexes/External packages#pydantic|pydantic]], [[Indexes/External packages#typing|typing]]

## Classes

### class `RAGRequest`(BaseModel)

[line 79](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/api/app.py#L79)


## Functions

### `health()`

```python
def health() -> dict[str, Any]
```
[line 24](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/api/app.py#L24)

### `notebooks_using_wrds()`

```python
def notebooks_using_wrds() -> list[dict]
```
[line 36](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/api/app.py#L36)

### `stale_strategy_deps()`

```python
def stale_strategy_deps() -> list[dict]
```
[line 41](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/api/app.py#L41)

### `strategy_lineage()`

```python
def strategy_lineage(name: str) -> list[dict]
```
[line 46](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/api/app.py#L46)

### `strategy_context()`

```python
def strategy_context(name: str) -> list[dict]
```
[line 51](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/api/app.py#L51)

### `active_deployments()`

```python
def active_deployments() -> list[dict]
```
[line 56](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/api/app.py#L56)

### `pipeline_health()`

```python
def pipeline_health() -> list[dict]
```
[line 61](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/api/app.py#L61)

### `dataset_dependents()`

```python
def dataset_dependents(name: str) -> list[dict]
```
[line 66](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/api/app.py#L66)

### `agent_task_graph()`

```python
def agent_task_graph() -> list[dict]
```
[line 71](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/api/app.py#L71)

### `rag_query()`

```python
def rag_query(req: RAGRequest) -> dict[str, Any]
```
[line 85](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/api/app.py#L85)

### `rag_stale_impact()`

```python
def rag_stale_impact() -> dict[str, Any]
```
[line 90](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/api/app.py#L90)

### `rag_strategy_readiness()`

```python
def rag_strategy_readiness(name: str) -> dict[str, Any]
```
[line 95](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/api/app.py#L95)

### `trigger_coding_agent()`

```python
def trigger_coding_agent(repo_path: str=Query(...), repo_url: str=Query('')) -> dict[str, Any]
```
[line 104](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/api/app.py#L104)

### `trigger_monitoring_agent()`

```python
def trigger_monitoring_agent() -> dict[str, Any]
```
[line 110](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/api/app.py#L110)

### `trigger_orchestration_agent()`

```python
def trigger_orchestration_agent() -> dict[str, Any]
```
[line 116](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/api/app.py#L116)

## Source

> [!example]- agent_graph_system/api/app.py (119 lines)
> ```python
> """FastAPI application — REST interface to the graph and agents."""
>
> from __future__ import annotations
>
> import logging
> from typing import Any
>
> from fastapi import FastAPI, HTTPException, Query
> from pydantic import BaseModel
>
> from agent_graph_system.graph.cypher import queries as cq
> from agent_graph_system.graph.backend import graph_stats
> from agent_graph_system.rag.retriever import graphrag_query, stale_impact_report, strategy_readiness
>
> log = logging.getLogger(__name__)
> app = FastAPI(title="Agent Graph System", version="0.1.0")
>
>
> # ---------------------------------------------------------------------------
> # Health
> # ---------------------------------------------------------------------------
>
> @app.get("/health")
> def health() -> dict[str, Any]:
>     import os
>     backend = os.getenv("GRAPH_BACKEND", "local")
>     stats = graph_stats()
>     return {"status": "ok", "backend": backend, "graph": stats}
>
>
> # ---------------------------------------------------------------------------
> # Graph queries
> # ---------------------------------------------------------------------------
>
> @app.get("/graph/notebooks/wrds")
> def notebooks_using_wrds() -> list[dict]:
>     return cq.notebooks_using_wrds()
>
>
> @app.get("/graph/strategies/stale-deps")
> def stale_strategy_deps() -> list[dict]:
>     return cq.stale_strategy_dependencies()
>
>
> @app.get("/graph/strategies/{name}/lineage")
> def strategy_lineage(name: str) -> list[dict]:
>     return cq.backtest_lineage(name)
>
>
> @app.get("/graph/strategies/{name}/context")
> def strategy_context(name: str) -> list[dict]:
>     return cq.full_strategy_context(name)
>
>
> @app.get("/graph/deployments")
> def active_deployments() -> list[dict]:
>     return cq.active_deployments()
>
>
> @app.get("/graph/pipelines/health")
> def pipeline_health() -> list[dict]:
>     return cq.pipeline_health()
>
>
> @app.get("/graph/datasets/{name}/dependents")
> def dataset_dependents(name: str) -> list[dict]:
>     return cq.dataset_dependency_graph(name)
>
>
> @app.get("/graph/agents")
> def agent_task_graph() -> list[dict]:
>     return cq.agent_task_graph()
>
>
> # ---------------------------------------------------------------------------
> # GraphRAG
> # ---------------------------------------------------------------------------
>
> class RAGRequest(BaseModel):
>     question: str
>     n_results: int = 5
>
>
> @app.post("/rag/query")
> def rag_query(req: RAGRequest) -> dict[str, Any]:
>     return graphrag_query(req.question, n_semantic=req.n_results)
>
>
> @app.get("/rag/stale-impact")
> def rag_stale_impact() -> dict[str, Any]:
>     return stale_impact_report()
>
>
> @app.get("/rag/strategy-readiness/{name}")
> def rag_strategy_readiness(name: str) -> dict[str, Any]:
>     return strategy_readiness(name)
>
>
> # ---------------------------------------------------------------------------
> # Agent triggers
> # ---------------------------------------------------------------------------
>
> @app.post("/agents/coding/ingest")
> def trigger_coding_agent(repo_path: str = Query(...), repo_url: str = Query("")) -> dict[str, Any]:
>     from agent_graph_system.agents.coding_agent import CodingAgent
>     return CodingAgent().run(repo_path=repo_path, repo_url=repo_url)
>
>
> @app.post("/agents/monitoring/run")
> def trigger_monitoring_agent() -> dict[str, Any]:
>     from agent_graph_system.agents.monitoring_agent import MonitoringAgent
>     return MonitoringAgent().run()
>
>
> @app.post("/agents/orchestration/run")
> def trigger_orchestration_agent() -> dict[str, Any]:
>     from agent_graph_system.agents.orchestration_agent import OrchestrationAgent
>     return OrchestrationAgent().run()
> ```
