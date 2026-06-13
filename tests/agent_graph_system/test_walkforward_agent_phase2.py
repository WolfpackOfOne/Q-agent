"""Integration tests for the phase-2 WalkforwardAgent and its automation loop.

Covers the agent in isolation (status transitions, injected returns provider,
single-strategy targeting), the MonitoringAgent → WalkforwardAgent handoff, and
the OrchestrationAgent queuing rule.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from agent_graph_system.agents.monitoring_agent import MonitoringAgent
from agent_graph_system.agents.orchestration_agent import OrchestrationAgent
from agent_graph_system.agents.walkforward_agent import WalkforwardAgent
from agent_graph_system.graph.backend import latest_walkforward_for_strategy
from agent_graph_system.graph.local import engine
from agent_graph_system.graph.neo4j import graph_models as gm


def _series(years: float = 4, mu: float = 0.0012, sigma: float = 0.006, seed: int = 0) -> pd.Series:
    n = int(round(years * 252))
    idx = pd.bdate_range("2018-01-01", periods=n)
    rng = np.random.default_rng(seed)
    return pd.Series(rng.normal(mu, sigma, n), index=idx)


def _windows(n_windows: int = 6, mu: float = 0.0015, sigma: float = 0.006, seed: int = 0) -> list:
    """Genuine per-window OOS return series → a real ``walkforward`` run."""
    rng = np.random.default_rng(seed)
    base = pd.Timestamp("2018-01-01")
    return [
        pd.Series(rng.normal(mu, sigma, 63),
                  index=pd.bdate_range(base + pd.DateOffset(months=4 * i), periods=63))
        for i in range(n_windows)
    ]


def _flag(strategy: str, strategy_type: str = "momentum") -> None:
    """Seed a strategy with a backtest, flagged needs_walkforward."""
    gm.upsert_strategy(strategy, strategy_type=strategy_type, status="needs_walkforward")
    gm.upsert_backtest(f"bt_{strategy}", name=strategy, sharpe=1.1, drawdown=0.1, cagr=0.2)
    gm.strategy_has_backtest(strategy, f"bt_{strategy}")


def _status(strategy: str) -> str:
    return (engine.get_node(f"Strategy::{strategy}") or {})["status"]


# --- status transitions ----------------------------------------------------

def test_agent_validates_significant_strategy():
    _flag("Sig")
    # Provider supplies genuine per-window OOS returns → a real walkforward run.
    agent = WalkforwardAgent(returns_provider=lambda name: _windows(seed=1))
    result = agent.run()

    assert [p["strategy"] for p in result["processed"]] == ["Sig"]
    assert _status("Sig") == "validated"
    wf = latest_walkforward_for_strategy("Sig")
    assert wf is not None and wf["status"] == "completed"
    assert wf["mode"] == "walkforward"
    assert result["processed"][0]["bootstrap_p_value"] <= 0.10


def test_agent_validated_when_bootstrap_disabled():
    _flag("NoBoot")
    agent = WalkforwardAgent(returns_provider=lambda name: _windows(seed=2), bootstrap=False)
    agent.run()

    assert _status("NoBoot") == "validated"
    wf = latest_walkforward_for_strategy("NoBoot")
    assert wf["status"] == "completed"
    assert wf.get("bootstrap_p_value") is None


def test_agent_marks_not_significant():
    _flag("Noise")
    # Zero-mean genuine windows: the bootstrap p-value should miss the bar.
    zero_mean = lambda name: _windows(mu=0.0, sigma=0.01, seed=3)
    agent = WalkforwardAgent(returns_provider=zero_mean)
    agent.run()

    assert _status("Noise") == "not_significant"
    # A completed run is still persisted — the gap is the significance, not the run.
    assert latest_walkforward_for_strategy("Noise")["status"] == "completed"


def test_agent_marks_rolling_holdout_when_only_a_full_series_is_available():
    # The default provider yields a single full-period series → in-sample slicing.
    # That is not OOS validation, so the status must say so (and the gate refuses).
    _flag("RollH")
    agent = WalkforwardAgent(returns_provider=lambda name: _series(seed=8))
    result = agent.run()

    assert _status("RollH") == "walkforward_not_oos"
    assert result["processed"][0]["mode"] == "rolling_holdout"
    assert latest_walkforward_for_strategy("RollH")["mode"] == "rolling_holdout"


def test_agent_marks_insufficient_data():
    _flag("Short")
    agent = WalkforwardAgent(returns_provider=lambda name: _series(years=1.2))
    agent.run()

    assert _status("Short") == "walkforward_insufficient_data"
    # An insufficient_data run never counts as completed, so the gate stays closed.
    assert latest_walkforward_for_strategy("Short") is None


def test_agent_marks_unavailable_when_no_returns():
    _flag("Missing")
    agent = WalkforwardAgent(returns_provider=lambda name: None)
    result = agent.run()

    assert "Missing" in result["unavailable"]
    assert _status("Missing") == "walkforward_unavailable"
    # No run node was written.
    assert not [n for n, _ in engine.nodes("WalkforwardRun")]


# --- scoping ----------------------------------------------------------------

def test_agent_only_processes_flagged_strategies():
    _flag("Flagged")
    # A strategy in normal backtesting state must be left alone.
    gm.upsert_strategy("Idle", strategy_type="momentum", status="backtesting")
    gm.upsert_backtest("bt_Idle", name="Idle", sharpe=1.0, drawdown=0.1, cagr=0.2)
    gm.strategy_has_backtest("Idle", "bt_Idle")

    agent = WalkforwardAgent(returns_provider=lambda name: _windows(seed=4))
    result = agent.run()

    assert [p["strategy"] for p in result["processed"]] == ["Flagged"]
    assert _status("Idle") == "backtesting"


def test_agent_scan_continues_after_one_strategy_fails():
    _flag("Bad")
    _flag("Good")

    def provider(name):
        if name == "Bad":
            raise RuntimeError("provider failed")
        return _windows(seed=9)

    result = WalkforwardAgent(returns_provider=provider, bootstrap=False).run()

    assert result["errors"] == [{"strategy": "Bad", "error": "provider failed"}]
    assert _status("Bad") == "walkforward_error"
    assert [p["strategy"] for p in result["processed"]] == ["Good"]
    assert _status("Good") == "validated"
    assert (engine.get_node("Agent::WalkforwardAgent") or {})["status"] == "idle"


def test_agent_direct_target_failure_reraises():
    _flag("BadDirect")

    def failing_provider(_name):
        raise RuntimeError("failed")

    agent = WalkforwardAgent(returns_provider=failing_provider)

    with pytest.raises(RuntimeError, match="failed"):
        agent.run(strategy="BadDirect")

    assert _status("BadDirect") == "walkforward_error"
    assert (engine.get_node("Agent::WalkforwardAgent") or {})["status"] == "error"


def test_agent_targets_single_strategy_with_explicit_windows():
    # Not flagged, but addressed directly with explicit per-window OOS returns.
    gm.upsert_strategy("OnDemand", strategy_type="momentum", status="backtesting")
    agent = WalkforwardAgent(bootstrap=False)
    result = agent.run(strategy="OnDemand", returns=_windows(seed=5))

    assert [p["strategy"] for p in result["processed"]] == ["OnDemand"]
    assert _status("OnDemand") == "validated"


def test_agent_preserves_strategy_type_on_status_update():
    gm.upsert_strategy("Typed", strategy_type="mean_reversion", status="needs_walkforward")
    gm.upsert_backtest("bt_Typed", name="Typed", sharpe=1.0, drawdown=0.1, cagr=0.2)
    gm.strategy_has_backtest("Typed", "bt_Typed")

    WalkforwardAgent(returns_provider=lambda name: _windows(seed=6), bootstrap=False).run()
    node = engine.get_node("Strategy::Typed")
    assert node["status"] == "validated"
    assert node["strategy_type"] == "mean_reversion"


# --- automation loop --------------------------------------------------------

def test_monitoring_then_walkforward_closes_the_loop():
    # A backtested strategy with no walk-forward run.
    gm.upsert_strategy("Loop", strategy_type="momentum")
    gm.upsert_backtest("bt_Loop", name="Loop", sharpe=1.2, drawdown=0.1, cagr=0.2)
    gm.strategy_has_backtest("Loop", "bt_Loop")

    # MonitoringAgent flags it...
    mon = MonitoringAgent().run()
    assert "Loop" in mon["needs_walkforward"]
    assert _status("Loop") == "needs_walkforward"

    # ...and the WalkforwardAgent picks it up and validates it out of sample.
    WalkforwardAgent(returns_provider=lambda name: _windows(seed=7)).run()
    assert _status("Loop") in {"validated", "not_significant"}
    assert latest_walkforward_for_strategy("Loop")["status"] == "completed"

    # A second monitoring pass no longer flags it (recent completed run).
    assert "Loop" not in MonitoringAgent().run()["needs_walkforward"]


def test_orchestration_queues_walkforward_for_flagged():
    _flag("Queued")
    actions = OrchestrationAgent().run()["actions"]
    assert {"action": "run_walkforward", "target": "Queued"} in actions
