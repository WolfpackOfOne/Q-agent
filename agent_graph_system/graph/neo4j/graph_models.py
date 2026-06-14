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


def upsert_walkforward_run(run_id: str, strategy: str, **props) -> None:
    """A walk-forward validation run for ``strategy``.

    ``status`` is one of ``completed`` | ``failed`` | ``insufficient_data``.
    Pass ``provenance=`` (e.g. ``Provenance.declared(...)``) for computed runs.
    """
    provenance = props.pop("provenance", None)
    merge_node(
        "WalkforwardRun", "run_id", run_id,
        {"strategy": strategy, **props},
        provenance=provenance,
    )


def upsert_walkforward_window(window_id: str, run_id: str, **props) -> None:
    """One train/test window belonging to a :func:`upsert_walkforward_run`."""
    provenance = props.pop("provenance", None)
    merge_node(
        "WalkforwardWindow", "window_id", window_id,
        {"run_id": run_id, **props},
        provenance=provenance,
    )


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


def strategy_has_walkforward(strategy: str, run_id: str, **props) -> None:
    """Link a Strategy to one of its WalkforwardRun results."""
    merge_relationship("Strategy", "name", strategy, "HAS_WALKFORWARD", "WalkforwardRun", "run_id", run_id, props)


def walkforward_run_has_window(run_id: str, window_id: str, **props) -> None:
    """Link a WalkforwardRun to one of its WalkforwardWindow nodes."""
    merge_relationship("WalkforwardRun", "run_id", run_id, "HAS_WINDOW", "WalkforwardWindow", "window_id", window_id, props)


def walkforward_validates_backtest(run_id: str, backtest_run_id: str, **props) -> None:
    """A WalkforwardRun VALIDATES the Backtest it was computed against.

    Lets the live deployment gate ask not just "is there a backtest?" but
    "is there a walk-forward run validating it?".
    """
    merge_relationship("WalkforwardRun", "run_id", run_id, "VALIDATES", "Backtest", "run_id", backtest_run_id, props)


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


def latest_walkforward_for_strategy(strategy: str) -> dict[str, Any] | None:
    """Neo4j implementation of the latest-completed-walkforward lookup.

    Mirrors :func:`latest_backtest_for_strategy`: linked via ``HAS_WALKFORWARD``
    or a ``strategy`` property, restricted to completed runs, newest first.
    """
    from agent_graph_system.graph.neo4j.driver import session

    cypher = """
        MATCH (w:WalkforwardRun)
        WHERE (
            EXISTS { MATCH (:Strategy {name: $name})-[:HAS_WALKFORWARD]->(w) }
            OR w.strategy = $name
        )
        AND coalesce(w.status, 'completed') = 'completed'
        RETURN w AS wf
        ORDER BY coalesce(w.created_at, w.updated_at, '') DESC
        LIMIT 1
    """
    with session() as s:
        record = s.run(cypher, name=strategy).single()
        return dict(record["wf"]) if record else None


def latest_walkforward_for_backtest(backtest_run_id: str) -> dict[str, Any] | None:
    """Latest completed walk-forward run that VALIDATES a specific backtest.

    Mirrors the local engine: only runs linked by ``VALIDATES`` to this exact
    backtest qualify, so the gate cannot accept a run that validated an older
    backtest. ``validates_backtest`` is returned alongside the run properties.
    """
    from agent_graph_system.graph.neo4j.driver import session

    cypher = """
        MATCH (w:WalkforwardRun)-[:VALIDATES]->(b:Backtest {run_id: $bt})
        WHERE coalesce(w.status, 'completed') = 'completed'
        RETURN w AS wf
        ORDER BY coalesce(w.created_at, w.updated_at, '') DESC
        LIMIT 1
    """
    with session() as s:
        record = s.run(cypher, bt=backtest_run_id).single()
        if not record:
            return None
        wf = dict(record["wf"])
        wf["validates_backtest"] = backtest_run_id
        return wf


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
