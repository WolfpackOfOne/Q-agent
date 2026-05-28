"""Isolation fixtures for agent_graph_system graph tests.

The local engine keeps a module-global networkx graph and persists it to a
pickle on every write. These fixtures give each test a clean in-memory graph
and disable persistence so the suite never touches the repo's .local_graph.pkl.
"""

from __future__ import annotations

import networkx as nx
import pytest

from agent_graph_system.graph.local import engine
from agent_graph_system.ontology import rules as rules_mod


@pytest.fixture(autouse=True)
def clean_graph(monkeypatch):
    """Reset the local graph and stub persistence for every test."""
    monkeypatch.setattr(engine, "_G", nx.MultiDiGraph(), raising=True)
    monkeypatch.setattr(engine, "_save", lambda: None, raising=True)
    # Rules are cached; clear so a test tweaking the rules file is honoured.
    rules_mod._cached_rules.cache_clear()
    yield
    rules_mod._cached_rules.cache_clear()
