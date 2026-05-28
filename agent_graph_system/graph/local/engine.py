"""
In-process graph engine backed by networkx.
Implements the same merge_node / merge_relationship / query interface
as graph_models so the rest of the system is backend-agnostic.
"""

from __future__ import annotations

import json
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any

import networkx as nx

log = logging.getLogger(__name__)

_PERSIST_PATH = Path(__file__).parent.parent.parent / ".local_graph.pkl"

# Backtest statuses that never count as a valid completed backtest.
_INVALID_BACKTEST_STATUSES = frozenset({"failed", "running"})

# MultiDiGraph: multiple edge types between same pair of nodes
_G: nx.MultiDiGraph = nx.MultiDiGraph()


def _load() -> None:
    global _G
    if _PERSIST_PATH.exists():
        try:
            with open(_PERSIST_PATH, "rb") as f:
                _G = pickle.load(f)
            log.info("Local graph loaded — %d nodes, %d edges", _G.number_of_nodes(), _G.number_of_edges())
        except Exception as exc:
            log.warning("Could not load persisted graph (%s), starting fresh", exc)
            _G = nx.MultiDiGraph()
    else:
        log.info("Local graph starting fresh")


def _save() -> None:
    with open(_PERSIST_PATH, "wb") as f:
        pickle.dump(_G, f)


_load()


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------

def merge_node(label: str, key: str, key_value: str, props: dict[str, Any] | None = None) -> None:
    node_id = f"{label}::{key_value}"
    existing = dict(_G.nodes.get(node_id, {}))
    existing.update(props or {})
    existing["_label"] = label
    existing[key] = key_value
    existing["updated_at"] = datetime.utcnow().isoformat()
    _G.add_node(node_id, **existing)
    _save()


def merge_relationship(
    from_label: str, from_key: str, from_val: str,
    rel_type: str,
    to_label: str, to_key: str, to_val: str,
    props: dict[str, Any] | None = None,
) -> None:
    from_id = f"{from_label}::{from_val}"
    to_id = f"{to_label}::{to_val}"
    if from_id not in _G or to_id not in _G:
        log.debug("merge_relationship: node(s) not found — %s, %s", from_id, to_id)
        return
    # Check if this exact (from, rel_type, to) triple already exists
    for _, v, data in _G.out_edges(from_id, data=True):
        if data.get("_type") == rel_type and v == to_id:
            data.update(props or {})
            data["updated_at"] = datetime.utcnow().isoformat()
            _save()
            return
    edge_props = dict(props or {})
    edge_props["_type"] = rel_type
    edge_props["updated_at"] = datetime.utcnow().isoformat()
    _G.add_edge(from_id, to_id, **edge_props)
    _save()


