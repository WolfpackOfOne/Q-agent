"""ArXiv fetch helper — resolve an id/URL to PDF bytes + metadata.

Adapted from QuantMind's ``quantmind/preprocess/fetch/arxiv.py`` (MIT
licensed): same arXiv-id parsing, reimplemented synchronously and without
the OpenAI Agents SDK dependency to match Q-agent's plain-class ingestion
modules (see ``ingestion/quantconnect/``).

The ``arxiv`` and ``httpx`` packages are imported lazily inside
:func:`fetch_arxiv` so this module — and :func:`extract_arxiv_id` in
particular — stays importable (and unit-testable) without those optional
dependencies installed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone

# Accepts:
#   2401.12345
#   2401.12345v3
#   arXiv:2401.12345
#   http(s)://arxiv.org/abs/2401.12345
#   http(s)://arxiv.org/pdf/2401.12345v2.pdf
#   cs.AI/0102001 (legacy ID format)
_NEW_ID_PATTERN = re.compile(r"\d{4}\.\d{4,5}(?:v\d+)?")
_LEGACY_ID_PATTERN = re.compile(r"[a-z\-]+(?:\.[A-Z]{2})?/\d{7}(?:v\d+)?")

DEFAULT_USER_AGENT = "Q-agent/1.0 (+https://github.com/WolfpackOfOne/Q-agent)"


class ArxivIdParseError(ValueError):
    """Raised when an arXiv id/URL cannot be parsed."""


@dataclass(frozen=True, slots=True)
class RawPaper:
    """PDF bytes plus metadata pulled from arXiv's public API."""

    pdf_bytes: bytes
    arxiv_id: str
    title: str
    authors: tuple[str, ...]
    abstract: str
    published_at: datetime | None
    categories: tuple[str, ...]


def extract_arxiv_id(id_or_url: str) -> str:
    """Pull the canonical arXiv id from a raw user input.

    Returns:
        Canonical id in either modern (``YYMM.NNNNN``) or legacy
        (``archive[.subject]/YYMMNNN``) form, with version suffix preserved
        when present.

    Raises:
        ArxivIdParseError: If no recognizable arXiv id can be extracted.
    """
    candidate = id_or_url.strip()
    for prefix in ("arXiv:", "arxiv:"):
        if candidate.startswith(prefix):
            candidate = candidate[len(prefix):]
    match = _NEW_ID_PATTERN.search(candidate) or _LEGACY_ID_PATTERN.search(candidate)
    if match is None:
        raise ArxivIdParseError(f"could not parse arXiv id from input: {id_or_url!r}")
    return match.group(0)


def fetch_arxiv(id_or_url: str) -> RawPaper:
    """Fetch arXiv metadata and PDF bytes for a single paper.

    Args:
        id_or_url: ArXiv id, ``arXiv:`` prefixed string, or full
            ``arxiv.org`` URL (abs or pdf form).

    Returns:
        ``RawPaper`` with PDF bytes and metadata from the arXiv API.

    Raises:
        ArxivIdParseError: If the id cannot be parsed.
        LookupError: If arXiv has no record for the parsed id, or the
            record has no PDF link.
        httpx.HTTPError: On PDF download failure.
    """
    import arxiv as arxiv_lib
    import httpx

    arxiv_id = extract_arxiv_id(id_or_url)

    client = arxiv_lib.Client()
    search = arxiv_lib.Search(id_list=[arxiv_id])
    results = list(client.results(search))
    if not results:
        raise LookupError(f"arXiv id not found: {arxiv_id!r}")
    result = results[0]

    pdf_url = result.pdf_url
    if not pdf_url:
        raise LookupError(f"arxiv result has no pdf_url for {arxiv_id!r}")

    headers = {"User-Agent": DEFAULT_USER_AGENT}
    response = httpx.get(pdf_url, headers=headers, timeout=60.0, follow_redirects=True)
    response.raise_for_status()

    published_at = result.published
    if published_at is not None and published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)

    return RawPaper(
        pdf_bytes=response.content,
        arxiv_id=arxiv_id,
        title=result.title,
        authors=tuple(str(a) for a in result.authors),
        abstract=result.summary,
        published_at=published_at,
        categories=tuple(str(c) for c in result.categories),
    )
