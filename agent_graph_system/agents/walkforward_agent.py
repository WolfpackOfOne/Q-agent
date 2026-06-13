"""Walk-forward agent: closes the validation loop for backtested strategies.

Phase 2 of issue #62. The pipeline this completes:

    LEAN backtest completes
      → MonitoringAgent sees a Backtest with no recent WalkforwardRun,
        sets Strategy.status = "needs_walkforward"
      → WalkforwardAgent (this) picks it up, fetches a return series, runs the
        walk-forward + bootstrap via the ResearchAgent, writes the WalkforwardRun
      → sets Strategy.status to "validated" / "not_significant" /
        "walkforward_insufficient_data" / "walkforward_unavailable" /
        "walkforward_error"
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

    def run(self, strategy: str | None = None, returns=None, **kwargs) -> Any:
        """Process strategies awaiting walk-forward validation.

        With no arguments, scans the graph for every strategy flagged
        ``needs_walkforward`` and processes each. Passing ``strategy`` (and
        optionally an explicit ``returns``) processes just that one — used by the
        CLI / orchestration to target a single strategy on demand.

        The provider (or the explicit ``returns``) may return **either** a single
        ``pd.Series`` — which is in-sample slicing (``rolling_holdout``, not
        gate-eligible) — **or** a list of per-window OOS return series, which is a
        genuine ``walkforward`` run. See :meth:`_validate`.
        """
        results: dict[str, Any] = {"processed": [], "unavailable": [], "errors": []}
        single_target = strategy is not None
        try:
            targets = [strategy] if single_target else self._flagged_strategies()
        except Exception as exc:
            self._mark_error(str(exc))
            raise

        for name in targets:
            try:
                oos = returns if (single_target and returns is not None) else self._returns_provider(name)
                if oos is None:
                    self._set_status(name, "walkforward_unavailable")
                    results["unavailable"].append(name)
                    log.warning("[WalkforwardAgent] no returns available for %s", name)
                    continue
                outcome = self._validate(name, oos)
                results["processed"].append(outcome)
            except Exception as exc:
                results["errors"].append({"strategy": name, "error": str(exc)})
                try:
                    self._set_status(name, "walkforward_error")
                except Exception:
                    log.exception("[WalkforwardAgent] could not set error status for %s", name)
                log.exception("[WalkforwardAgent] failed to process %s", name)
                if single_target:
                    self._mark_error(str(exc))
                    raise

        try:
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

    def _validate(self, strategy: str, oos) -> dict[str, Any]:
        """Run the walk-forward via the ResearchAgent and update the status.

        A list/tuple of per-window OOS series runs the genuine ``walkforward``
        path; a single series runs the ``rolling_holdout`` path (which cannot
        validate a live deploy — its status reflects that honestly).
        """
        from agent_graph_system.agents.research_agent import ResearchAgent

        run_kwargs = dict(
            mode="walkforward", strategy=strategy,
            train_months=self._train_months, test_months=self._test_months,
            step_months=self._step_months, bootstrap=self._bootstrap,
        )
        if isinstance(oos, (list, tuple)):
            run_kwargs["windows"] = list(oos)
        else:
            run_kwargs["returns"] = oos

        payload = ResearchAgent().run(**run_kwargs)
        status = self._status_from_payload(payload)
        self._set_status(strategy, status)
        log.info(
            "[WalkforwardAgent] %s → %s (run %s, mode=%s)",
            strategy, status, payload.get("run_id"), payload.get("mode"),
        )
        return {
            "strategy": strategy,
            "status": status,
            "run_id": payload.get("run_id"),
            "mode": payload.get("mode"),
            "bootstrap_p_value": payload.get("bootstrap_p_value"),
        }

    @staticmethod
    def _status_from_payload(payload: dict) -> str:
        """Translate a walk-forward result into a Strategy.status.

        - ``walkforward_insufficient_data`` — too little data to form windows.
        - ``walkforward_not_oos`` — a completed ``rolling_holdout`` run (in-sample
          slicing); honest about the fact that it is NOT out-of-sample validation
          and the live gate will refuse it.
        - ``not_significant`` — a genuine run whose bootstrap p-value missed the
          threshold.
        - ``validated`` — a genuine run that clears the bar (or had no p-value),
          matching :func:`ontology.policy.check_deployment_gate`.
        """
        from agent_graph_system.ontology.policy import BOOTSTRAP_P_VALUE_THRESHOLD

        if payload.get("status") == "insufficient_data":
            return "walkforward_insufficient_data"
        if (payload.get("mode") or "walkforward") != "walkforward":
            return "walkforward_not_oos"
        p_value = payload.get("bootstrap_p_value")
        if p_value is not None and p_value > BOOTSTRAP_P_VALUE_THRESHOLD:
            return "not_significant"
        return "validated"

    def _set_status(self, strategy: str, status: str) -> None:
        gm.upsert_strategy(strategy, strategy_type=self._strategy_type(strategy), status=status)

    @staticmethod
    def _strategy_type(name: str) -> str:
        """Preserve an existing strategy's type when re-upserting its status.

        Resolved through the active backend (not the local engine directly) so it
        stays correct when ``GRAPH_BACKEND=neo4j``.
        """
        rows = query("MATCH (s:Strategy) RETURN s.name AS name, s.strategy_type AS strategy_type")
        for row in rows:
            if row.get("name") == name:
                return row.get("strategy_type") or "unknown"
        return "unknown"

    def _default_returns_provider(self, strategy: str):
        from agent_graph_system.analysis.returns import discover_returns
        return discover_returns(strategy, self._search_roots)
