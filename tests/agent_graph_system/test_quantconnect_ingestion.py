"""Golden-fixture tests for MyProjects/ ingestion (#53 sub-issue 5).

Ingests the real ElectionIndustryBeta project and asserts the graph it
produces is useful and provenance-stamped.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_graph_system.graph.local import engine
from agent_graph_system.ingestion.quantconnect import graph_writer, parser
from agent_graph_system.ontology.provenance import PROV_PREFIX, provenance_from_props

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FIXTURE = _REPO_ROOT / "MyProjects" / "ElectionIndustryBeta"

pytestmark = pytest.mark.skipif(
    not _FIXTURE.is_dir(), reason="ElectionIndustryBeta fixture not present"
)


# --- pure parser ------------------------------------------------------------

def test_parser_finds_structure():
    inv = parser.parse_project(_FIXTURE)
    assert inv["project"] == "ElectionIndustryBeta"
    # Docs include the agent files and docs/ pages.
    assert "AGENTS.md" in inv["docs"] and "claude.md" in inv["docs"]
    assert any(d.startswith("docs/") for d in inv["docs"])
    # The pure signal atoms are detected as signals, not modules.
    signal_names = {s["name"] for s in inv["signals"]}
    assert {"rolling_beta", "top_bottom_k_betaweighted"} <= signal_names
    # Classes show up as modules.
    module_names = {m["name"] for m in inv["modules"]}
    assert "ElectionBetaAlpha" in module_names and "PortfolioLogger" in module_names
    # Bundled data file detected.
    assert "data/trump_prob.csv" in inv["data_files"]


def test_parser_resolves_const_and_flags_dynamic():
    inv = parser.parse_project(_FIXTURE)
    # SPY resolved from the BENCHMARK constant (heuristic confidence).
    spy = [s for s in inv["subscriptions"] if s["ticker"] == "SPY"]
    assert spy and spy[0]["confidence"] == parser.CONF_HEURISTIC
    # The loop-variable subscription is honestly flagged low-confidence.
    dynamic = [s for s in inv["subscriptions"] if s["ticker"] is None]
    assert dynamic and all(s["confidence"] == parser.CONF_DYNAMIC for s in dynamic)


# --- graph writer (autouse clean_graph fixture isolates the graph) ----------

def test_ingest_writes_expected_nodes():
    summary = graph_writer.ingest_project(_FIXTURE)
    assert summary["project"] == "ElectionIndustryBeta"
    c = summary["counts"]
    assert c["files"] >= 15
    assert c["docs"] == 6
    assert c["signals"] == 2
    assert c["modules"] >= 5

    g = engine._G
    assert "Project::ElectionIndustryBeta" in g
    # Project is also a Strategy, so the deployment-gate lineage applies.
    assert "Strategy::ElectionIndustryBeta" in g
    assert "Signal::rolling_beta" in g
    assert "ConfigParam::ElectionIndustryBeta.LOOKBACK" in g
    # SPY dataset + USES edge from the strategy.
    assert "Dataset::SPY" in g


def test_ingest_relationships():
    graph_writer.ingest_project(_FIXTURE)
    g = engine._G

    def edge_types(src):
        return {d.get("_type") for _, _, d in g.out_edges(src, data=True)}

    assert "CONTAINS" in edge_types("Project::ElectionIndustryBeta")
    assert "HAS_DOC" in edge_types("Project::ElectionIndustryBeta")
    assert "USES" in edge_types("Strategy::ElectionIndustryBeta")
    # main.py reads the bundled trump_prob.csv from the ObjectStore.
    assert "ObjectStoreKey::data/trump_prob.csv" in g


def test_ingested_facts_carry_provenance():
    graph_writer.ingest_project(_FIXTURE)
    g = engine._G

    # An extracted module fact has full provenance with source file + line.
    alpha = g.nodes["Module::ElectionIndustryBeta.ElectionBetaAlpha"]
    prov = provenance_from_props(alpha)
    assert prov is not None
    assert prov.extractor == "quantconnect_project_extractor"
    assert prov.source_file == "models/alpha.py"
    assert prov.line and prov.line > 0

    # The Project node is *declared*, not extracted.
    proj = g.nodes["Project::ElectionIndustryBeta"]
    assert proj[f"{PROV_PREFIX}assertion_type"] == "declared"


def test_low_confidence_facts_exist_and_are_flagged():
    graph_writer.ingest_project(_FIXTURE)
    g = engine._G
    # The dynamic ObjectStore key(s) from the logger are recorded but flagged
    # low-confidence so they never masquerade as authoritative.
    low = [
        n for n, d in g.nodes(data=True)
        if d.get("_label") == "ObjectStoreKey" and float(d.get(f"{PROV_PREFIX}confidence", 1.0)) < 0.75
    ]
    assert low, "expected at least one low-confidence (dynamic) ObjectStore key"


def test_re_ingest_is_idempotent_on_node_count():
    first = graph_writer.ingest_project(_FIXTURE)
    n_after_first = engine._G.number_of_nodes()
    second = graph_writer.ingest_project(_FIXTURE)
    n_after_second = engine._G.number_of_nodes()
    assert first["counts"] == second["counts"]
    assert n_after_first == n_after_second  # merge, not duplicate


def _make_project(root: Path, name: str, ticker: str) -> Path:
    proj = root / name
    proj.mkdir(parents=True)
    (proj / "main.py").write_text(
        f"class {name}Algo:\n    def Initialize(self):\n        self.AddEquity('{ticker}')\n"
    )
    (proj / "AGENTS.md").write_text(f"# {name}\n")
    return proj


def test_two_projects_do_not_share_file_nodes(tmp_path):
    # Both projects have a main.py and AGENTS.md at the same relative paths.
    proj_a = _make_project(tmp_path, "Alpha", "AAA")
    proj_b = _make_project(tmp_path, "Beta", "BBB")
    graph_writer.ingest_project(proj_a)
    graph_writer.ingest_project(proj_b)
    g = engine._G

    # Each project's File nodes must be distinct, not merged onto File::main.py.
    def contained_files(project: str) -> set[str]:
        out = set()
        for _, v, d in g.out_edges(f"Project::{project}", data=True):
            node = g.nodes.get(v, {})
            if node.get("_label") == "File":
                out.add(node.get("rel_path", node.get("path")))
                # the node must belong to the project that contains it
                assert node.get("project") == project, (
                    f"{v} contained by {project} but tagged {node.get('project')}"
                )
        return out

    assert contained_files("Alpha") == {"main.py", "AGENTS.md"}
    assert contained_files("Beta") == {"main.py", "AGENTS.md"}
    # And there is no single shared File::main.py node both point at.
    main_nodes = [n for n, d in g.nodes(data=True)
                  if d.get("_label") == "File" and d.get("rel_path") == "main.py"]
    assert len(main_nodes) == 2
