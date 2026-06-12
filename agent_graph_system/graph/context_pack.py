"""Build a project *context pack* for coding agents.

Before an agent edits a project it should know what the project is made of:
its docs, important files, the datasets and ObjectStore keys it touches, any
backtests and their metrics, the signals/modules it defines, known risks, and
which facts are only low-confidence guesses. This module assembles exactly that
from the ingested graph (see ``ingestion/quantconnect``) and can render it as
markdown or JSON.

It reads the local graph backend (the default and only fully-implemented one);
a Neo4j-backed reader is a future parity item.
"""

from __future__ import annotations

from typing import Any

from agent_graph_system.graph.local import engine
from agent_graph_system.ontology.provenance import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    PROV_PREFIX,
    is_low_confidence,
)

# Files an agent should almost always read before editing.
_PRIORITY_BASENAMES = ("main.py", "config.py")
_PRIORITY_DIRS = ("docs/", "domain/signals/")


class ProjectNotInGraph(KeyError):
    """Raised when a context pack is requested for an un-ingested project."""


def _fact_summary(props: dict[str, Any]) -> dict[str, Any]:
    """Compact provenance view for the low-confidence section."""
    return {
        "extractor": props.get(f"{PROV_PREFIX}extractor"),
        "assertion_type": props.get(f"{PROV_PREFIX}assertion_type"),
        "confidence": props.get(f"{PROV_PREFIX}confidence"),
        "source_file": props.get(f"{PROV_PREFIX}source_file"),
        "line": props.get(f"{PROV_PREFIX}line"),
    }


def build_context_pack(
    project: str, *, confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
) -> dict[str, Any]:
    """Assemble a structured context pack for ``project`` from the graph."""
    project_id = f"Project::{project}"
    strategy_id = f"Strategy::{project}"
    project_node = engine.get_node(project_id)
    if project_node is None:
        raise ProjectNotInGraph(
            f"Project '{project}' is not in the graph — ingest it first "
            f"(ingestion.quantconnect.graph_writer.ingest_project)."
        )

    # Facts refreshed by the latest ingest carry this run marker as last_seen.
    # Edges from an older run (whose file/config/key has since disappeared) keep
    # their stale marker and are filtered out below, so the pack reflects the
    # current project rather than accreting deleted artifacts. A project with no
    # run marker (legacy ingest) disables filtering — nothing is hidden.
    run_marker = project_node.get("last_ingest_run")

    files: list[str] = []
    docs: list[str] = []
    config_params: list[dict[str, Any]] = []
    notebooks: list[str] = []
    file_ids: list[str] = []
    notebook_ids: list[str] = []

    # Track the project's connected subgraph so low-confidence facts can be
    # gathered from exactly the nodes/edges that belong to this project —
    # including shared-label nodes (ObjectStoreKey, Dataset) that don't carry a
    # `project` property.
    touched_nodes: set[str] = {project_id, strategy_id}
    edge_facts: list[tuple[str, dict[str, Any]]] = []

    def _is_current(props: dict[str, Any]) -> bool:
        """True unless the fact was last seen by an older ingest run."""
        if run_marker is None:
            return True
        last_seen = props.get(f"{PROV_PREFIX}last_seen")
        return last_seen is None or last_seen == run_marker

    def _visit(src_id: str) -> list[tuple[str, str, dict[str, Any]]]:
        """Follow only edges refreshed by the latest ingest run."""
        kept: list[tuple[str, str, dict[str, Any]]] = []
        for rel_type, target_id, edge in engine.out_relations(src_id):
            if not _is_current(edge):
                continue
            touched_nodes.add(target_id)
            edge_facts.append((f"{src_id} -[{rel_type}]-> {target_id}", edge))
            kept.append((rel_type, target_id, edge))
        return kept

    def _disp(node: dict[str, Any], fallback: str) -> str:
        return node.get("rel_path") or node.get("path") or fallback

    for rel_type, target_id, _edge in _visit(project_id):
        node = engine.get_node(target_id) or {}
        label = node.get("_label")
        if label == "File":
            (docs if rel_type == "HAS_DOC" else files).append(_disp(node, target_id))
            file_ids.append(target_id)
        elif label == "ConfigParam":
            config_params.append({"param": node.get("param"), "value": node.get("value")})
        elif label == "ResearchNotebook":
            notebooks.append(_disp(node, target_id))
            notebook_ids.append(target_id)

    # Datasets / ObjectStore keys via the Strategy node's edges.
    datasets: list[dict[str, Any]] = []
    objectstore: list[dict[str, Any]] = []
    for rel_type, target_id, _edge in _visit(strategy_id):
        node = engine.get_node(target_id) or {}
        label = node.get("_label")
        if label == "Dataset" and rel_type == "USES":
            datasets.append({"name": node.get("name"), "source": node.get("source")})
        elif label == "ObjectStoreKey" and rel_type in ("READS", "WRITES"):
            objectstore.append({
                "key": node.get("key"), "op": rel_type.lower(),
                "resolved": bool(node.get("resolved", True)),
            })

    # Notebook ObjectStore reads (Notebook READS ObjectStoreKey).
    for nb_id in notebook_ids:
        nb_disp = _disp(engine.get_node(nb_id) or {}, nb_id)
        for rel_type, target_id, _edge in _visit(nb_id):
            node = engine.get_node(target_id) or {}
            if node.get("_label") == "ObjectStoreKey" and rel_type in ("READS", "WRITES"):
                objectstore.append({
                    "key": node.get("key"), "op": rel_type.lower(),
                    "resolved": bool(node.get("resolved", True)), "via": f"notebook:{nb_disp}",
                })

    # Signals / modules via DEFINES edges from this project's files — robust to
    # shared Signal nodes whose `project` property may belong to another project.
    signal_names: set[str] = set()
    module_names: set[str] = set()
    for fid in file_ids:
        for rel_type, target_id, _edge in _visit(fid):
            if rel_type != "DEFINES":
                continue
            node = engine.get_node(target_id) or {}
            if node.get("_label") == "Signal":
                signal_names.add(node.get("name"))
            elif node.get("_label") == "Module":
                module_names.add(node.get("class_name") or node.get("name"))
    signals = sorted(n for n in signal_names if n)
    modules = sorted(n for n in module_names if n)

    backtest = engine.latest_backtest_for_strategy(project)

    # Low-confidence facts: scan the project's connected nodes and the edges
    # between them, so dynamic ObjectStore keys etc. are surfaced honestly.
    low_conf: list[dict[str, Any]] = []
    for nid in sorted(touched_nodes):
        props = engine.get_node(nid)
        if props and is_low_confidence(props, confidence_threshold):
            low_conf.append({"node": nid, **_fact_summary(props)})
    for descriptor, edge in edge_facts:
        if is_low_confidence(edge, confidence_threshold):
            low_conf.append({"node": descriptor, **_fact_summary(edge)})

    risks = _derive_risks(backtest, objectstore, low_conf)
    recommended = _recommend_files(files + docs + notebooks)

    return {
        "project": project,
        "summary": {
            "files": len(files), "docs": len(docs), "datasets": len(datasets),
            "objectstore_keys": len({o["key"] for o in objectstore}),
            "signals": len(signals), "modules": len(modules),
            "notebooks": len(notebooks),
            "has_completed_backtest": backtest is not None,
        },
        "important_files": recommended,
        "docs": sorted(docs),
        "datasets": datasets,
        "objectstore": objectstore,
        "backtest": backtest,
        "signals": signals,
        "modules": modules,
        "config_params": config_params,
        "notebooks": sorted(notebooks),
        "known_risks": risks,
        "low_confidence_facts": low_conf,
    }


