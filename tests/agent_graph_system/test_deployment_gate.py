"""Tests that the deployment_gate is actually enforced fail-closed.

These exercise the supported graph API (``graph_models``) end to end against
the local backend, plus the pure policy decision function.
"""

from __future__ import annotations

import pytest

from agent_graph_system.graph.backend import latest_backtest_for_strategy, query
from agent_graph_system.graph.neo4j import graph_models as gm
from agent_graph_system.ontology.policy import (
    PolicyViolation,
    check_deployment_gate,
)


def _seed_strategy_with_backtest(strategy="S1", sharpe=0.9, run_id="bt1", **bt_props):
    gm.upsert_strategy(strategy, strategy_type="momentum")
    gm.upsert_backtest(run_id, name=strategy, sharpe=sharpe, drawdown=0.1, cagr=0.2, **bt_props)
    gm.strategy_has_backtest(strategy, run_id)


def _seed_walkforward(strategy, run_id="wf1", p_value=0.02, status="completed",
                      backtest_run_id="bt1"):
    """Seed a completed walk-forward run validating ``backtest_run_id``.

    The VALIDATES edge is what the gate now keys off — a run must validate the
    exact backtest being gated.
    """
    gm.upsert_walkforward_run(
        run_id, strategy, status=status, bootstrap_p_value=p_value,
        created_at="2026-05-01T00:00:00", n_windows=8,
    )
    gm.strategy_has_walkforward(strategy, run_id)
    if backtest_run_id:
        gm.walkforward_validates_backtest(run_id, backtest_run_id)


def _active_deploy_envs(strategy):
    return [d for d in query("MATCH (s:Strategy)-[r:DEPLOYS_TO]->(a:API) RETURN r")
            if d.get("strategy") == strategy]


# --- pure policy decision -------------------------------------------------

def test_gate_passes_with_high_sharpe():
    decision = check_deployment_gate(
        "S1", "live",
        latest_backtest={"run_id": "bt1", "sharpe": 0.9},
        latest_walkforward={"run_id": "wf1", "bootstrap_p_value": 0.02},
    )
    assert decision.allowed is True
    assert decision.code == "DEPLOYMENT_GATE_PASSED"


# --- walk-forward second-bar checks ---------------------------------------

def test_gate_blocked_when_no_walkforward():
    # High Sharpe backtest, but no walk-forward run (empty graph) → fail closed.
    decision = check_deployment_gate(
        "Unknown", "live", latest_backtest={"run_id": "bt1", "sharpe": 0.9}
    )
    assert decision.allowed is False
    assert decision.code == "NO_WALKFORWARD"


def test_gate_blocked_when_not_significant():
    decision = check_deployment_gate(
        "S1", "live",
        latest_backtest={"run_id": "bt1", "sharpe": 0.9},
        latest_walkforward={"run_id": "wf1", "bootstrap_p_value": 0.15},
    )
    assert decision.allowed is False
    assert decision.code == "NOT_SIGNIFICANT"


def test_gate_allowed_when_significant():
    decision = check_deployment_gate(
        "S1", "live",
        latest_backtest={"run_id": "bt1", "sharpe": 0.9},
        latest_walkforward={"run_id": "wf1", "bootstrap_p_value": 0.03},
    )
    assert decision.allowed is True
    assert decision.code == "DEPLOYMENT_GATE_PASSED"


def test_gate_blocked_when_walkforward_validates_a_different_backtest():
    # The run validated an older backtest; it must not green-light a newer one.
    decision = check_deployment_gate(
        "S1", "live",
        latest_backtest={"run_id": "bt_new", "sharpe": 0.9},
        latest_walkforward={"run_id": "wf1", "bootstrap_p_value": 0.02,
                            "validates_backtest": "bt_old"},
    )
    assert decision.allowed is False
    assert decision.code == "NO_WALKFORWARD"


def test_gate_blocked_when_pvalue_is_nan():
    decision = check_deployment_gate(
        "S1", "live",
        latest_backtest={"run_id": "bt1", "sharpe": 0.9},
        latest_walkforward={"run_id": "wf1", "bootstrap_p_value": float("nan")},
    )
    assert decision.allowed is False
    assert decision.code == "INVALID_PVALUE"


