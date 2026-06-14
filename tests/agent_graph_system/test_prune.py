"""Tests for stale-fact cleanup after merge-only re-ingest (#67).

Covers the shared ``is_current`` staleness check, the papers
``paper_sections`` filtered reader, and the engine's explicit ``prune_stale``
maintenance primitive (dry-run by default, edge-source scoping, shared-node
protection).
"""

from __future__ import annotations

from agent_graph_system.graph.local import engine
from agent_graph_system.graph.local.engine import merge_node, merge_relationship
from agent_graph_system.ingestion.papers.graph_writer import (
    _write_card,
    paper_sections,
    strategy_cites_paper,
)
from agent_graph_system.ingestion.papers.parser import PaperCard, PaperSection
from agent_graph_system.ontology.provenance import Provenance, is_current

RUN1 = "2026-01-01T00:00:00+00:00"
RUN2 = "2026-02-02T00:00:00+00:00"


# --- is_current ---------------------------------------------------------------

def test_is_current_no_marker_disables_filtering():
    assert is_current({"prov_last_seen": RUN1}, None) is True


def test_is_current_unstamped_fact_is_never_stale():
    assert is_current({}, RUN2) is True


def test_is_current_matching_and_older_markers():
    assert is_current({"prov_last_seen": RUN2}, RUN2) is True
    assert is_current({"prov_last_seen": RUN1}, RUN2) is False


# --- prune_stale on a project-shaped graph ------------------------------------

def _ingest_fake_project(project: str, run_ts: str, files: list[str]) -> None:
    """Minimal Project/Strategy/File subgraph the way graph_writer lays it out."""
    prov = Provenance.declared("test_extractor", last_seen=run_ts)
    merge_node("Project", "name", project,
               {"root": f"/tmp/{project}", "last_ingest_run": run_ts}, provenance=prov)
    merge_node("Strategy", "name", project, {"status": "backtesting"}, provenance=prov)
    for rel in files:
        fkey = f"{project}/{rel}"
        fprov = Provenance.extracted("test_extractor", last_seen=run_ts, source_file=rel)
        merge_node("File", "path", fkey, {"project": project, "rel_path": rel},
                   provenance=fprov)
        merge_relationship("Project", "name", project, "CONTAINS",
                           "File", "path", fkey, provenance=fprov)


def test_prune_dry_run_reports_without_mutating():
    _ingest_fake_project("P1", RUN1, ["main.py", "old.py"])
    _ingest_fake_project("P1", RUN2, ["main.py"])  # old.py disappeared

    report = engine.prune_stale(
        ["Project::P1", "Strategy::P1"], RUN2,
        scope_prop="project", scope_value="P1",
    )

    assert report["dry_run"] is True
    assert [e["to"] for e in report["edges"]] == ["File::P1/old.py"]
    assert report["nodes"] == ["File::P1/old.py"]
    # Nothing was actually removed.
    assert "File::P1/old.py" in engine._G.nodes
    assert engine._G.number_of_edges() == 2


def test_prune_apply_removes_stale_facts_and_keeps_current():
    _ingest_fake_project("P1", RUN1, ["main.py", "old.py"])
    _ingest_fake_project("P1", RUN2, ["main.py"])

    report = engine.prune_stale(
        ["Project::P1", "Strategy::P1"], RUN2,
        scope_prop="project", scope_value="P1", apply=True,
    )

    assert report["dry_run"] is False
    assert "File::P1/old.py" not in engine._G.nodes
    assert "File::P1/main.py" in engine._G.nodes
    assert "Project::P1" in engine._G.nodes
    assert engine._G.number_of_edges() == 1  # the current CONTAINS edge