def _derive_risks(
    backtest: dict[str, Any] | None,
    objectstore: list[dict[str, Any]],
    low_conf: list[dict[str, Any]],
) -> list[str]:
    risks: list[str] = []
    if backtest is None:
        risks.append(
            "No completed backtest is linked to this strategy — a live "
            "deployment_gate check would fail closed."
        )
    unresolved = [o for o in objectstore if not o["resolved"]]
    if unresolved:
        risks.append(
            f"{len(unresolved)} ObjectStore key(s) are computed at runtime and "
            "could not be resolved statically; verify keys before relying on them."
        )
    if low_conf:
        risks.append(
            f"{len(low_conf)} low-confidence fact(s) present — treat as hints, "
            "not ground truth."
        )
    return risks


def _recommend_files(paths: list[str]) -> list[str]:
    """Order files so the ones worth reading first come first."""
    def rank(p: str) -> tuple[int, str]:
        base = p.rsplit("/", 1)[-1]
        if base in _PRIORITY_BASENAMES:
            return (0, p)
        if any(p.startswith(d) or f"/{d}" in p for d in _PRIORITY_DIRS):
            return (1, p)
        if p.endswith(".md"):
            return (2, p)
        return (3, p)

    return [p for p in sorted(dict.fromkeys(paths), key=rank)]


def render_markdown(pack: dict[str, Any]) -> str:
    """Render a context pack as readable markdown."""
    s = pack["summary"]
    lines: list[str] = [
        f"# Context pack — {pack['project']}",
        "",
        "## Project summary",
        f"- Files: {s['files']} | Docs: {s['docs']} | Notebooks: {s['notebooks']}",
        f"- Datasets: {s['datasets']} | ObjectStore keys: {s['objectstore_keys']}",
        f"- Signals: {s['signals']} | Modules: {s['modules']}",
        f"- Completed backtest linked: {'yes' if s['has_completed_backtest'] else 'no'}",
        "",
        "## Recommended files to inspect before editing",
    ]
    lines += [f"- `{p}`" for p in pack["important_files"][:12]] or ["- (none)"]

    lines += ["", "## Relevant docs"]
    lines += [f"- `{d}`" for d in pack["docs"]] or ["- (none)"]

    lines += ["", "## Datasets & subscriptions"]
    lines += [f"- {d['name']} ({d['source']})" for d in pack["datasets"]] or ["- (none)"]

    lines += ["", "## ObjectStore reads/writes"]
    lines += [
        f"- {o['op']}: `{o['key']}`" + ("" if o["resolved"] else "  ⚠️ unresolved")
        for o in pack["objectstore"]
    ] or ["- (none)"]

    lines += ["", "## Backtests & metrics"]
    bt = pack["backtest"]
    if bt:
        lines.append(
            f"- latest: {bt.get('run_id') or bt.get('name')} "
            f"(sharpe={bt.get('sharpe')}, cagr={bt.get('cagr')})"
        )
    else:
        lines.append("- (no completed backtest linked)")

    lines += ["", "## Signals / modules detected"]
    lines.append(f"- signals: {', '.join(pack['signals']) or '(none)'}")
    lines.append(f"- modules: {', '.join(pack['modules']) or '(none)'}")

    lines += ["", "## Known risks"]
    lines += [f"- {r}" for r in pack["known_risks"]] or ["- (none)"]

    lines += ["", "## Low-confidence facts"]
    if pack["low_confidence_facts"]:
        for f in pack["low_confidence_facts"]:
            loc = f.get("source_file") or ""
            line = f":{f['line']}" if f.get("line") else ""
            lines.append(f"- `{f['node']}` (conf={f['confidence']}) {loc}{line}")
    else:
        lines.append("- (none)")

    return "\n".join(lines) + "\n"
