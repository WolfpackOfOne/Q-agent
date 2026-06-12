"""Provenance for graph facts — where a node or edge came from and how much
to trust it.

Agents must be able to tell a hand-declared fact from one parsed out of source
code, derived by a rule, or suggested by a model. Every fact can therefore
carry a small, flat block of provenance metadata:

    extractor       which component asserted the fact
    assertion_type  declared | extracted | inferred | learned
    source_file     file the fact was read from (if any)
    line            line within that file (if any)
    confidence      0.0–1.0 trust score
    source_hash     hash of the source span, for change detection
    observed_at     first time this fact was seen
    last_seen       most recent time this fact was re-observed

Document-derived facts (e.g. paper ingestion) carry an additional, optional
set of fields anchoring the fact to a span of an external source:

    source_kind     SourceKind — code | arxiv | http | doi | local_doc | manual
    source_uri      e.g. "arxiv:2401.12345"
    page            page number within the source, if any
    char_offset     character offset within the page/source, if any
    quote           supporting quote, capped at MAX_QUOTE_LENGTH chars

Provenance keys are stored on nodes/edges under the ``prov_`` prefix so they
never collide with domain properties, and so a single helper
(:func:`provenance_from_props`) can round-trip them back into a
:class:`Provenance`.

The guiding rule (shared with the rules/policy layer): metadata describes, it
does not enforce. A ``learned`` or low-``confidence`` fact must never be treated
as authoritative just because it exists in the graph — see
:func:`is_low_confidence` and the context-pack's separation of authoritative vs
low-confidence facts.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

# Prefix under which provenance is flattened onto node/edge property bags.
PROV_PREFIX = "prov_"

# Facts at or above this confidence are treated as reliable; below it they are
# surfaced separately (e.g. the context-pack's "low-confidence facts" section).
DEFAULT_CONFIDENCE_THRESHOLD = 0.75

# Quotes longer than this are truncated when stored as provenance, mirroring
# QuantMind's `Citation.quote: str = Field(max_length=500)`.
MAX_QUOTE_LENGTH = 500


class AssertionType(str, Enum):
    """How a fact came to be — ordered loosely from most to least trusted."""

    DECLARED = "declared"      # manually declared, or read from a deterministic source
    EXTRACTED = "extracted"    # parsed from source code, notebooks, docs, or config
    INFERRED = "inferred"      # derived by a deterministic rule
    LEARNED = "learned"        # suggested by an LLM or statistical model


class SourceKind(str, Enum):
    """The kind of external source a document-derived fact was read from."""

    CODE = "code"              # source_file/line — existing code-derived behavior
    ARXIV = "arxiv"
    HTTP = "http"
    DOI = "doi"
    LOCAL_DOC = "local_doc"
    MANUAL = "manual"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def source_hash(text: str) -> str:
    """Short, stable hash of a source span for change detection."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


@dataclass(frozen=True)
class Provenance:
    """Where a single graph fact came from and how much to trust it."""

    extractor: str
    assertion_type: AssertionType = AssertionType.EXTRACTED
    source_file: str | None = None
    line: int | None = None
    confidence: float = 1.0
    source_hash: str | None = None
    observed_at: str = field(default_factory=_now_iso)
    last_seen: str = field(default_factory=_now_iso)

    # Document-derived provenance — all optional, additive (#64). These let a
    # fact point at a span of an external source (an arXiv paper, a web page,
    # ...) rather than a line in a source file.
    source_kind: SourceKind | None = None
    source_uri: str | None = None
    page: int | None = None
    char_offset: int | None = None
    quote: str | None = None

    def __post_init__(self) -> None:
        if self.quote is not None and len(self.quote) > MAX_QUOTE_LENGTH:
            # Frozen dataclass: bypass __setattr__ to truncate in place.
            object.__setattr__(self, "quote", self.quote[:MAX_QUOTE_LENGTH])

    # -- convenience constructors -------------------------------------------
    @classmethod
    def declared(cls, extractor: str, **kw: Any) -> Provenance:
        kw.setdefault("confidence", 1.0)
        return cls(extractor=extractor, assertion_type=AssertionType.DECLARED, **kw)

    @classmethod
    def extracted(cls, extractor: str, **kw: Any) -> Provenance:
        return cls(extractor=extractor, assertion_type=AssertionType.EXTRACTED, **kw)

    @classmethod
    def inferred(cls, extractor: str, **kw: Any) -> Provenance:
        return cls(extractor=extractor, assertion_type=AssertionType.INFERRED, **kw)

    @classmethod
    def from_document(
        cls,
        extractor: str,
        *,
        source_kind: SourceKind,
        source_uri: str,
        assertion_type: AssertionType = AssertionType.EXTRACTED,
        page: int | None = None,
        char_offset: int | None = None,
        quote: str | None = None,
        **kw: Any,
    ) -> Provenance:
        """Provenance for a fact extracted from an external document.

        E.g. a ``CITES`` edge written by issue #63's paper ingestion,
        anchored to a page/quote in an arXiv PDF.
        """
        return cls(
            extractor=extractor,
            assertion_type=assertion_type,
            source_kind=source_kind,
            source_uri=source_uri,
            page=page,
            char_offset=char_offset,
            quote=quote,
            **kw,
        )

    # -- serialization ------------------------------------------------------
    def as_props(self) -> dict[str, Any]:
        """Flatten to ``prov_*`` keys suitable for a node/edge property bag.

        ``None`` fields are omitted so they don't clutter the graph.
        """
        props: dict[str, Any] = {
            f"{PROV_PREFIX}extractor": self.extractor,
            f"{PROV_PREFIX}assertion_type": self.assertion_type.value,
            f"{PROV_PREFIX}confidence": float(self.confidence),
            f"{PROV_PREFIX}observed_at": self.observed_at,
            f"{PROV_PREFIX}last_seen": self.last_seen,
        }
        if self.source_file is not None:
            props[f"{PROV_PREFIX}source_file"] = self.source_file
        if self.line is not None:
            props[f"{PROV_PREFIX}line"] = int(self.line)
        if self.source_hash is not None:
            props[f"{PROV_PREFIX}source_hash"] = self.source_hash
        if self.source_kind is not None:
            props[f"{PROV_PREFIX}source_kind"] = self.source_kind.value
        if self.source_uri is not None:
            props[f"{PROV_PREFIX}source_uri"] = self.source_uri
        if self.page is not None:
            props[f"{PROV_PREFIX}page"] = int(self.page)
        if self.char_offset is not None:
            props[f"{PROV_PREFIX}char_offset"] = int(self.char_offset)
        if self.quote is not None:
            props[f"{PROV_PREFIX}quote"] = self.quote
        return props