def query(cypher: str, **params) -> list[dict[str, Any]]:
    """
    Lightweight Cypher interpreter for the named patterns we actually use.
    Handles the specific queries in graph/cypher/queries.py.
    """
    c = cypher.strip().upper()

    # --- notebooks using WRDS ---
    if "WRDS" in c and "NOTEBOOK" in c and "DATASET" in c:
        results = []
        for u, v, data in _G.edges(data=True):
            if data.get("_type") != "USES":
                continue
            nb = _G.nodes.get(u, {})
            ds = _G.nodes.get(v, {})
            if nb.get("_label") == "Notebook" and ds.get("_label") == "Dataset" and ds.get("source") == "WRDS":
                results.append({
                    "notebook": nb.get("name", u),
                    "path": nb.get("path", ""),
                    "dataset": ds.get("name", v),
                    "data_status": ds.get("status", "unknown"),
                })
        return results

    # --- stale dataset dependencies (strategy->dataset traversal) ---
    if "STALE" in c and "STRATEGY" in c and ("USES" in c or "DEPENDS" in c):
        results = []
        for u, v, data in _G.edges(data=True):
            if data.get("_type") not in ("USES", "DEPENDS_ON"):
                continue
            src = _G.nodes.get(u, {})
            dst = _G.nodes.get(v, {})
            if dst.get("status") == "stale":
                results.append({
                    "strategy": src.get("name", u),
                    "strategy_status": src.get("status", ""),
                    "stale_dataset": dst.get("name", v),
                    "last_updated": dst.get("last_updated", ""),
                })
        return results

    # --- active deployments ---
    if "DEPLOYS_TO" in c:
        results = []
        for u, v, data in _G.edges(data=True):
            if data.get("_type") == "DEPLOYS_TO":
                s = _G.nodes.get(u, {})
                a = _G.nodes.get(v, {})
                results.append({
                    "strategy": s.get("name", u),
                    "broker": a.get("name", v),
                    "env": data.get("environment", ""),
                    "deployed_at": data.get("deployed_at", ""),
                })
        return results

    # --- pipeline health ---
    if "PIPELINE" in c and "PRODUCES" in c:
        results = []
        for node_id, data in _G.nodes(data=True):
            if data.get("_label") != "Pipeline":
                continue
            outputs = [
                _G.nodes[v].get("name", v)
                for _, v, ed in _G.out_edges(node_id, data=True)
                if ed.get("_type") == "PRODUCES"
            ]
            results.append({
                "pipeline": data.get("name", node_id),
                "status": data.get("status", ""),
                "last_run": data.get("last_run", ""),
                "output_datasets": outputs,
            })
        return results

    # --- dataset dependents ---
    if "DEPEND" in c or ("USES" in c and "DATASET" in c):
        ds_name = params.get("name", "")
        results = []
        for u, v, data in _G.edges(data=True):
            if data.get("_type") not in ("USES", "DEPENDS_ON", "FEEDS"):
                continue
            dst = _G.nodes.get(v, {})
            if ds_name and dst.get("name") != ds_name:
                continue
            src = _G.nodes.get(u, {})
            results.append({
                "entity_type": src.get("_label", ""),
                "entity": src.get("name", u),
                "status": src.get("status", ""),
            })
        return results

    # --- agent task graph ---
    if "MONITORS" in c and "AGENT" in c:
        results = []
        for u, v, data in _G.edges(data=True):
            if data.get("_type") == "MONITORS":
                a = _G.nodes.get(u, {})
                t = _G.nodes.get(v, {})
                results.append({
                    "agent": a.get("name", u),
                    "role": a.get("role", ""),
                    "watching_type": t.get("_label", ""),
                    "watching": t.get("name", v),
                    "target_status": t.get("status", ""),
                })
        return results

    # --- neighbourhood (full context) ---
    if "*1.." in c or "path" in c.lower():
        name = params.get("name", "")
        label = _extract_label_from_match(cypher)
        if not name or not label:
            return []
        seed_id = f"{label}::{name}"
        if seed_id not in _G:
            return []
        results = []
        for nbr in nx.ego_graph(_G, seed_id, radius=2).nodes():
            if nbr == seed_id:
                continue
            nd = _G.nodes.get(nbr, {})
            rel = next(
                (ed.get("_type", "") for _, v, ed in _G.out_edges(seed_id, data=True) if v == nbr),
                "RELATED"
            )
            results.append({
                "node_type": nd.get("_label", ""),
                "name": nd.get("name", nbr),
                "via_relationship": rel,
            })
        return results

    # --- backtest lineage ---
    if "LINEAGE" in c or ("BACKTEST" in c and "STRATEGY" in c):
        name = params.get("name", "")
        results = []
        for node_id, data in _G.nodes(data=True):
            if data.get("_label") == "Backtest" and data.get("strategy") == name:
                results.append({
                    "strategy": name,
                    "dataset": "",
                    "notebook": "",
                    "backtest_id": data.get("run_id", node_id),
                    "sharpe": data.get("sharpe", 0),
                    "cagr": data.get("cagr", 0),
                })
        return results

    # Generic fallback: return nodes matching a label, with optional WHERE status filter
    label = _extract_label_from_match(cypher)
    if label:
        # Parse a simple WHERE x.status = 'value' clause if present
        import re
        status_filter: str | None = None
        m = re.search(r"WHERE\s+\w+\.status\s*=\s*['\"]([^'\"]+)['\"]", cypher, re.IGNORECASE)
        if m:
            status_filter = m.group(1)
        name_filter: str | None = params.get("name")
        results = []
        for _, data in _G.nodes(data=True):
            if data.get("_label") != label:
                continue
            if status_filter and data.get("status") != status_filter:
                continue
            if name_filter and data.get("name") != name_filter and data.get("run_id") != name_filter:
                continue
            results.append(dict(data))
        return results

    log.debug("Unhandled query pattern — returning empty: %s", cypher[:80])
    return []


def _extract_label_from_match(cypher: str) -> str:
    """Pull the first :Label from a MATCH clause."""
    import re
    m = re.search(r":\s*([A-Za-z][A-Za-z0-9_]*)", cypher)
    return m.group(1) if m else ""


def latest_backtest_for_strategy(strategy: str) -> dict[str, Any] | None:
    """Return the latest valid backtest linked to ``strategy``, or None.

    A backtest is linked either via a ``Strategy -[HAS_BACKTEST]-> Backtest``
    edge or by carrying a ``strategy`` property. Failed/running backtests are
    excluded; "latest" is the max over completed_at / run_date / created_at /
    updated_at. Results are de-duplicated by run_id.
    """
    candidates: dict[str, dict[str, Any]] = {}

    def _add(node: dict[str, Any]) -> None:
        if node.get("_label") != "Backtest":
            return
        key = node.get("run_id") or node.get("name") or id(node)
        candidates[str(key)] = dict(node)

    seed_id = f"Strategy::{strategy}"
    if seed_id in _G:
        for _, v, data in _G.out_edges(seed_id, data=True):
            if data.get("_type") == "HAS_BACKTEST":
                _add(_G.nodes.get(v, {}))

    for _, data in _G.nodes(data=True):
        if data.get("_label") == "Backtest" and data.get("strategy") == strategy:
            _add(data)

    pool = [
        b for b in candidates.values()
        if b.get("status", "completed") not in _INVALID_BACKTEST_STATUSES
    ]
    if not pool:
        return None

    def _ts(node: dict[str, Any]) -> str:
        for key in ("completed_at", "run_date", "created_at", "updated_at"):
            if node.get(key):
                return str(node[key])
        return ""

    return max(pool, key=_ts)


def graph_stats() -> dict[str, Any]:
    label_counts: dict[str, int] = {}
    for _, data in _G.nodes(data=True):
        lbl = data.get("_label", "Unknown")
        label_counts[lbl] = label_counts.get(lbl, 0) + 1

    rel_counts: dict[str, int] = {}
    for _, _, data in _G.edges(data=True):
        rt = data.get("_type", "Unknown")
        rel_counts[rt] = rel_counts.get(rt, 0) + 1

    return {
        "nodes": _G.number_of_nodes(),
        "edges": _G.number_of_edges(),
        "node_counts": dict(sorted(label_counts.items(), key=lambda x: -x[1])),
        "rel_counts": dict(sorted(rel_counts.items(), key=lambda x: -x[1])),
    }


def create_indexes() -> None:
    log.info("Local graph backend — no indexes needed")
