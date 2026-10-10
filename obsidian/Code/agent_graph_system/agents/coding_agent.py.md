---
path: "agent_graph_system/agents/coding_agent.py"
hub: "Agent Graph System"
lines: 29
tags:
  - "code/python"
  - "areas/Agent-Graph-System"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/coding_agent.py"
---
# coding_agent.py

`agent_graph_system/agents/coding_agent.py` · hub [[Hubs/Areas/Agent Graph System|Agent Graph System]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/coding_agent.py)

## Purpose

Coding agent: parses repos and keeps notebook dependency graph fresh.

## Dependencies

**Imports (workspace):** [[Code/agent_graph_system/agents/base_agent.py|base_agent.py]], [[Code/agent_graph_system/ingestion/github/graph_writer.py|graph_writer.py]]

**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#logging|logging]], [[Indexes/External packages#pathlib|pathlib]], [[Indexes/External packages#typing|typing]]

**Imported by:** [[Code/agent_graph_system/api/app.py|app.py]], [[Code/agent_graph_system/main.py|main.py]]

## Classes

### class `CodingAgent`(BaseAgent)

[line 15](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/coding_agent.py#L15)

- `def run(self, repo_path: str | Path='', repo_url: str='', **kwargs) -> Any` — [L19](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/agents/coding_agent.py#L19)

## Source

> [!example]- agent_graph_system/agents/coding_agent.py (29 lines)
> ```python
> """Coding agent: parses repos and keeps notebook dependency graph fresh."""
>
> from __future__ import annotations
>
> import logging
> from pathlib import Path
> from typing import Any
>
> from agent_graph_system.agents.base_agent import BaseAgent
> from agent_graph_system.ingestion.github.graph_writer import ingest_repo
>
> log = logging.getLogger(__name__)
>
>
> class CodingAgent(BaseAgent):
>     name = "CodingAgent"
>     role = "coding"
>
>     def run(self, repo_path: str | Path = "", repo_url: str = "", **kwargs) -> Any:
>         path = Path(repo_path) if repo_path else Path.cwd()
>         log.info("[CodingAgent] scanning repo at %s", path)
>         try:
>             result = ingest_repo(path, repo_url=repo_url)
>             self._mark_idle()
>             return result
>         except Exception as exc:
>             self._mark_error(str(exc))
>             raise
> ```
