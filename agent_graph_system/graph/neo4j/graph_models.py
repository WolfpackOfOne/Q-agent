"""CRUD helpers for all ontology node and relationship types."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from agent_graph_system.graph.backend import merge_node, merge_relationship, query  # noqa: F401

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Entity-specific helpers
# ---------------------------------------------------------------------------

def upsert_dataset(name: str, source: str, status: str = "fresh", **props) -> None:
    merge_node("Dataset", "name", name, {"source": source, "status": status, **props})


def upsert_notebook(name: str, path: str, notebook_type: str = "research", **props) -> None:
    merge_node("Notebook", "name", name, {"path": path, "notebook_type": notebook_type, **props})


def upsert_strategy(name: str, strategy_type: str, status: str = "backtesting", **props) -> None:
    merge_node("Strategy", "name", name, {"strategy_type": strategy_type, "status": status, **props})


def upsert_backtest(run_id: str, name: str, sharpe: float, drawdown: float, cagr: float, **props) -> None:
    merge_node("Backtest", "run_id", run_id, {
        "name": name,
        "sharpe": sharpe,
        "max_drawdown": drawdown,
        "cagr": cagr,
        **props,
    })


def upsert_repository(name: str, url: str, branch: str = "main", **props) -> None:
    merge_node("Repository", "name", name, {"url": url, "branch": branch, **props})


def upsert_pipeline(name: str, pipeline_type: str, status: str = "idle", **props) -> None:
    merge_node("Pipeline", "name", name, {"pipeline_type": pipeline_type, "status": status, **props})


def upsert_agent(name: str, role: str, status: str = "active", **props) -> None:
    merge_node("Agent", "name", name, {"role": role, "status": status, **props})


def upsert_security(ticker: str, name: str, asset_type: str = "equity", sector: str = "", **props) -> None:
    merge_node("Security", "ticker", ticker, {"name": name, "asset_type": asset_type, "sector": sector, **props})


# ---------------------------------------------------------------------------
# Relationship helpers
# ---------------------------------------------------------------------------

def notebook_uses_dataset(notebook: str, dataset: str, **props) -> None:
    merge_relationship("Notebook", "name", notebook, "USES", "Dataset", "name", dataset, props)


def strategy_uses_dataset(strategy: str, dataset: str, **props) -> None:
    merge_relationship("Strategy", "name", strategy, "USES", "Dataset", "name", dataset, props)


def notebook_generates_backtest(notebook: str, run_id: str, **props) -> None:
    merge_relationship("Notebook", "name", notebook, "GENERATES", "Backtest", "run_id", run_id, props)


def strategy_has_backtest(strategy: str, run_id: str, **props) -> None:
    """Link a Strategy to one of its Backtest runs (lineage for the gate)."""
    merge_relationship("Strategy", "name", strategy, "HAS_BACKTEST", "Backtest", "run_id", run_id, props)


def strategy_deploys_to(
    strategy: str,
    api_name: str,
    environment: str = "paper",
    *,
    enforce_gate: bool = True,
    **props,
) -> None:
    """Write a Strategy -[DEPLOYS_TO]-> API edge.

    For live environments this is gated by the enforced ``deployment_gate``
    rule and is fail-closed: if the gate denies the write a
    :class:`~agent_graph_system.ontology.policy.PolicyViolation` is raised and
    no edge is written. Pass ``enforce_gate=False`` only for trusted backfills.
    """
    if enforce_gate:
        from agent_graph_system.ontology.policy import PolicyViolation, check_deployment_gate

        decision = check_deployment_gate(strategy, environment)
        if not decision.allowed:
            log.warning(
                "Blocked DEPLOYS_TO %s->%s (%s): %s",
                strategy, api_name, decision.code, decision.message,
            )
            raise PolicyViolation(decision)

    merge_relationship("Strategy", "name", strategy, "DEPLOYS_TO", "API", "name", api_name, {
        "environment": environment, **props
    })


def latest_backtest_for_strategy(strategy: str) -> dict[str, Any] | None:
    """Neo4j implementation of the latest-valid-backtest lookup.

    Mirrors the local engine: linked via ``HAS_BACKTEST`` or a ``strategy``
    property, excluding failed/running runs, ordered by recency.
    """
    from agent_graph_system.graph.neo4j.driver import session

    cypher = """
        MATCH (b:Backtest)
        WHERE (
            EXISTS { MATCH (:Strategy {name: $name})-[:HAS_BACKTEST]->(b) }
            OR b.strategy = $name
        )
        AND coalesce(b.status, 'completed') NOT IN ['failed', 'running']
        RETURN b AS bt
        ORDER BY coalesce(b.completed_at, b.run_date, b.created_at, b.updated_at, '') DESC
        LIMIT 1
    """
    with session() as s:
        record = s.run(cypher, name=strategy).single()
        return dict(record["bt"]) if record else None


def repository_contains_notebook(repo: str, notebook: str, **props) -> None:
    merge_relationship("Repository", "name", repo, "CONTAINS", "Notebook", "name", notebook, props)


def pipeline_produces_dataset(pipeline: str, dataset: str, **props) -> None:
    merge_relationship("Pipeline", "name", pipeline, "PRODUCES", "Dataset", "name", dataset, props)


def dataset_feeds_strategy(dataset: str, strategy: str, valid_from: str = "", valid_to: str = "", **props) -> None:
    extra: dict[str, Any] = {**props}
    if valid_from:
        extra["valid_from"] = valid_from
    if valid_to:
        extra["valid_to"] = valid_to
    merge_relationship("Dataset", "name", dataset, "FEEDS", "Strategy", "name", strategy, extra)


def agent_monitors(agent: str, target_label: str, target_name_key: str, target_name: str, **props) -> None:
    merge_relationship("Agent", "name", agent, "MONITORS", target_label, target_name_key, target_name, props)
