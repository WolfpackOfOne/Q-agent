"""
Graph backend selector.
Set GRAPH_BACKEND=neo4j to use a live Neo4j server.
Defaults to the local networkx engine (no server required).
"""

import os

_backend = os.getenv("GRAPH_BACKEND", "local").lower()

if _backend == "neo4j":
    from agent_graph_system.graph.neo4j.driver import verify_connectivity
    if not verify_connectivity():
        import logging
        logging.getLogger(__name__).warning(
            "GRAPH_BACKEND=neo4j but Neo4j unreachable — falling back to local engine"
        )
        from agent_graph_system.graph.local.engine import (  # noqa: F401
            merge_node, merge_relationship, query, create_indexes, graph_stats,
            latest_backtest_for_strategy,
        )
    else:
        from agent_graph_system.graph.neo4j.graph_models import (  # noqa: F401
            merge_node, merge_relationship, latest_backtest_for_strategy,
        )
        from agent_graph_system.graph.neo4j.driver import query  # noqa: F401
        from agent_graph_system.graph.cypher.queries import create_indexes  # noqa: F401

        def graph_stats():
            from agent_graph_system.graph.neo4j.driver import query as q
            nodes = q("MATCH (n) RETURN labels(n)[0] AS label, count(*) AS count ORDER BY count DESC")
            rels = q("MATCH ()-[r]->() RETURN type(r) AS rel, count(*) AS count ORDER BY count DESC")
            return {
                "node_counts": {r["label"]: r["count"] for r in nodes},
                "rel_counts": {r["rel"]: r["count"] for r in rels},
            }
else:
    from agent_graph_system.graph.local.engine import (  # noqa: F401
        merge_node, merge_relationship, query, create_indexes, graph_stats,
        latest_backtest_for_strategy,
    )
