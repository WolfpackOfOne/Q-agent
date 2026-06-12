"""Research agent: discovers new relationships in the graph via GraphRAG."""

from __future__ import annotations

import logging
from typing import Any

from agent_graph_system.agents.base_agent import BaseAgent
from agent_graph_system.rag.retriever import graphrag_query, stale_impact_report

log = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    name = "ResearchAgent"
    role = "research"

    def run(
        self, question: str = "", mode: str = "rag", arxiv_id: str = "", **kwargs
    ) -> Any:
        log.info(
            "[ResearchAgent] mode=%s running query: %s",
            mode, question or arxiv_id or "<stale impact>",
        )
        try:
            if mode == "ingest_paper":
                if not arxiv_id:
                    raise ValueError("mode='ingest_paper' requires arxiv_id")
                from agent_graph_system.ingestion.papers.graph_writer import ingest_paper
                result = ingest_paper(arxiv_id)
            elif question:
                result = graphrag_query(question)
            else:
                result = stale_impact_report()
            self._mark_idle()
            return result
        except Exception as exc:
            self._mark_error(str(exc))
            raise
