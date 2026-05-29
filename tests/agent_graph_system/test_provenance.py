"""Tests for graph-fact provenance (#53 sub-issue 4)."""

from __future__ import annotations

import pytest

from agent_graph_system.ontology.provenance import (
    PROV_PREFIX,
    AssertionType,
    Provenance,
    is_low_confidence,
    merge_provenance_props,
    provenance_from_props,
    source_hash,
)


def test_as_props_roundtrips_through_from_props():
    prov = Provenance(
        extractor="quantconnect_project_extractor",
        assertion_type=AssertionType.EXTRACTED,
        source_file="MyProjects/Example/main.py",
        line=42,
        confidence=0.9,
        source_hash="abc123",
    )
    props = prov.as_props()
    # Flattened under the prov_ prefix, nothing bare.
    assert all(k.startswith(PROV_PREFIX) for k in props)
    restored = provenance_from_props(props)
    assert restored == prov


def test_optional_fields_are_omitted_when_none():
    props = Provenance(extractor="x").as_props()
    assert f"{PROV_PREFIX}source_file" not in props
    assert f"{PROV_PREFIX}line" not in props
    assert f"{PROV_PREFIX}source_hash" not in props
    # Required-ish fields are always present.
    assert props[f"{PROV_PREFIX}extractor"] == "x"
    assert props[f"{PROV_PREFIX}assertion_type"] == "extracted"


def test_from_props_returns_none_without_provenance():
    assert provenance_from_props({"name": "Foo", "status": "live"}) is None


def test_declared_distinct_from_extracted():
    declared = Provenance.declared("manual")
    extracted = Provenance.extracted("python_ast_extractor", confidence=0.8)
    assert declared.assertion_type is AssertionType.DECLARED
    assert extracted.assertion_type is AssertionType.EXTRACTED
    # The distinction survives serialization — agents can filter on it.
    assert declared.as_props()[f"{PROV_PREFIX}assertion_type"] == "declared"
    assert extracted.as_props()[f"{PROV_PREFIX}assertion_type"] == "extracted"


def test_unknown_assertion_type_falls_back_to_extracted():
    restored = provenance_from_props({f"{PROV_PREFIX}assertion_type": "bogus"})
    assert restored is not None
    assert restored.assertion_type is AssertionType.EXTRACTED


def test_merge_preserves_observed_at_and_bumps_last_seen():
    first = Provenance(
        extractor="x", observed_at="2026-01-01T00:00:00+00:00",
        last_seen="2026-01-01T00:00:00+00:00",
    )
    existing = first.as_props()
    second = Provenance(
        extractor="x", observed_at="2026-05-01T00:00:00+00:00",
        last_seen="2026-05-01T00:00:00+00:00",
    )
    merged = merge_provenance_props(existing, second)
    # observed_at stays at the original; last_seen advances.
    assert merged[f"{PROV_PREFIX}observed_at"] == "2026-01-01T00:00:00+00:00"
    assert merged[f"{PROV_PREFIX}last_seen"] == "2026-05-01T00:00:00+00:00"


def test_merge_into_empty_keeps_new_observed_at():
    prov = Provenance(extractor="x", observed_at="2026-05-01T00:00:00+00:00")
    merged = merge_provenance_props({}, prov)
    assert merged[f"{PROV_PREFIX}observed_at"] == "2026-05-01T00:00:00+00:00"


@pytest.mark.parametrize(
    "confidence,expected",
    [(0.5, True), (0.74, True), (0.75, False), (0.99, False), (1.0, False)],
)
def test_is_low_confidence(confidence, expected):
    props = Provenance(extractor="x", confidence=confidence).as_props()
    assert is_low_confidence(props) is expected


def test_is_low_confidence_false_when_unrecorded():
    # Legacy facts with no provenance are treated as reliable.
    assert is_low_confidence({"name": "Foo"}) is False


def test_source_hash_is_stable_and_short():
    h1 = source_hash("hello world")
    h2 = source_hash("hello world")
    assert h1 == h2
    assert len(h1) == 12
    assert source_hash("different") != h1


# --- engine write-path integration (uses autouse clean_graph fixture) -------

def test_merge_node_persists_provenance():
    from agent_graph_system.graph.local import engine

    prov = Provenance.extracted("python_ast_extractor", source_file="a.py", line=3, confidence=0.8)
    engine.merge_node("Signal", "name", "event_tilt", {"kind": "pure"}, provenance=prov)

    data = engine._G.nodes["Signal::event_tilt"]
    assert data["kind"] == "pure"                      # domain prop preserved
    restored = provenance_from_props(data)
    assert restored is not None
    assert restored.extractor == "python_ast_extractor"
    assert restored.assertion_type is AssertionType.EXTRACTED
    assert restored.confidence == 0.8


def test_merge_node_without_provenance_unchanged():
    from agent_graph_system.graph.local import engine

    engine.merge_node("Project", "name", "Example", {"status": "active"})
    data = engine._G.nodes["Project::Example"]
    assert provenance_from_props(data) is None         # no prov_* keys added


def test_re_ingest_preserves_observed_at():
    from agent_graph_system.graph.local import engine

    first = Provenance.extracted("x", observed_at="2026-01-01T00:00:00+00:00",
                                 last_seen="2026-01-01T00:00:00+00:00")
    engine.merge_node("File", "path", "main.py", provenance=first)
    again = Provenance.extracted("x", observed_at="2026-05-01T00:00:00+00:00",
                                 last_seen="2026-05-01T00:00:00+00:00")
    engine.merge_node("File", "path", "main.py", provenance=again)

    data = engine._G.nodes["File::main.py"]
    assert data[f"{PROV_PREFIX}observed_at"] == "2026-01-01T00:00:00+00:00"
    assert data[f"{PROV_PREFIX}last_seen"] == "2026-05-01T00:00:00+00:00"


def test_merge_relationship_persists_provenance():
    from agent_graph_system.graph.local import engine

    engine.merge_node("Project", "name", "Example")
    engine.merge_node("File", "path", "main.py")
    prov = Provenance.extracted("quantconnect_project_extractor", confidence=0.95)
    engine.merge_relationship(
        "Project", "name", "Example", "CONTAINS", "File", "path", "main.py",
        provenance=prov,
    )

    _, _, data = next(iter(engine._G.edges(data=True)))
    assert data["_type"] == "CONTAINS"
    restored = provenance_from_props(data)
    assert restored is not None and restored.confidence == 0.95
