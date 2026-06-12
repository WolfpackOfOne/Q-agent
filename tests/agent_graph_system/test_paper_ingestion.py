"""Tests for arXiv paper ingestion (#63)."""

from __future__ import annotations

import pytest

from agent_graph_system.ingestion.papers.fetch import (
    ArxivIdParseError,
    RawPaper,
    extract_arxiv_id,
)
from agent_graph_system.ingestion.papers.parser import (
    PaperCard,
    PaperSection,
    _classify_section,
    _summarize,
    split_sections,
)
from agent_graph_system.ontology.provenance import (
    AssertionType,
    SourceKind,
    provenance_from_props,
)


# --- fetch.extract_arxiv_id --------------------------------------------------

@pytest.mark.parametrize(
    "id_or_url,expected",
    [
        ("2401.12345", "2401.12345"),
        ("2401.12345v3", "2401.12345v3"),
        ("arXiv:2401.12345", "2401.12345"),
        ("arxiv:2401.12345", "2401.12345"),
        ("https://arxiv.org/abs/2401.12345", "2401.12345"),
        ("https://arxiv.org/pdf/2401.12345v2.pdf", "2401.12345v2"),
        ("cs.AI/0102001", "cs.AI/0102001"),
    ],
)
def test_extract_arxiv_id_handles_known_formats(id_or_url, expected):
    assert extract_arxiv_id(id_or_url) == expected


def test_extract_arxiv_id_raises_on_unparseable_input():
    with pytest.raises(ArxivIdParseError):
        extract_arxiv_id("not an arxiv id at all")


# --- parser.split_sections / _classify_section / _summarize -----------------

_PAPER_TEXT = """\
Some preamble text before any heading is recognized.

1 Introduction
This paper introduces a new approach. It builds on prior work.

2 Methodology
We use a deterministic method to extract sections. This is the core approach.

3 Limitations
Our method has several limitations and caveats worth discussing.

4 Conclusion
In conclusion, this approach works well for parsing papers.
"""


def test_split_sections_classifies_methodology_and_limitations():
    sections = split_sections(_PAPER_TEXT)
    titles = [s.title for s in sections]
    assert titles == ["Introduction", "Methodology", "Limitations", "Conclusion"]

    by_title = {s.title: s for s in sections}
    assert by_title["Introduction"].kind == "section"
    assert by_title["Methodology"].kind == "methodology"
    assert by_title["Limitations"].kind == "limitations"
    assert by_title["Conclusion"].kind == "section"


def test_split_sections_summary_is_first_sentence():
    sections = split_sections(_PAPER_TEXT)
    by_title = {s.title: s for s in sections}
    assert by_title["Introduction"].summary == "This paper introduces a new approach."


def test_classify_section_keyword_matching():
    assert _classify_section("Methodology") == "methodology"
    assert _classify_section("Our Approach") == "methodology"
    assert _classify_section("Limitations and Future Work") == "limitations"
    assert _classify_section("Background") == "section"


def test_summarize_caps_length_and_collapses_whitespace():
    long_text = ("word " * 100).strip() + "."
    summary = _summarize(long_text, max_len=20)
    assert len(summary) <= 20
    assert "\n" not in summary


def test_summarize_empty_content_returns_empty_string():
    assert _summarize("   \n  ") == ""


# --- graph_writer ------------------------------------------------------------

def _make_card() -> PaperCard:
    return PaperCard(
        arxiv_id="2401.12345",
        title="A Paper About Things",
        authors=("A. Author", "B. Author"),
        abstract="An abstract.",
        published_at=None,
        categories=("q-fin.PM",),
        sections=[
            PaperSection(
                title="Methodology",
                summary="We propose a new method.",
                content="We propose a new method. Details follow.",
                kind="methodology",
            ),
            PaperSection(
                title="Conclusion",
                summary="It works.",
                content="It works well in practice.",
                kind="section",
            ),
        ],
    )


