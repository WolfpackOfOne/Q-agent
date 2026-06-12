"""Tests for the project context pack (#53 sub-issue 6)."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_graph_system.graph import context_pack as cp
from agent_graph_system.graph.local import engine
from agent_graph_system.ingestion.quantconnect import graph_writer
from agent_graph_system.graph.neo4j import graph_models as gm

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FIXTURE = _REPO_ROOT / "MyProjects" / "ElectionIndustryBeta"


def test_raises_for_uningested_project():
    with pytest.raises(cp.ProjectNotInGraph):
        cp.build_context_pack("DoesNotExist")


@pytest.mark.skipif(not _FIXTURE.is_dir(), reason="fixture missing")
def test_pack_has_all_sections():
    graph_writer.ingest_project(_FIXTURE)
    pack = cp.build_context_pack("ElectionIndustryBeta")

    for key in (
        "summary", "important_files", "docs", "datasets", "objectstore",
        "backtest", "signals", "modules", "config_params", "notebooks",
        "known_risks", "low_confidence_facts",
    ):
        assert key in pack

    assert pack["project"] == "ElectionIndustryBeta"
    assert "rolling_beta" in pack["signals"]
    assert any(d.endswith("strategy.md") for d in pack["docs"])
    assert {d["name"] for d in pack["datasets"]} >= {"SPY"}


@pytest.mark.skipif(not _FIXTURE.is_dir(), reason="fixture missing")
def test_recommended_files_prioritise_main_and_docs():
    graph_writer.ingest_project(_FIXTURE)
    pack = cp.build_context_pack("ElectionIndustryBeta")
    important = pack["important_files"]
    assert "main.py" in important
    # main.py should rank ahead of an arbitrary deep doc page.
    assert important.index("main.py") < important.index("docs/strategy.md")


@pytest.mark.skipif(not _FIXTURE.is_dir(), reason="fixture missing")
def test_no_backtest_surfaces_as_risk():
    graph_writer.ingest_project(_FIXTURE)
    pack = cp.build_context_pack("ElectionIndustryBeta")
    # The fixture commits no backtest node, so the gate risk must be flagged.
    assert pack["summary"]["has_completed_backtest"] is False
    assert any("deployment_gate" in r for r in pack["known_risks"])


@pytest.mark.skipif(not _FIXTURE.is_dir(), reason="fixture missing")
def test_backtest_metrics_appear_when_present():
    graph_writer.ingest_project(_FIXTURE)
    # Link a passing backtest, mirroring what a real run would write.
    gm.upsert_backtest("bt_1", name="baseline", sharpe=1.2, drawdown=-0.1, cagr=0.18)
    gm.strategy_has_backtest("ElectionIndustryBeta", "bt_1")

    pack = cp.build_context_pack("ElectionIndustryBeta")
    assert pack["summary"]["has_completed_backtest"] is True
    assert pack["backtest"]["sharpe"] == 1.2
    assert not any("deployment_gate" in r for r in pack["known_risks"])


@pytest.mark.skipif(not _FIXTURE.is_dir(), reason="fixture missing")
def test_low_confidence_facts_listed():
    graph_writer.ingest_project(_FIXTURE)
    pack = cp.build_context_pack("ElectionIndustryBeta")
    # Dynamic ObjectStore keys ingest at low confidence and must be surfaced
    # separately, not silently mixed into authoritative facts.
    assert pack["low_confidence_facts"]
    assert all(float(f["confidence"]) < 0.75 for f in pack["low_confidence_facts"])


def test_re_ingest_drops_stale_facts(tmp_path):
    proj = tmp_path / "Demo"
    proj.mkdir()
    (proj / "main.py").write_text("class DemoAlgo:\n    pass\n")
    (proj / "old_helper.py").write_text("class OldHelper:\n    pass\n")

    graph_writer.ingest_project(proj)
    pack1 = cp.build_context_pack("Demo")
    assert "old_helper.py" in pack1["important_files"]
    assert "OldHelper" in pack1["modules"]

    # Delete the helper and re-ingest: the stale file/module must drop out of
    # the pack even though the writer never deletes graph nodes.
    (proj / "old_helper.py").unlink()
    graph_writer.ingest_project(proj)
    pack2 = cp.build_context_pack("Demo")
    assert "old_helper.py" not in pack2["important_files"]
    assert "OldHelper" not in pack2["modules"]
    assert "main.py" in pack2["important_files"]


@pytest.mark.skipif(not _FIXTURE.is_dir(), reason="fixture missing")
def test_render_markdown_contains_headers():
    graph_writer.ingest_project(_FIXTURE)
    md = cp.render_markdown(cp.build_context_pack("ElectionIndustryBeta"))
    assert "# Context pack — ElectionIndustryBeta" in md
    assert "## Known risks" in md
    assert "## Low-confidence facts" in md