def test_gate_blocked_when_pvalue_unparseable():
    decision = check_deployment_gate(
        "S1", "live",
        latest_backtest={"run_id": "bt1", "sharpe": 0.9},
        latest_walkforward={"run_id": "wf1", "bootstrap_p_value": "not-a-number"},
    )
    assert decision.allowed is False
    assert decision.code == "INVALID_PVALUE"


def test_gate_allowed_when_walkforward_has_no_pvalue():
    # bootstrap skipped → no p-value → presence of the run satisfies the bar.
    decision = check_deployment_gate(
        "S1", "live",
        latest_backtest={"run_id": "bt1", "sharpe": 0.9},
        latest_walkforward={"run_id": "wf1", "bootstrap_p_value": None},
    )
    assert decision.allowed is True
    assert decision.code == "DEPLOYMENT_GATE_PASSED"


def test_walkforward_not_checked_until_backtest_passes():
    # A sub-threshold Sharpe is denied at the backtest bar, before walk-forward.
    decision = check_deployment_gate(
        "S1", "live",
        latest_backtest={"run_id": "bt1", "sharpe": 0.1},
        latest_walkforward={"run_id": "wf1", "bootstrap_p_value": 0.01},
    )
    assert decision.allowed is False
    assert decision.code == "DEPLOYMENT_GATE_FAILED"


def test_gate_fails_with_low_sharpe():
    decision = check_deployment_gate(
        "S1", "live", latest_backtest={"run_id": "bt1", "sharpe": 0.42}
    )
    assert decision.allowed is False
    assert decision.code == "DEPLOYMENT_GATE_FAILED"
    assert decision.evidence[0]["value"] == 0.42


def test_gate_fails_closed_with_no_backtest():
    decision = check_deployment_gate("Unknown", "live", latest_backtest=None)
    assert decision.allowed is False
    assert decision.code == "MISSING_BACKTEST"


def test_gate_fails_closed_with_non_numeric_sharpe():
    decision = check_deployment_gate(
        "S1", "live", latest_backtest={"run_id": "bt1", "sharpe": None}
    )
    assert decision.allowed is False
    assert decision.code == "MISSING_BACKTEST"


def test_paper_environment_is_not_gated():
    decision = check_deployment_gate("Unknown", "paper", latest_backtest=None)
    assert decision.allowed is True
    assert decision.code == "NOT_LIVE"


# --- end to end through the supported write API ---------------------------

def test_live_deploy_allowed_when_gate_passes():
    _seed_strategy_with_backtest("S1", sharpe=1.5)
    _seed_walkforward("S1", p_value=0.02)
    gm.merge_node("API", "name", "AlpacaLive")
    gm.strategy_deploys_to("S1", "AlpacaLive", environment="live")
    assert _active_deploy_envs("S1"), "expected a DEPLOYS_TO edge to be written"


def test_live_deploy_blocked_when_no_walkforward():
    # Passing backtest but no walk-forward run → blocked at the second bar.
    _seed_strategy_with_backtest("S8", sharpe=1.5)
    gm.merge_node("API", "name", "AlpacaLive")
    with pytest.raises(PolicyViolation) as exc:
        gm.strategy_deploys_to("S8", "AlpacaLive", environment="live")
    assert exc.value.decision.code == "NO_WALKFORWARD"
    assert not _active_deploy_envs("S8")


def test_live_deploy_blocked_when_not_significant():
    _seed_strategy_with_backtest("S9", sharpe=1.5)
    _seed_walkforward("S9", p_value=0.20)
    gm.merge_node("API", "name", "AlpacaLive")
    with pytest.raises(PolicyViolation) as exc:
        gm.strategy_deploys_to("S9", "AlpacaLive", environment="live")
    assert exc.value.decision.code == "NOT_SIGNIFICANT"
    assert not _active_deploy_envs("S9")


