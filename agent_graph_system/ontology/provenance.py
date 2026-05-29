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


class AssertionType(str, Enum):
    """How a fact came to be — ordered loosely from most to least trusted."""

    DECLARED = "declared"      # manually declared, or read from a deterministic source
    EXTRACTED = "extracted"    # parsed from source code, notebooks, docs, or config
    INFERRED = "inferred"      # derived by a deterministic rule
    LEARNED = "learned"        # suggested by an LLM or statistical model


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

    line = _get("line")
    return Provenance(
        extractor=str(_get("extractor", "unknown")),
        assertion_type=assertion,
        source_file=_get("source_file"),
        line=int(line) if line is not None else None,
        confidence=float(_get("confidence", 1.0)),
        source_hash=_get("source_hash"),
        observed_at=str(_get("observed_at", _now_iso())),
        last_seen=str(_get("last_seen", _now_iso())),
    )


def merge_provenance_props(
    existing: dict[str, Any], new_prov: Provenance
) -> dict[str, Any]:
    """Provenance props for a re-observed fact.

    Re-running an extractor should refresh ``last_seen`` while keeping the
    original ``observed_at`` (the fact was first seen earlier). Everything else
    takes the new values.
    """
    merged = new_prov.as_props()
    prior_observed = existing.get(f"{PROV_PREFIX}observed_at")
    if prior_observed:
        merged[f"{PROV_PREFIX}observed_at"] = prior_observed
    return merged


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
