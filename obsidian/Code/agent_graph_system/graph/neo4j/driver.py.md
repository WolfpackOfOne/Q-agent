---
path: "agent_graph_system/graph/neo4j/driver.py"
hub: "Agent Graph System"
lines: 49
tags:
  - "code/python"
  - "areas/Agent-Graph-System"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/driver.py"
---
# driver.py

`agent_graph_system/graph/neo4j/driver.py` · hub [[Hubs/Areas/Agent Graph System|Agent Graph System]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/driver.py)

## Purpose

Neo4j driver singleton and session context manager.

## Dependencies

**Imports (workspace):** [[Code/agent_graph_system/config.py|config.py]]

**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#contextlib|contextlib]], [[Indexes/External packages#logging|logging]], [[Indexes/External packages#neo4j|neo4j]], [[Indexes/External packages#typing|typing]]

**Imported by:** [[Code/agent_graph_system/graph/backend.py|backend.py]], [[Code/agent_graph_system/graph/neo4j/graph_models.py|graph_models.py]]

## Functions

### `get_driver()`

```python
def get_driver() -> Driver
```
[line 18](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/driver.py#L18)

### `close_driver()`

```python
def close_driver() -> None
```
[line 29](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/driver.py#L29)

### `session()`

```python
def session() -> Generator[Session, None, None]
```
[line 37](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/driver.py#L37)

### `verify_connectivity()`

```python
def verify_connectivity() -> bool
```
[line 42](https://github.com/WolfpackOfOne/Q-agent/blob/main/agent_graph_system/graph/neo4j/driver.py#L42)

## Source

> [!example]- agent_graph_system/graph/neo4j/driver.py (49 lines)
> ```python
> """Neo4j driver singleton and session context manager."""
>
> from __future__ import annotations
>
> import logging
> from contextlib import contextmanager
> from typing import Generator
>
> from neo4j import Driver, GraphDatabase, Session
>
> from agent_graph_system.config import cfg
>
> log = logging.getLogger(__name__)
>
> _driver: Driver | None = None
>
>
> def get_driver() -> Driver:
>     global _driver
>     if _driver is None:
>         _driver = GraphDatabase.driver(
>             cfg.neo4j.uri,
>             auth=(cfg.neo4j.user, cfg.neo4j.password),
>         )
>         log.info("Neo4j driver initialised at %s", cfg.neo4j.uri)
>     return _driver
>
>
> def close_driver() -> None:
>     global _driver
>     if _driver:
>         _driver.close()
>         _driver = None
>
>
> @contextmanager
> def session() -> Generator[Session, None, None]:
>     with get_driver().session(database=cfg.neo4j.database) as s:
>         yield s
>
>
> def verify_connectivity() -> bool:
>     try:
>         get_driver().verify_connectivity()
>         return True
>     except Exception as exc:
>         log.warning("Neo4j connectivity check failed: %s", exc)
>         return False
> ```
