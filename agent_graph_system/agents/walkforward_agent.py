"""Walk-forward agent: closes the validation loop for backtested strategies.

Phase 2 of issue #62. The pipeline this completes:

    LEAN backtest completes
      → MonitoringAgent sees a Backtest with no recent WalkforwardRun,
        sets Strategy.status = "needs_walkforward"
      → WalkforwardAgent (this) picks it up, fetches a return series, runs the
        walk-forward + bootstrap via the ResearchAgent, writes the WalkforwardRun
      → sets Strategy.status to "validated" / "not_significant" /
        "walkforward_insufficient_data" / "walkforward_unavailable"
      → deployment gate reads the WalkforwardRun before any live deploy

The heavy lifting (analysis, persistence, provenance) lives in the ResearchAgent
walk-forward path; this agent only orchestrates *which* strategies get run and
*where their returns come from*. Returns sourcing is injectable so the agent is
unit-testable without touching disk, and so a richer provider (yfinance/WRDS
auto-fetch, ObjectStore) can be slotted in later without changing this class.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable

from agent_graph_system.agents.base_agent import BaseAgent
from agent_graph_system.graph.backend import query
from agent_graph_system.graph.neo4j import graph_models as gm

if TYPE_CHECKING:  # avoid importing pandas at module load
    import pandas as pd

log = logging.getLogger(__name__)

# Strategy.status set by MonitoringAgent that marks a strategy as ready for a
# walk-forward run.
NEEDS_WALKFORWARD = "needs_walkforward"

# A provider maps a strategy name to its daily return Series, or None if no
# returns artifact can be found for it.
ReturnsProvider = Callable[[str], "pd.Series | None"]


class WalkforwardAgent(BaseAgent):
    name = "WalkforwardAgent"
    role = "walkforward"

    def __init__(
        self,
        returns_provider: ReturnsProvider | None = None,
        *,
        search_roots: "list | None" = None,
        bootstrap: bool = True,
        train_months: int = 12,
        test_months: int = 3,
        step_months: int = 3,
    ) -> None:
        super().__init__()
        self._search_roots = search_roots
        self._returns_provider = returns_provider or self._default_returns_provider
        self._bootstrap = bootstrap
        self._train_months = train_months
        self._test_months = test_months
        self._step_months = step_months

    # -- public entry point --------------------------------------------------

    def run(self, strategy: str | None = None, returns: "pd.Series | None" = None, **kwargs) -> Any:
        """Process strategies awaiting walk-forward validation.

        With no arguments, scans the graph for every strategy flagged
        ``needs_walkforward`` and processes each. Passing ``strategy`` (and
        optionally an explicit ``returns`` series) processes just that one — used
        by the CLI / orchestration to target a single strategy on demand.
        """
        results: dict[str, Any] = {"processed": [], "unavailable": [], "errors": []}
        try:
            targets = [strategy] if strategy else self._flagged_strategies()
            for name in targets:
                series = returns if (strategy and returns is not None) else self._returns_provider(name)
                if series is None:
                    self._set_status(name, "walkforward_unavailable")
                    results["unavailable"].append(name)
                    log.warning("[WalkforwardAgent] no returns available for %s", name)
                    continue
                outcome = self._validate(name, series)
                results["processed"].append(outcome)
            self._mark_idle()
        except Exception as exc:
            self._mark_error(str(exc))
            raise
        return results

    # -- internals -----------------------------------------------------------

    def _flagged_strategies(self) -> list[str]:
        # Filter status in Python rather than in the query string: the local
        # backend's interpreter routes any query containing "WALKFORWARD" to the
        # WalkforwardRun handler, and the literal 'needs_walkforward' would
        # collide with that guard.
        rows = query("MATCH (s:Strategy) RETURN s.name AS name, s.status AS status")
        return [r["name"] for r in rows if r.get("status") == NEEDS_WALKFORWARD and r.get("name")]

    def _validate(self, strategy: str, returns: "pd.Series") -> dict[str, Any]:
        """Run the walk-forward via the ResearchAgent and update the status."""
        from agent_graph_system.agents.research_agent import ResearchAgent

        payload = ResearchAgent().run(
            mode="walkforward",
            strategy=strategy,
            returns=returns,
            train_months=self._train_months,
            test_months=self._test_months,
            step_months=self._step_months,
            bootstrap=self._bootstrap,
        )
        status = self._status_from_payload(payload)
        self._set_status(strategy, status)
        log.info(
            "[WalkforwardAgent] %s → %s (run %s)",
            strategy, status, payload.get("run_id"),
        )
        return {
            "strategy": strategy,
            "status": status,
            "run_id": payload.get("run_id"),
            "bootstrap_p_value": payload.get("bootstrap_p_value"),
        }

    @staticmethod
    def _status_from_payload(payload: dict) -> str:
        """Translate a walk-forward result into a Strategy.status.

        ``validated`` means a completed run that clears the significance bar (or
        had no bootstrap p-value, i.e. presence alone satisfies the gate, matching
        :func:`ontology.policy.check_deployment_gate`). ``not_significant`` means
        the run completed but the bootstrap p-value missed the threshold.
        """
        from agent_graph_system.ontology.policy import BOOTSTRAP_P_VALUE_THRESHOLD

        if payload.get("status") == "insufficient_data":
            return "walkforward_insufficient_data"
        p_value = payload.get("bootstrap_p_value")
        if p_value is not None and p_value > BOOTSTRAP_P_VALUE_THRESHOLD:
            return "not_significant"
        return "validated"

    def _set_status(self, strategy: str, status: str) -> None:
        gm.upsert_strategy(strategy, strategy_type=self._strategy_type(strategy), status=status)

    @staticmethod
    def _strategy_type(name: str) -> str:
        """Preserve an existing strategy's type when re-upserting its status."""
        from agent_graph_system.graph.local import engine
        node = engine.get_node(f"Strategy::{name}") or {}
        return node.get("strategy_type", "unknown")

    def _default_returns_provider(self, strategy: str) -> "pd.Series | None":
        from agent_graph_system.analysis.returns import discover_returns
        return discover_returns(strategy, self._search_roots)
