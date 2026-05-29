"""
main.py — Agentic Graph Ontology System

Entry point with subcommands:
  init            Create Neo4j indexes and seed the graph from ontology schema
  ingest          Parse a local repo and write to the graph
  ingest-project  Ingest one MyProjects/ QuantConnect project into the graph
  context-pack    Build a project context pack for an agent (md | json)
  query           Run a named Cypher query or GraphRAG search
  agent       Run a named agent (coding | monitoring | orchestration | research)
  api         Start the FastAPI server
  status      Show graph node/relationship counts

Usage:
  python -m agent_graph_system.main init
  python -m agent_graph_system.main ingest --repo /path/to/repo
  python -m agent_graph_system.main query stale-deps
  python -m agent_graph_system.main query rag "show notebooks using WRDS data"
  python -m agent_graph_system.main agent monitoring
  python -m agent_graph_system.main api
  python -m agent_graph_system.main status
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from agent_graph_system.config import cfg

logging.basicConfig(
    level=getattr(logging, cfg.log_level.upper(), logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("main")


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------

def cmd_init(args: argparse.Namespace) -> None:
    """Bootstrap the graph: create indexes, seed agents, datasets, pipelines."""
    from agent_graph_system.graph.cypher.queries import create_indexes
    from agent_graph_system.graph.neo4j import graph_models as gm
    import os
    log.info("Backend: %s", os.getenv("GRAPH_BACKEND", "local"))
    log.info("Creating indexes …")
    create_indexes()

    # Seed the known agents
    for name, role in [
        ("ResearchAgent", "research"),
        ("CodingAgent", "coding"),
        ("MonitoringAgent", "monitoring"),
        ("OrchestrationAgent", "orchestration"),
    ]:
        gm.upsert_agent(name, role=role, status="idle")

    # Seed the known data pipelines
    for name, src in [
        ("WRDS_CRSP_Daily", "WRDS"),
        ("EDGAR_Fundamentals", "EDGAR"),
        ("Polymarket_Prices", "Polymarket"),
        ("Crypto_OHLCV", "Crypto"),
    ]:
        gm.upsert_dataset(f"{src}_Data", source=src, status="fresh")
        gm.upsert_pipeline(f"{name}_Pipeline", pipeline_type="ingestion")
        gm.pipeline_produces_dataset(f"{name}_Pipeline", f"{src}_Data")

    log.info("Init complete. Open http://localhost:7474 to explore the graph.")


def cmd_ingest(args: argparse.Namespace) -> None:
    """Parse a local git repo and write notebook/dependency graph."""
    from agent_graph_system.agents.coding_agent import CodingAgent
    repo_path = Path(args.repo).expanduser().resolve()
    if not repo_path.exists():
        log.error("Repo path not found: %s", repo_path)
        sys.exit(1)
    result = CodingAgent().run(repo_path=repo_path, repo_url=args.url or "")
    log.info("Ingested %d notebooks from '%s'", result["total"], result["repo"])


def cmd_ingest_project(args: argparse.Namespace) -> None:
    """Ingest a single MyProjects/ QuantConnect project into the graph."""
    from agent_graph_system.ingestion.quantconnect.graph_writer import ingest_project
    project_path = Path(args.project).expanduser().resolve()
    if not project_path.is_dir():
        log.error("Project path not found: %s", project_path)
        sys.exit(1)
    result = ingest_project(project_path)
    log.info("Ingested project '%s': %s", result["project"], result["counts"])
    print(json.dumps(result, indent=2, default=str))


def cmd_context_pack(args: argparse.Namespace) -> None:
    """Build a project context pack for an agent (markdown or JSON)."""
    from agent_graph_system.graph import context_pack as cp
    from agent_graph_system.ingestion.quantconnect.graph_writer import ingest_project

    path = Path(args.project).expanduser()
    project_name = path.name if (path.exists() or "/" in args.project) else args.project

    # By default, (re)ingest from the path so the pack reflects the files on disk.
    if not args.no_ingest:
        if not path.is_dir():
            log.error("Project path not found: %s (use --no-ingest to read the graph as-is)", path)
            sys.exit(1)
        ingest_project(path.resolve())
        project_name = path.name

    try:
        pack = cp.build_context_pack(project_name)
    except cp.ProjectNotInGraph as exc:
        log.error("%s", exc)
        sys.exit(1)

    if args.format == "json":
        print(json.dumps(pack, indent=2, default=str))
    else:
        print(cp.render_markdown(pack))


def cmd_query(args: argparse.Namespace) -> None:
    """Run a named query or GraphRAG search."""
    from agent_graph_system.graph.cypher import queries as cq
    from agent_graph_system.rag.retriever import graphrag_query, stale_impact_report

    name = args.query_name

    dispatch = {
        "wrds-notebooks":    cq.notebooks_using_wrds,
        "stale-deps":        cq.stale_strategy_dependencies,
        "deployments":       cq.active_deployments,
        "pipeline-health":   cq.pipeline_health,
        "agents":            cq.agent_task_graph,
        "stale-impact":      stale_impact_report,
    }

    if name == "rag":
        if not args.question:
            log.error("Pass a question: python main.py query rag \"your question\"")
            sys.exit(1)
        result = graphrag_query(args.question)
    elif name in dispatch:
        result = dispatch[name]()
    else:
        log.error("Unknown query '%s'. Available: %s", name, ", ".join(sorted(dispatch)))
        sys.exit(1)

    print(json.dumps(result, indent=2, default=str))


def cmd_agent(args: argparse.Namespace) -> None:
    """Run a named agent once."""
    agents = {
        "coding":        ("agent_graph_system.agents.coding_agent", "CodingAgent"),
        "monitoring":    ("agent_graph_system.agents.monitoring_agent", "MonitoringAgent"),
        "orchestration": ("agent_graph_system.agents.orchestration_agent", "OrchestrationAgent"),
        "research":      ("agent_graph_system.agents.research_agent", "ResearchAgent"),
    }
    name = args.agent_name.lower()
    if name not in agents:
        log.error("Unknown agent '%s'. Available: %s", name, ", ".join(sorted(agents)))
        sys.exit(1)

    module_path, class_name = agents[name]
    import importlib
    module = importlib.import_module(module_path)
    agent_cls = getattr(module, class_name)

    kwargs: dict = {}
    if name == "coding":
        kwargs["repo_path"] = args.repo or str(Path.cwd())
    if name == "research" and args.question:
        kwargs["question"] = args.question

    result = agent_cls().run(**kwargs)
    print(json.dumps(result, indent=2, default=str))


def cmd_api(args: argparse.Namespace) -> None:
    """Start the FastAPI server."""
    import uvicorn
    uvicorn.run(
        "agent_graph_system.api.app:app",
        host=cfg.api.host,
        port=cfg.api.port,
        reload=cfg.api.reload,
        log_level=cfg.log_level.lower(),
    )


def cmd_status(args: argparse.Namespace) -> None:
    """Print node and relationship counts."""
    from agent_graph_system.graph.backend import graph_stats
    import os
    stats = graph_stats()
    backend = os.getenv("GRAPH_BACKEND", "local")
    print(f"\n=== Graph status (backend: {backend}) ===")
    print(f"  Total nodes : {stats.get('nodes', sum(stats.get('node_counts', {}).values()))}")
    print(f"  Total edges : {stats.get('edges', sum(stats.get('rel_counts', {}).values()))}")
    print("\n  Node counts:")
    for label, count in stats.get("node_counts", {}).items():
        print(f"    {label:<20} {count}")
    print("\n  Relationship counts:")
    for rel, count in stats.get("rel_counts", {}).items():
        print(f"    {rel:<30} {count}")
    print()


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m agent_graph_system.main",
        description="Agentic Graph Ontology System",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # init
    sub.add_parser("init", help="Bootstrap Neo4j schema and seed graph")

    # ingest
    ingest_p = sub.add_parser("ingest", help="Ingest a local repo into the graph")
    ingest_p.add_argument("--repo", default=str(Path.cwd()), help="Path to repo root")
    ingest_p.add_argument("--url", default="", help="Remote URL for the repo")

    # ingest-project
    ip = sub.add_parser("ingest-project", help="Ingest one MyProjects/ project into the graph")
    ip.add_argument("project", help="Path to the project directory (e.g. MyProjects/ElectionIndustryBeta)")

    # context-pack
    cp = sub.add_parser("context-pack", help="Build a project context pack for an agent")
    cp.add_argument("project", help="Project path (or name, with --no-ingest)")
    cp.add_argument("--format", choices=["md", "json"], default="md", help="Output format")
    cp.add_argument("--no-ingest", action="store_true",
                    help="Read the graph as-is instead of (re)ingesting from disk first")

    # query
    query_p = sub.add_parser("query", help="Run a named Cypher query or GraphRAG search")
    query_p.add_argument("query_name", help=(
        "Query name: wrds-notebooks | stale-deps | deployments | "
        "pipeline-health | agents | stale-impact | rag"
    ))
    query_p.add_argument("question", nargs="?", default="",
                         help="Question text (for 'rag' query type)")

    # agent
    agent_p = sub.add_parser("agent", help="Run an agent: coding | monitoring | orchestration | research")
    agent_p.add_argument("agent_name", help="Agent name")
    agent_p.add_argument("--repo", default="", help="Repo path (coding agent)")
    agent_p.add_argument("--question", default="", help="Question (research agent)")

    # api
    api_p = sub.add_parser("api", help="Start FastAPI server")

    # status
    sub.add_parser("status", help="Show graph node/relationship counts")

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    handlers = {
        "init":    cmd_init,
        "ingest":  cmd_ingest,
        "ingest-project": cmd_ingest_project,
        "context-pack":   cmd_context_pack,
        "query":   cmd_query,
        "agent":   cmd_agent,
        "api":     cmd_api,
        "status":  cmd_status,
    }
    handlers[args.command](args)


if __name__ == "__main__":
    main()
