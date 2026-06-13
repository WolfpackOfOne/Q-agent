"""Integration tests: ResearchAgent walk-forward mode against the local graph."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from agent_graph_system.agents.research_agent import ResearchAgent
from agent_graph_system.graph.backend import latest_walkforward_for_strategy
from agent_graph_system.graph.local import engine
from agent_graph_system.graph.neo4j import graph_models as gm


def _series(years: float = 4, mu: float = 0.001, sigma: float = 0.008, seed: int = 0) -> pd.Series:
    n = int(round(years * 252))
    idx = pd.bdate_range("2018-01-01", periods=n)
    rng = np.random.default_rng(seed)
    return pd.Series(rng.normal(mu, sigma, n), index=idx)


def test_walkforward_run_persisted_to_graph():
    gm.upsert_strategy("WF1", strategy_type="momentum")
    payload = ResearchAgent().run(
        mode="walkforward", strategy="WF1", returns=_series(), bootstrap=True
    )

    assert payload["status"] == "completed"
    run_id = payload["run_id"]

    run_node = engine.get_node(f"WalkforwardRun::{run_id}")
    assert run_node is not None
    assert run_node["strategy"] == "WF1"
    assert run_node["n_windows"] >= 4
    assert run_node["bootstrap_p_value"] is not None

    # HAS_WALKFORWARD edge from the strategy.
    rels = [r for r, _, _ in engine.out_relations("Strategy::WF1")]
    assert "HAS_WALKFORWARD" in rels

    # Per-window nodes exist and are linked.
    windows = [n for n, d in engine.nodes("WalkforwardWindow")]
    assert len(windows) == run_node["n_windows"]
    window_rels = [r for r, _, _ in engine.out_relations(f"WalkforwardRun::{run_id}")]
    assert "HAS_WINDOW" in window_rels

    # Backend lookup returns the completed run.
    latest = latest_walkforward_for_strategy("WF1")
    assert latest is not None and latest["run_id"] == run_id


def test_walkforward_validates_existing_backtest():
    gm.upsert_strategy("WF2", strategy_type="momentum")
    gm.upsert_backtest("btX", name="WF2", sharpe=1.2, drawdown=0.1, cagr=0.2)
    gm.strategy_has_backtest("WF2", "btX")

    payload = ResearchAgent().run(mode="walkforward", strategy="WF2", returns=_series())
    run_id = payload["run_id"]
    targets = [
        t for r, t, _ in engine.out_relations(f"WalkforwardRun::{run_id}")
        if r == "VALIDATES"
    ]
    assert "Backtest::btX" in targets


def test_insufficient_data_persists_status_not_raises():
    gm.upsert_strategy("WF3", strategy_type="momentum")
    payload = ResearchAgent().run(
        mode="walkforward", strategy="WF3", returns=_series(years=1.2)
    )
    assert payload["status"] == "insufficient_data"
    # A completed-only lookup ignores it, so the gate still fails closed.
    assert latest_walkforward_for_strategy("WF3") is None


def test_walkforward_requires_strategy_and_returns():
    with pytest.raises(ValueError):
        ResearchAgent().run(mode="walkforward", strategy="", returns=_series())
    with pytest.raises(ValueError):
        ResearchAgent().run(mode="walkforward", strategy="WF4", returns=None)


def test_monitoring_flags_strategy_needing_walkforward():
    from agent_graph_system.agents.monitoring_agent import MonitoringAgent

    # A strategy with a backtest but no walk-forward run should be flagged.
    gm.upsert_strategy("Cov1", strategy_type="momentum")
    gm.upsert_backtest("btc1", name="Cov1", sharpe=1.0, drawdown=0.1, cagr=0.2)
    gm.strategy_has_backtest("Cov1", "btc1")
    # A strategy without any backtest must NOT be flagged.
    gm.upsert_strategy("Cov2", strategy_type="momentum")

    result = MonitoringAgent().run()
    assert "Cov1" in result["needs_walkforward"]
    assert "Cov2" not in result["needs_walkforward"]
    assert engine.get_node("Strategy::Cov1")["status"] == "needs_walkforward"
    assert engine.get_node("Strategy::Cov1")["strategy_type"] == "momentum"


def test_monitoring_does_not_flag_when_walkforward_recent():
    from datetime import datetime, timezone

    from agent_graph_system.agents.monitoring_agent import MonitoringAgent

    gm.upsert_strategy("Cov3", strategy_type="momentum")
    gm.upsert_backtest("btc3", name="Cov3", sharpe=1.0, drawdown=0.1, cagr=0.2)
    gm.strategy_has_backtest("Cov3", "btc3")
    gm.upsert_walkforward_run(
        "wfc3", "Cov3", status="completed",
        created_at=datetime.now(timezone.utc).isoformat(), n_windows=8,
    )
    gm.strategy_has_walkforward("Cov3", "wfc3")

    result = MonitoringAgent().run()
    assert "Cov3" not in result["needs_walkforward"]