def test_write_card_creates_paper_and_section_nodes():
    from agent_graph_system.graph.local import engine
    from agent_graph_system.ingestion.papers.graph_writer import _write_card

    card = _make_card()
    result = _write_card(card)

    assert result == {
        "arxiv_id": "2401.12345",
        "title": "A Paper About Things",
        "section_count": 2,
        "methodology_count": 1,
        "limitations_count": 0,
    }

    paper = engine._G.nodes["Paper::2401.12345"]
    assert paper["title"] == "A Paper About Things"
    assert paper["authors"] == ["A. Author", "B. Author"]
    paper_prov = provenance_from_props(paper)
    assert paper_prov is not None
    assert paper_prov.source_kind is SourceKind.ARXIV
    assert paper_prov.source_uri == "arxiv:2401.12345"

    section0 = engine._G.nodes["PaperSection::2401.12345_s0"]
    assert section0["title"] == "Methodology"
    assert section0["kind"] == "methodology"
    section_prov = provenance_from_props(section0)
    assert section_prov is not None
    assert section_prov.quote == "We propose a new method."


def test_write_card_links_paper_to_sections_via_has_section():
    from agent_graph_system.graph.local import engine
    from agent_graph_system.ingestion.papers.graph_writer import _write_card

    _write_card(_make_card())

    targets = {
        v for _, v, data in engine._G.out_edges("Paper::2401.12345", data=True)
        if data.get("_type") == "HAS_SECTION"
    }
    assert targets == {"PaperSection::2401.12345_s0", "PaperSection::2401.12345_s1"}


def test_strategy_cites_paper_records_quote_and_page():
    from agent_graph_system.graph.local import engine
    from agent_graph_system.ingestion.papers.graph_writer import (
        _write_card,
        strategy_cites_paper,
    )

    _write_card(_make_card())
    engine.merge_node("Strategy", "name", "MyStrategy")

    strategy_cites_paper(
        "MyStrategy", "2401.12345", quote="key supporting sentence", page=4,
    )

    edge_data = None
    for _, v, data in engine._G.out_edges("Strategy::MyStrategy", data=True):
        if data.get("_type") == "CITES" and v == "Paper::2401.12345":
            edge_data = data
            break
    assert edge_data is not None

    prov = provenance_from_props(edge_data)
    assert prov is not None
    assert prov.source_kind is SourceKind.ARXIV
    assert prov.page == 4
    assert prov.quote == "key supporting sentence"


def test_strategy_cites_paper_can_override_assertion_type():
    from agent_graph_system.graph.local import engine
    from agent_graph_system.ingestion.papers.graph_writer import (
        _write_card,
        strategy_cites_paper,
    )

    _write_card(_make_card())
    engine.merge_node("Strategy", "name", "MyStrategy")
    strategy_cites_paper(
        "MyStrategy", "2401.12345", assertion_type=AssertionType.DECLARED,
    )

    for _, v, data in engine._G.out_edges("Strategy::MyStrategy", data=True):
        if data.get("_type") == "CITES" and v == "Paper::2401.12345":
            prov = provenance_from_props(data)
            assert prov is not None
            assert prov.assertion_type is AssertionType.DECLARED
            return
    pytest.fail("CITES edge not found")


# --- end-to-end ingest_paper (mocked fetch/extract) --------------------------

def test_ingest_paper_end_to_end(monkeypatch):
    from agent_graph_system.graph.local import engine
    from agent_graph_system.ingestion.papers import graph_writer

    raw = RawPaper(
        pdf_bytes=b"%PDF-fake",
        arxiv_id="2401.12345",
        title="A Paper About Things",
        authors=("A. Author",),
        abstract="An abstract.",
        published_at=None,
        categories=("q-fin.PM",),
    )
    card = _make_card()

    monkeypatch.setattr(graph_writer, "fetch_arxiv", lambda id_or_url: raw)
    monkeypatch.setattr(graph_writer, "extract_paper", lambda raw_paper: card)

    result = graph_writer.ingest_paper("2401.12345")

    assert result["arxiv_id"] == "2401.12345"
    assert result["section_count"] == 2
    assert "Paper::2401.12345" in engine._G.nodes
