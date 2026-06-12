"""Deterministic paper-section extraction.

v1 is intentionally deterministic (no LLM): split a paper's text into
sections via heading detection, then classify each section as plain
``"section"``, ``"methodology"``, or ``"limitations"`` by keyword matching
on its title. ``extract_paper()``'s signature is kept stable so an
LLM-driven pass can be swapped in later (issue #63).

``pdf_to_text`` lazily imports ``pypdf`` so the rest of this module — and
in particular ``split_sections``, ``_classify_section``, ``_summarize`` —
stays importable and unit-testable without that dependency installed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

from agent_graph_system.ingestion.papers.fetch import RawPaper

_METHODOLOGY_KEYWORDS = ("method", "approach", "model", "methodology")
_LIMITATIONS_KEYWORDS = ("limitation", "caveat", "discussion", "future work")

# Matches numbered/roman-numeral headings ("1 Introduction", "2.1 Approach",
# "IV. Results") as well as common unnumbered section titles.
_HEADING_PATTERN = re.compile(
    r"^\s*(?:(?:\d+(?:\.\d+)*)|(?:[IVXLC]+))[.\s]+(?P<title>[A-Z][A-Za-z0-9 ,\-:']{2,80})\s*$"
    r"|^\s*(?P<plain_title>Abstract|Introduction|Conclusion|References|Acknowledg(?:e)?ments)\s*$",
    re.MULTILINE,
)


@dataclass(slots=True)
class PaperSection:
    """One section of a paper, classified by ``kind``."""

    title: str
    summary: str
    content: str
    kind: str = "section"  # "section" | "methodology" | "limitations"


@dataclass(slots=True)
class PaperCard:
    """Structured representation of a paper, ready for graph_writer."""

    arxiv_id: str
    title: str
    authors: tuple[str, ...]
    abstract: str
    published_at: datetime | None
    categories: tuple[str, ...]
    sections: list[PaperSection] = field(default_factory=list)

    @property
    def methodology(self) -> list[PaperSection]:
        return [s for s in self.sections if s.kind == "methodology"]

    @property
    def limitations(self) -> list[PaperSection]:
        return [s for s in self.sections if s.kind == "limitations"]


def split_sections(text: str) -> list[PaperSection]:
    """Split raw paper text into sections by heading detection."""
    matches = list(_HEADING_PATTERN.finditer(text))
    sections: list[PaperSection] = []
    for i, m in enumerate(matches):
        title = (m.group("title") or m.group("plain_title") or "").strip()
        if not title:
            continue
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        sections.append(
            PaperSection(
                title=title,
                summary=_summarize(content),
                content=content,
                kind=_classify_section(title),
            )
        )
    return sections


def _classify_section(title: str) -> str:
    lowered = title.lower()
    if any(k in lowered for k in _METHODOLOGY_KEYWORDS):
        return "methodology"
    if any(k in lowered for k in _LIMITATIONS_KEYWORDS):
        return "limitations"
    return "section"


def _summarize(content: str, max_len: int = 240) -> str:
    """First sentence of ``content``, collapsed to one line and capped."""
    stripped = " ".join(content.split())
    if not stripped:
        return ""
    match = re.search(r"(.+?[.!?])(\s|$)", stripped)
    candidate = match.group(1) if match else stripped
    return candidate[:max_len]


def pdf_to_text(pdf_bytes: bytes) -> str:
    """Extract raw text from a PDF's bytes via ``pypdf``."""
    import io

    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_paper(raw: RawPaper) -> PaperCard:
    """Parse a fetched ``RawPaper`` into a structured ``PaperCard``."""
    text = pdf_to_text(raw.pdf_bytes)
    return PaperCard(
        arxiv_id=raw.arxiv_id,
        title=raw.title,
        authors=raw.authors,
        abstract=raw.abstract,
        published_at=raw.published_at,
        categories=raw.categories,
        sections=split_sections(text),
    )
