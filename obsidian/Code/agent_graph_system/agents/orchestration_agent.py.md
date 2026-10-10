---
path: "agent_graph_system/agents/orchestration_agent.py"
hub: "Agent Graph System"
lines: 59
tags:
  - "code/python"
  - "areas/Agent-Graph-System"
  - "has/cypher"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/orchestration_agent.py"
---
# orchestration_agent.py

`agent_graph_system/agents/orchestration_agent.py` · hub [[Hubs/Areas/Agent Graph System|Agent Graph System]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/orchestration_agent.py)

## Purpose

Orchestration agent: coordinates other agents in response to graph events.

## Dependencies

**Imports (workspace):** [[Code/agent_graph_system/agents/base_agent.py|base_agent.py]], [[Code/agent_graph_system/graph/backend.py|backend.py]]

**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#logging|logging]], [[Indexes/External packages#typing|typing]]

**Imported by:** [[Code/agent_graph_system/api/app.py|app.py]], [[Code/tests/agent_graph_system/test_walkforward_agent_phase2.py|test_walkforward_agent_phase2.py]]

## CYPHER queries (3)

### OrchestrationAgent.run · L30

**`OrchestrationAgent.run()`** — line [30](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/orchestration_agent.py#L30) · assigned to `stale`

```cypher
MATCH (d:Dataset) WHERE d.status = 'stale' RETURN d.name AS name, d.source AS source
```

### OrchestrationAgent.run · L37

**`OrchestrationAgent.run()`** — line [37](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/orchestration_agent.py#L37) · assigned to `failed_pipelines`

```cypher
MATCH (p:Pipeline) WHERE p.status = 'failed' RETURN p.name AS name
```

### OrchestrationAgent.run · L47

**`OrchestrationAgent.run()`** — line [47](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/orchestration_agent.py#L47) · assigned to `strategies`

```cypher
MATCH (s:Strategy) RETURN s.name AS name, s.status AS status
```

## Classes

### class `OrchestrationAgent`(BaseAgent)

[line 14](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/orchestration_agent.py#L14)

- `def run(self, **kwargs) -> Any` — [L18](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/orchestration_agent.py#L18)  
  Inspect the graph for issues and dispatch remediation tasks. Current rules:   - Stale datasets → log for re-ingestion   - Failed pipelines → log for restart   - Strategies needing walk-forward → queue a walk-forward run

## Source

> [!example]- agent_graph_system/agents/orchestration_agent.py (59 lines)
> ```python
> """Orchestration agent: coordinates other agents in response to graph events."""
>
> from __future__ import annotations
>
> import logging
> from typing import Any
>
> from agent_graph_system.agents.base_agent import BaseAgent
> from agent_graph_system.graph.backend import query
>
> log = logging.getLogger(__name__)
>
>
> class OrchestrationAgent(BaseAgent):
>     name = "OrchestrationAgent"
>     role = "orchestration"
>
>     def run(self, **kwargs) -> Any:
>         """
>         Inspect the graph for issues and dispatch remediation tasks.
>         Current rules:
>           - Stale datasets → log for re-ingestion
>           - Failed pipelines → log for restart
>           - Strategies needing walk-forward → queue a walk-forward run
>         """
>         actions: list[dict] = []
>         log.info("[OrchestrationAgent] scanning graph for remediation tasks")
>         try:
>             stale = query(
>                 "MATCH (d:Dataset) WHERE d.status = 'stale' RETURN d.name AS name, d.source AS source"
>             )
>             for ds in stale:
>                 actions.append({"action": "reingest_dataset", "target": ds["name"], "source": ds["source"]})
>                 log.info("[OrchestrationAgent] queuing reingest for: %s", ds["name"])
>
>             failed_pipelines = query(
>                 "MATCH (p:Pipeline) WHERE p.status = 'failed' RETURN p.name AS name"
>             )
>             for p in failed_pipelines:
>                 actions.append({"action": "restart_pipeline", "target": p["name"]})
>                 log.info("[OrchestrationAgent] queuing restart for pipeline: %s", p["name"])
>
>             # Filter status in Python: a query string containing the literal
>             # 'needs_walkforward' is routed to the local backend's WalkforwardRun
>             # handler (its guard matches the "WALKFORWARD" substring), not the
>             # generic Strategy scan.
>             strategies = query("MATCH (s:Strategy) RETURN s.name AS name, s.status AS status")
>             for s in strategies:
>                 if s.get("status") != "needs_walkforward" or not s.get("name"):
>                     continue
>                 actions.append({"action": "run_walkforward", "target": s["name"]})
>                 log.info("[OrchestrationAgent] queuing walk-forward for: %s", s["name"])
>
>             self._mark_idle()
>         except Exception as exc:
>             self._mark_error(str(exc))
>             raise
>         return {"actions": actions}
> ```
