"""Write a fetched/parsed paper into the knowledge graph.

Node labels:  Paper, PaperSection
Relationships: HAS_SECTION (Paper -> PaperSection), CITES (Strategy -> Paper)

Uses ``merge_node``/``merge_relationship`` directly (see
``ingestion/quantconnect/graph_writer.py`` for the same pattern) — the local
engine's CRUD is label-agnostic, so no changes to ``graph/local/engine.py``
or ``graph/neo4j/graph_models.py`` are needed for new node types.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from agent_graph_system.graph.backend import merge_node, merge_relationship
from agent_graph_system.ingestion.papers.fetch import RawPaper, fetch_arxiv
from agent_graph_system.ingestion.papers.parser import PaperCard, extract_paper
from agent_graph_system.ontology.provenance import Provenance, SourceKind

log = logging.getLogger(__name__)

_EXTRACTOR = "arxiv_paper_extractor"


def ingest_paper(arxiv_id: str) -> dict[str, Any]:
    """Fetch, parse, and write an arXiv paper into the graph.

    Returns a summary dict: ``arxiv_id``, ``title``, ``section_count``,
    ``methodology_count``, ``limitations_count``.
    """
    raw: RawPaper = fetch_arxiv(arxiv_id)
    card: PaperCard = extract_paper(raw)
    return _write_card(card)


def _write_card(card: PaperCard) -> dict[str, Any]:
    run_ts = datetime.now(timezone.utc).isoformat()
    source_uri = f"arxiv:{card.arxiv_id}"

    paper_prov = Provenance.from_document(
        _EXTRACTOR,
        source_kind=SourceKind.ARXIV,
        source_uri=source_uri,
        last_seen=run_ts,
    )
    merge_node(
        "Paper",
        "arxiv_id",
        card.arxiv_id,
        {
            "title": card.title,
            "authors": list(card.authors),
            "abstract": card.abstract,
            "published_at": card.published_at.isoformat() if card.published_at else None,
            "categories": list(card.categories),
            # Run marker, mirroring Project.last_ingest_run: re-ingest is
            # merge-only, so readers (paper_sections) and the prune CLI use
            # this to tell current sections from ones a revision dropped.
            "last_ingest_run": run_ts,
        },
        provenance=paper_prov,
    )

    for i, section in enumerate(card.sections):
        section_id = f"{card.arxiv_id}_s{i}"
        section_prov = Provenance.from_document(
            _EXTRACTOR,
            source_kind=SourceKind.ARXIV,
            source_uri=source_uri,
            quote=section.summary,
            last_seen=run_ts,
        )
        merge_node(
            "PaperSection",
            "section_id",
            section_id,
            {
                "title": section.title,
                "summary": section.summary,
                "content": section.content,
                "kind": section.kind,
                "index": i,
                "paper": card.arxiv_id,
            },
            provenance=section_prov,
        )
        merge_relationship(
            "Paper", "arxiv_id", card.arxiv_id,
            "HAS_SECTION",
            "PaperSection", "section_id", section_id,
            provenance=section_prov,
        )

    return {
        "arxiv_id": card.arxiv_id,
        "title": card.title,
        "section_count": len(card.sections),
        "methodology_count": len(card.methodology),
        "limitations_count": len(card.limitations),
    }


def paper_sections(arxiv_id: str) -> list[dict[str, Any]]:
    """Current sections of an ingested paper, in document order.

    Re-ingest is merge-only, so a re-fetched revision with fewer sections
    leaves the old trailing ``PaperSection`` nodes in the graph. Like the
    project context pack, this reader filters ``HAS_SECTION`` edges to the
    paper's current ``last_ingest_run`` so callers only see sections present
    in the latest fetch. Reads the local backend (Neo4j parity is a known gap).
    """
    from agent_graph_system.graph.local import engine
    from agent_graph_system.ontology.provenance import is_current

    paper = engine.get_node(f"Paper::{arxiv_id}")
    if paper is None:
        return []
    run_marker = paper.get("last_ingest_run")
    sections = [
        engine.get_node(target_id) or {}
        for rel_type, target_id, edge in engine.out_relations(f"Paper::{arxiv_id}")
        if rel_type == "HAS_SECTION" and is_current(edge, run_marker)
    ]
    return sorted(sections, key=lambda s: s.get("index", 0))


def strategy_cites_paper(
    strategy: str,
    arxiv_id: str,
    *,
    quote: str | None = None,
    page: int | None = None,
    **prov_kwargs: Any,
) -> None:
    """Record that ``strategy`` cites the paper ``arxiv_id``.

    ``prov_kwargs`` is forwarded to :meth:`Provenance.from_document` — pass
    ``assertion_type=AssertionType.DECLARED`` for a hand-asserted citation
    versus the default ``EXTRACTED`` for an agent-discovered one.
    """
    prov = Provenance.from_document(
        _EXTRACTOR,
        source_kind=SourceKind.ARXIV,
        source_uri=f"arxiv:{arxiv_id}",
        page=page,
        quote=quote,
        **prov_kwargs,
    )
    merge_relationship(
        "Strategy", "name", strategy,
        "CITES",
        "Paper", "arxiv_id", arxiv_id,
        provenance=prov,
    )