def test_live_deploy_blocked_when_gate_fails():
    _seed_strategy_with_backtest("S2", sharpe=0.1)
    gm.merge_node("API", "name", "AlpacaLive")
    with pytest.raises(PolicyViolation) as exc:
        gm.strategy_deploys_to("S2", "AlpacaLive", environment="live")
    assert exc.value.decision.code == "DEPLOYMENT_GATE_FAILED"
    assert not _active_deploy_envs("S2"), "no edge should be written on denial"


def test_live_deploy_blocked_when_no_backtest():
    gm.upsert_strategy("S3", strategy_type="momentum")
    gm.merge_node("API", "name", "AlpacaLive")
    with pytest.raises(PolicyViolation) as exc:
        gm.strategy_deploys_to("S3", "AlpacaLive", environment="live")
    assert exc.value.decision.code == "MISSING_BACKTEST"
    assert not _active_deploy_envs("S3")


def test_paper_deploy_allowed_without_backtest():
    gm.upsert_strategy("S4", strategy_type="momentum")
    gm.merge_node("API", "name", "AlpacaPaper")
    gm.strategy_deploys_to("S4", "AlpacaPaper", environment="paper")
    assert _active_deploy_envs("S4")


def test_enforce_gate_false_bypasses_check():
    gm.upsert_strategy("S5", strategy_type="momentum")
    gm.merge_node("API", "name", "AlpacaLive")
    # Trusted backfill path: no backtest, but explicitly bypassed.
    gm.strategy_deploys_to("S5", "AlpacaLive", environment="live", enforce_gate=False)
    assert _active_deploy_envs("S5")


# --- latest-backtest selection --------------------------------------------

def test_failed_backtest_is_ignored():
    gm.upsert_strategy("S6", strategy_type="momentum")
    gm.upsert_backtest("bt_fail", name="S6", sharpe=2.0, drawdown=0.1, cagr=0.3, status="failed")
    gm.strategy_has_backtest("S6", "bt_fail")
    assert latest_backtest_for_strategy("S6") is None


def test_latest_backtest_selected_by_timestamp():
    gm.upsert_strategy("S7", strategy_type="momentum")
    gm.upsert_backtest("old", name="S7", sharpe=0.1, drawdown=0.1, cagr=0.1,
                       completed_at="2026-01-01T00:00:00")
    gm.upsert_backtest("new", name="S7", sharpe=1.9, drawdown=0.1, cagr=0.1,
                       completed_at="2026-05-01T00:00:00")
    gm.strategy_has_backtest("S7", "old")
    gm.strategy_has_backtest("S7", "new")
    latest = latest_backtest_for_strategy("S7")
    assert latest is not None
    assert latest["run_id"] == "new"
    # And the gate should pass on the newer, higher-Sharpe backtest once a
    # significant walk-forward run validates *that* backtest out of sample.
    _seed_walkforward("S7", p_value=0.02, backtest_run_id="new")
    gm.merge_node("API", "name", "AlpacaLive")
    gm.strategy_deploys_to("S7", "AlpacaLive", environment="live")
    assert _active_deploy_envs("S7")


def test_live_deploy_blocked_when_only_an_older_backtest_is_validated():
    # A new passing backtest is added, but the only walk-forward run validates
    # the OLD backtest — the gate must not deploy on the unvalidated new one.
    gm.upsert_strategy("S10", strategy_type="momentum")
    gm.upsert_backtest("old10", name="S10", sharpe=1.5, drawdown=0.1, cagr=0.2,
                       completed_at="2026-01-01T00:00:00")
    gm.upsert_backtest("new10", name="S10", sharpe=1.6, drawdown=0.1, cagr=0.2,
                       completed_at="2026-05-01T00:00:00")
    gm.strategy_has_backtest("S10", "old10")
    gm.strategy_has_backtest("S10", "new10")
    # Walk-forward validates only the older backtest.
    _seed_walkforward("S10", p_value=0.01, backtest_run_id="old10")
    gm.merge_node("API", "name", "AlpacaLive")
    with pytest.raises(PolicyViolation) as exc:
        gm.strategy_deploys_to("S10", "AlpacaLive", environment="live")
    assert exc.value.decision.code == "NO_WALKFORWARD"
    assert not _active_deploy_envs("S10")
