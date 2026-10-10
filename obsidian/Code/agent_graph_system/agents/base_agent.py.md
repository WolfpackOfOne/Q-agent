---
path: "agent_graph_system/agents/base_agent.py"
hub: "Agent Graph System"
lines: 36
tags:
  - "code/python"
  - "areas/Agent-Graph-System"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/base_agent.py"
---
# base_agent.py

`agent_graph_system/agents/base_agent.py` · hub [[Hubs/Areas/Agent Graph System|Agent Graph System]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/base_agent.py)

## Purpose

Abstract base class for all graph agents.

## Dependencies

**Imports (workspace):** [[Code/agent_graph_system/graph/neo4j/graph_models.py|graph_models.py]]

**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#abc|abc]], [[Indexes/External packages#datetime|datetime]], [[Indexes/External packages#logging|logging]], [[Indexes/External packages#typing|typing]]

**Imported by:** [[Code/agent_graph_system/agents/coding_agent.py|coding_agent.py]], [[Code/agent_graph_system/agents/monitoring_agent.py|monitoring_agent.py]], [[Code/agent_graph_system/agents/orchestration_agent.py|orchestration_agent.py]], [[Code/agent_graph_system/agents/research_agent.py|research_agent.py]], [[Code/agent_graph_system/agents/walkforward_agent.py|walkforward_agent.py]]

## Classes

### class `BaseAgent`(abc.ABC)

[line 15](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/base_agent.py#L15)

- `def __init__(self) -> None` — [L19](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/base_agent.py#L19)
- `def run(self, **kwargs) -> Any` — [L25](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/base_agent.py#L25)
- `def _mark_idle(self) -> None` — [L28](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/base_agent.py#L28)
- `def _mark_error(self, msg: str) -> None` — [L32](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/base_agent.py#L32)

## Source

> [!example]- agent_graph_system/agents/base_agent.py (36 lines)
> ```python
> """Abstract base class for all graph agents."""
>
> from __future__ import annotations
>
> import abc
> import logging
> from datetime import datetime
> from typing import Any
>
> from agent_graph_system.graph.neo4j import graph_models as gm
>
> log = logging.getLogger(__name__)
>
>
> class BaseAgent(abc.ABC):
>     name: str
>     role: str
>
>     def __init__(self) -> None:
>         gm.upsert_agent(self.name, role=self.role, status="active",
>                         last_seen=datetime.utcnow().isoformat())
>         log.info("[%s] registered in graph", self.name)
>
>     @abc.abstractmethod
>     def run(self, **kwargs) -> Any:
>         ...
>
>     def _mark_idle(self) -> None:
>         gm.merge_node("Agent", "name", self.name,
>                       {"status": "idle", "last_seen": datetime.utcnow().isoformat()})
>
>     def _mark_error(self, msg: str) -> None:
>         gm.merge_node("Agent", "name", self.name,
>                       {"status": "error", "last_error": msg, "last_seen": datetime.utcnow().isoformat()})
>         log.error("[%s] error: %s", self.name, msg)
> ```
