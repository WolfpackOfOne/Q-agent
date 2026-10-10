---
path: "tests/agent_graph_system/conftest.py"
hub: "Tests"
lines: 26
tags:
  - "code/python"
  - "areas/Tests"
github: "https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/conftest.py"
---
# conftest.py

`tests/agent_graph_system/conftest.py` · hub [[Hubs/Areas/Tests|Tests]] · [GitHub](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/conftest.py)

## Purpose

Isolation fixtures for agent_graph_system graph tests.

The local engine keeps a module-global networkx graph and persists it to a
pickle on every write. These fixtures give each test a clean in-memory graph
and disable persistence so the suite never touches the repo's .local_graph.pkl.

## Dependencies

**Imports (workspace):** [[Code/agent_graph_system/graph/local/engine.py|engine.py]], [[Code/agent_graph_system/ontology/rules.py|rules.py]]

**Imports (external):** [[Indexes/External packages#__future__|__future__]], [[Indexes/External packages#networkx|networkx]], [[Indexes/External packages#pytest|pytest]]

## Functions

### `clean_graph()`

```python
def clean_graph(monkeypatch)
```
[line 18](https://github.com/WolfpackOfOne/Q-agent/blob/main/tests/agent_graph_system/conftest.py#L18)

Reset the local graph and stub persistence for every test.

## Source

> [!example]- tests/agent_graph_system/conftest.py (26 lines)
> ```python
> """Isolation fixtures for agent_graph_system graph tests.
>
> The local engine keeps a module-global networkx graph and persists it to a
> pickle on every write. These fixtures give each test a clean in-memory graph
> and disable persistence so the suite never touches the repo's .local_graph.pkl.
> """
>
> from __future__ import annotations
>
> import networkx as nx
> import pytest
>
> from agent_graph_system.graph.local import engine
> from agent_graph_system.ontology import rules as rules_mod
>
>
> @pytest.fixture(autouse=True)
> def clean_graph(monkeypatch):
>     """Reset the local graph and stub persistence for every test."""
>     monkeypatch.setattr(engine, "_G", nx.MultiDiGraph(), raising=True)
>     monkeypatch.setattr(engine, "_save", lambda: None, raising=True)
>     # Rules are cached; clear so a test tweaking the rules file is honoured.
>     rules_mod._cached_rules.cache_clear()
>     yield
>     rules_mod._cached_rules.cache_clear()
> ```