def provenance_from_props(props: dict[str, Any]) -> Provenance | None:
    """Reconstruct a :class:`Provenance` from a node/edge property bag.

    Returns ``None`` when the bag carries no provenance at all, so callers can
    distinguish "no provenance recorded" from "declared with full confidence".
    """
    if not any(str(k).startswith(PROV_PREFIX) for k in props):
        return None

    def _get(name: str, default: Any = None) -> Any:
        return props.get(f"{PROV_PREFIX}{name}", default)

    raw_type = str(_get("assertion_type", AssertionType.EXTRACTED.value))
    try:
        assertion = AssertionType(raw_type)
    except ValueError:
        assertion = AssertionType.EXTRACTED

    raw_kind = _get("source_kind")
    source_kind: SourceKind | None
    if raw_kind is None:
        source_kind = None
    else:
        try:
            source_kind = SourceKind(str(raw_kind))
        except ValueError:
            source_kind = None

    line = _get("line")
    page = _get("page")
    char_offset = _get("char_offset")
    return Provenance(
        extractor=str(_get("extractor", "unknown")),
        assertion_type=assertion,
        source_file=_get("source_file"),
        line=int(line) if line is not None else None,
        confidence=float(_get("confidence", 1.0)),
        source_hash=_get("source_hash"),
        observed_at=str(_get("observed_at", _now_iso())),
        last_seen=str(_get("last_seen", _now_iso())),
        source_kind=source_kind,
        source_uri=_get("source_uri"),
        page=int(page) if page is not None else None,
        char_offset=int(char_offset) if char_offset is not None else None,
        quote=_get("quote"),
    )


# Optional fields that as_props() omits when None. If a re-observed fact no
# longer carries one of these (e.g. a citation losing its page/quote), the
# stale value must be explicitly cleared rather than left behind by
# existing.update(merged).
_OPTIONAL_PROV_FIELDS = (
    "source_file", "line", "source_hash",
    "source_kind", "source_uri", "page", "char_offset", "quote",
)


def merge_provenance_props(
    existing: dict[str, Any], new_prov: Provenance
) -> dict[str, Any]:
    """Provenance props for a re-observed fact.

    Re-running an extractor should refresh ``last_seen`` while keeping the
    original ``observed_at`` (the fact was first seen earlier). Everything else
    takes the new values. Optional fields present on ``existing`` but absent
    from ``new_prov`` are explicitly set to ``None`` so the merge clears them
    instead of leaving the stale value in place.
    """
    merged = new_prov.as_props()
    prior_observed = existing.get(f"{PROV_PREFIX}observed_at")
    if prior_observed:
        merged[f"{PROV_PREFIX}observed_at"] = prior_observed
    for field_name in _OPTIONAL_PROV_FIELDS:
        prov_key = f"{PROV_PREFIX}{field_name}"
        if prov_key not in merged and prov_key in existing:
            merged[prov_key] = None
    return merged


def is_current(props: dict[str, Any], run_marker: str | None) -> bool:
    """True unless the fact was last seen by an older ingest run.

    ``run_marker`` is the parent's current run stamp — ``last_ingest_run`` on a
    ``Project`` or ``Paper`` node. Read paths use this to filter out facts left
    behind by earlier ingest runs (a deleted file, a dropped paper section).

    Staleness is only asserted positively: a missing ``run_marker`` (legacy
    parent) or a fact with no ``prov_last_seen`` disables filtering rather than
    hiding facts whose provenance was never stamped.
    """
    if run_marker is None:
        return True
    last_seen = props.get(f"{PROV_PREFIX}last_seen")
    return last_seen is None or last_seen == run_marker


def is_low_confidence(
    props: dict[str, Any], threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
) -> bool:
    """True when the fact carries a confidence below ``threshold``.

    Facts with no recorded confidence are treated as reliable (not low),
    matching the ``declared``-by-default reading of legacy facts.
    """
    value = props.get(f"{PROV_PREFIX}confidence")
    if value is None:
        return False
    try:
        return float(value) < threshold
    except (TypeError, ValueError):
        return False
