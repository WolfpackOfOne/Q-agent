"""Standalone tests for latest-backtest selection (#53 sub-issue 3).

The deployment-gate tests exercise the gate with an injected backtest; these
pin down the selection logic itself: recency, validity, linkage, dedup.
"""

from __future__ import annotations

from agent_graph_system.graph.local import engine
from agent_graph_system.graph.neo4j import graph_models as gm


def _bt(run_id, sharpe=1.0, status="completed", **kw):
    gm.upsert_backtest(run_id, name=run_id, sharpe=sharpe, drawdown=-0.1, cagr=0.1)
    if status != "completed" or kw:
        engine.merge_node("Backtest", "run_id", run_id, {"status": status, **kw})


def test_picks_most_recent_by_completed_at():
    gm.upsert_strategy("S", strategy_type="factor")
    _bt("old", completed_at="2026-01-01")
    _bt("new", completed_at="2026-05-01")
    gm.strategy_has_backtest("S", "old")
    gm.strategy_has_backtest("S", "new")

    latest = engine.latest_backtest_for_strategy("S")
    assert latest is not None and latest["run_id"] == "new"


def test_excludes_failed_and_running():
    gm.upsert_strategy("S", strategy_type="factor")
    _bt("good", completed_at="2026-01-01")
    _bt("failed_recent", status="failed", completed_at="2026-09-01")
    _bt("running_recent", status="running", completed_at="2026-09-02")
    gm.strategy_has_backtest("S", "good")
    gm.strategy_has_backtest("S", "failed_recent")
    gm.strategy_has_backtest("S", "running_recent")

    latest = engine.latest_backtest_for_strategy("S")
    assert latest is not None and latest["run_id"] == "good"


def test_links_via_strategy_property_without_edge():
    # A backtest carrying a `strategy` property is found even with no edge.
    _bt("orphan", completed_at="2026-03-01")
    engine.merge_node("Backtest", "run_id", "orphan", {"strategy": "S"})
    latest = engine.latest_backtest_for_strategy("S")
    assert latest is not None and latest["run_id"] == "orphan"


def test_returns_none_when_no_valid_backtest():
    gm.upsert_strategy("S", strategy_type="factor")
    _bt("nope", status="failed", completed_at="2026-01-01")
    gm.strategy_has_backtest("S", "nope")
    assert engine.latest_backtest_for_strategy("S") is None


def test_returns_none_for_unknown_strategy():
    assert engine.latest_backtest_for_strategy("Ghost") is None
