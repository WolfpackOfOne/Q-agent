"""Write a parsed QuantConnect project into the knowledge graph.

Turns the structured inventory from :func:`parser.parse_project` into nodes and
relationships, each stamped with provenance so agents can tell extracted facts
(and their confidence) from hand-declared ones.

A project is written as BOTH a ``Project`` node (the container of files/docs)
and a ``Strategy`` node of the same name, so the ingested project is
immediately compatible with the deployment-gate / latest-backtest lineage from
``ontology/policy.py``.

Node labels:  Project, Strategy, File, Module, Signal, ConfigParam,
              Dataset, ObjectStoreKey, ResearchNotebook
Relationships: CONTAINS, HAS_DOC, DEFINES, USES, WRITES, READS
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_graph_system.graph.backend import merge_node, merge_relationship
from agent_graph_system.ingestion.quantconnect.parser import CONF_AST, parse_project
from agent_graph_system.ontology.provenance import Provenance

log = logging.getLogger(__name__)

_EXTRACTOR = "quantconnect_project_extractor"


def ingest_project(project_root: str | Path) -> dict[str, Any]:
    """Parse and write ``project_root`` into the graph. Returns a count summary.

    Every fact written in one call shares a single ``run_ts``, stamped as its
    provenance ``last_seen`` and recorded on the Project node as
    ``last_ingest_run``. Re-ingest is merge-only (nothing is deleted), but
    because stale facts keep their older ``last_seen`` the context pack can tell
    current facts from ones whose file/config/key disappeared — see
    ``graph.context_pack``.
    """
    inv = parse_project(project_root)
    name = inv["project"]

    run_ts = datetime.now(timezone.utc).isoformat()

    def _declared(**kw: Any) -> Provenance:
        return Provenance.declared(_EXTRACTOR, last_seen=run_ts, **kw)

    def _extracted(**kw: Any) -> Provenance:
        return Provenance.extracted(_EXTRACTOR, last_seen=run_ts, **kw)

    declared = _declared(source_file=name)
    notebooks = set(inv["notebooks"])

    # Project + Strategy (same name) — declared, deterministic from the dir.
    # last_ingest_run marks which facts the current run refreshed.
    merge_node("Project", "name", name, {"root": inv["root"], "last_ingest_run": run_ts},
               provenance=declared)
    merge_node(
        "Strategy", "name", name,
        {"strategy_type": "factor", "status": "backtesting"},
        provenance=declared,
    )

    counts = {"files": 0, "docs": 0, "modules": 0, "signals": 0,
              "config_params": 0, "datasets": 0, "objectstore_keys": 0, "notebooks": 0}

    # File/ResearchNotebook nodes are keyed by a project-qualified path so two
    # projects that both contain e.g. main.py don't collapse onto one node.
    # rel_path keeps the bare path for display.
    def _fkey(rel: str) -> str:
        return f"{name}/{rel}"

    # Files (+ CONTAINS, HAS_DOC, ResearchNotebook).
    for f in inv["files"]:
        rel, kind = f["path"], f["kind"]
        fkey = _fkey(rel)
        file_prov = _extracted(source_file=rel, confidence=1.0)
        merge_node("File", "path", fkey, {"kind": kind, "project": name, "rel_path": rel},
                   provenance=file_prov)
        merge_relationship("Project", "name", name, "CONTAINS", "File", "path", fkey,
                           provenance=file_prov)
        counts["files"] += 1
        if kind == "doc":
            merge_relationship("Project", "name", name, "HAS_DOC", "File", "path", fkey,
                               provenance=file_prov)
            counts["docs"] += 1
        if kind == "notebook":
            merge_node("ResearchNotebook", "path", fkey, {"project": name, "rel_path": rel},
                       provenance=file_prov)
            merge_relationship("Project", "name", name, "CONTAINS",
                               "ResearchNotebook", "path", fkey, provenance=file_prov)
            counts["notebooks"] += 1

    # Modules: File DEFINES Module.
    for m in inv["modules"]:
        prov = _extracted(source_file=m["file"], line=m["line"], confidence=CONF_AST)
        mod_name = f"{name}.{m['name']}"
        merge_node("Module", "name", mod_name, {"class_name": m["name"], "project": name},
                   provenance=prov)
        merge_relationship("File", "path", _fkey(m["file"]), "DEFINES", "Module", "name", mod_name,
                           provenance=prov)
        counts["modules"] += 1

    # Signals: File DEFINES Signal (keyed by function name — shared atoms dedupe).
    for s in inv["signals"]:
        prov = _extracted(source_file=s["file"], line=s["line"], confidence=CONF_AST)
        merge_node("Signal", "name", s["name"], {"project": name}, provenance=prov)
        merge_relationship("File", "path", _fkey(s["file"]), "DEFINES", "Signal", "name", s["name"],
                           provenance=prov)
        counts["signals"] += 1

    # Config params.
    for c in inv["config_params"]:
        prov = _extracted(source_file=c["file"], line=c["line"], confidence=CONF_AST)
        cp_name = f"{name}.{c['name']}"
        merge_node("ConfigParam", "name", cp_name,
                   {"param": c["name"], "value": c["value"], "project": name}, provenance=prov)
        merge_relationship("Project", "name", name, "CONTAINS", "ConfigParam", "name", cp_name,
                           provenance=prov)
        counts["config_params"] += 1

    # Datasets: data subscriptions (resolved tickers) + bundled data files.
    seen_datasets: set[str] = set()
    for sub in inv["subscriptions"]:
        ticker = sub["ticker"]
        if not ticker:
            continue  # dynamic subscription (e.g. loop var) — not a nameable dataset
        prov = _extracted(source_file=sub["file"], line=sub["line"],
                                    confidence=sub["confidence"])
        merge_node("Dataset", "name", ticker, {"source": "QuantConnect"}, provenance=prov)
        merge_relationship("Strategy", "name", name, "USES", "Dataset", "name", ticker, provenance=prov)
        seen_datasets.add(ticker)
        counts["datasets"] += 1
    for data_rel in inv["data_files"]:
        if data_rel in seen_datasets:
            continue
        prov = _extracted(source_file=data_rel, confidence=1.0)
        merge_node("Dataset", "name", data_rel, {"source": "bundled"}, provenance=prov)
        merge_relationship("Strategy", "name", name, "USES", "Dataset", "name", data_rel, provenance=prov)
        seen_datasets.add(data_rel)
        counts["datasets"] += 1

    # ObjectStore keys: writes/reads. Reads from a notebook -> Notebook READS;
    # everything else attributes to the Strategy.
    seen_keys: set[str] = set()
    for op in inv["objectstore"]:
        key = op["key"] or f"<dynamic:{op['file']}:{op['line']}>"
        prov = _extracted(source_file=op["file"], line=op["line"],
                                    confidence=op["confidence"])
        if key not in seen_keys:
            merge_node("ObjectStoreKey", "key", key,
                       {"resolved": op["key"] is not None}, provenance=prov)
            seen_keys.add(key)
            counts["objectstore_keys"] += 1
        rel_type = "READS" if op["op"] == "read" else "WRITES"
        if op["file"] in notebooks:
            merge_relationship("ResearchNotebook", "path", _fkey(op["file"]), rel_type,
                               "ObjectStoreKey", "key", key, provenance=prov)
        else:
            merge_relationship("Strategy", "name", name, rel_type,
                               "ObjectStoreKey", "key", key, provenance=prov)

    log.info("Ingested project '%s': %s", name, counts)
    return {"project": name, "counts": counts}