def test_prune_keeps_shared_node_referenced_by_another_project():
    # P1 (run1) and P2 both define the shared Signal "momentum"; P1's re-ingest
    # (run2) no longer defines it. Pruning P1 must drop only P1's DEFINES edge —
    # the Signal node survives because P2 still points at it.
    _ingest_fake_project("P1", RUN1, ["alpha.py"])
    sig_prov = Provenance.extracted("test_extractor", last_seen=RUN1, source_file="alpha.py")
    merge_node("Signal", "name", "momentum", {"project": "P1"}, provenance=sig_prov)
    merge_relationship("File", "path", "P1/alpha.py", "DEFINES",
                       "Signal", "name", "momentum", provenance=sig_prov)

    _ingest_fake_project("P2", "2026-01-15T00:00:00+00:00", ["beta.py"])
    p2_prov = Provenance.extracted("test_extractor",
                                   last_seen="2026-01-15T00:00:00+00:00",
                                   source_file="beta.py")
    merge_relationship("File", "path", "P2/beta.py", "DEFINES",
                       "Signal", "name", "momentum", provenance=p2_prov)

    _ingest_fake_project("P1", RUN2, ["alpha.py"])  # alpha.py kept, signal gone

    engine.prune_stale(
        ["Project::P1", "Strategy::P1"], RUN2,
        scope_prop="project", scope_value="P1", apply=True,
    )

    assert "Signal::momentum" in engine._G.nodes
    defines_sources = {
        u for u, v, d in engine._G.in_edges("Signal::momentum", data=True)
        if d.get("_type") == "DEFINES"
    }
    assert defines_sources == {"File::P2/beta.py"}  # P1's stale edge is gone


def test_prune_never_touches_unstamped_facts():
    _ingest_fake_project("P1", RUN2, ["main.py"])
    # A hand-written fact with no provenance at all.
    merge_node("File", "path", "P1/manual.py", {"project": "P1", "rel_path": "manual.py"})
    merge_relationship("Project", "name", "P1", "CONTAINS",
                       "File", "path", "P1/manual.py")

    report = engine.prune_stale(
        ["Project::P1", "Strategy::P1"], RUN2,
        scope_prop="project", scope_value="P1", apply=True,
    )

    assert report["edges"] == [] and report["nodes"] == []
    assert "File::P1/manual.py" in engine._G.nodes


# --- papers: filtered reader + prune ------------------------------------------

def _card(arxiv_id: str, n_sections: int) -> PaperCard:
    return PaperCard(
        arxiv_id=arxiv_id,
        title="A Paper",
        authors=("A. Author",),
        abstract="An abstract.",
        published_at=None,
        categories=("q-fin.PM",),
        sections=[
            PaperSection(title=f"S{i}", summary=f"Summary {i}.",
                         content=f"Content {i}.", kind="section")
            for i in range(n_sections)
        ],
    )


def test_paper_sections_filters_sections_dropped_by_reingest():
    _write_card(_card("2401.12345", 3))
    result = _write_card(_card("2401.12345", 2))  # revision lost a section

    sections = paper_sections("2401.12345")
    assert [s["title"] for s in sections] == ["S0", "S1"]
    # The summary now agrees with what readers see (the PR #66 review gap).
    assert result["section_count"] == len(sections)
    # ... even though the stale node is still in the graph (merge-only ingest).
    assert "PaperSection::2401.12345_s2" in engine._G.nodes


def test_prune_paper_removes_dropped_sections_but_not_cites():
    _write_card(_card("2401.12345", 3))
    merge_node("Strategy", "name", "MyStrategy")
    strategy_cites_paper("MyStrategy", "2401.12345", quote="useful result")
    _write_card(_card("2401.12345", 2))

    marker = engine.get_node("Paper::2401.12345")["last_ingest_run"]
    report = engine.prune_stale(
        ["Paper::2401.12345"], marker,
        scope_prop="paper", scope_value="2401.12345", apply=True,
    )

    assert report["nodes"] == ["PaperSection::2401.12345_s2"]
    assert "PaperSection::2401.12345_s2" not in engine._G.nodes
    assert "PaperSection::2401.12345_s1" in engine._G.nodes
    # The CITES edge originates outside the paper's scope and predates the
    # re-ingest, but prune must not consider it: only edges whose source is
    # in scope are candidates.
    cites = [
        v for _, v, d in engine._G.out_edges("Strategy::MyStrategy", data=True)
        if d.get("_type") == "CITES"
    ]
    assert cites == ["Paper::2401.12345"]
