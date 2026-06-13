"""Research agent: GraphRAG discovery, paper ingestion, and walk-forward validation."""

from __future__ import annotations

import dataclasses
import logging
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from agent_graph_system.agents.base_agent import BaseAgent
from agent_graph_system.rag.retriever import graphrag_query, stale_impact_report

if TYPE_CHECKING:  # avoid importing pandas at module load
    import pandas as pd

log = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    name = "ResearchAgent"
    role = "research"

    def run(
        self,
        question: str = "",
        mode: str = "rag",
        arxiv_id: str = "",
        *,
        strategy: str = "",
        returns: "pd.Series | None" = None,
        train_months: int = 12,
        test_months: int = 3,
        step_months: int = 3,
        bootstrap: bool = True,
        **kwargs,
    ) -> Any:
        log.info(
            "[ResearchAgent] mode=%s running query: %s",
            mode, question or arxiv_id or strategy or "<stale impact>",
        )
        try:
            if mode == "walkforward":
                result = self._run_walkforward(
                    strategy, returns,
                    train_months=train_months,
                    test_months=test_months,
                    step_months=step_months,
                    bootstrap=bootstrap,
                )
            elif mode == "ingest_paper":
                if not arxiv_id:
                    raise ValueError("mode='ingest_paper' requires arxiv_id")
                from agent_graph_system.ingestion.papers.graph_writer import ingest_paper
                result = ingest_paper(arxiv_id)
            elif question:
                result = graphrag_query(question)
            else:
                result = stale_impact_report()
            self._mark_idle()
            return result
        except Exception as exc:
            self._mark_error(str(exc))
            raise

    def _run_walkforward(
        self,
        strategy: str,
        returns: "pd.Series | None",
        *,
        train_months: int,
        test_months: int,
        step_months: int,
        bootstrap: bool,
    ) -> dict[str, Any]:
        """Run walk-forward analysis and persist the result to the graph.

        On insufficient data, a ``status='insufficient_data'`` run is still
        written (so the gap is visible in context packs and the gate) and
        returned rather than raised.
        """
        import numpy as np

        from agent_graph_system.analysis.bootstrap import bootstrap_sharpe_pvalue
        from agent_graph_system.analysis.walkforward import (
            InsufficientDataError,
            run_walkforward,
        )
        from agent_graph_system.graph.backend import latest_backtest_for_strategy
        from agent_graph_system.graph.neo4j import graph_models as gm
        from agent_graph_system.ontology.provenance import Provenance

        if not strategy:
            raise ValueError("mode='walkforward' requires a strategy name")
        if returns is None:
            raise ValueError("mode='walkforward' requires a returns Series")

        run_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        prov = Provenance.declared("ResearchAgent.walkforward")

        try:
            result = run_walkforward(
                returns,
                strategy=strategy,
                train_months=train_months,
                test_months=test_months,
                step_months=step_months,
            )
        except InsufficientDataError as exc:
            gm.upsert_walkforward_run(
                run_id, strategy,
                created_at=created_at, status="insufficient_data",
                train_months=train_months, test_months=test_months,
                step_months=step_months, n_windows=0, message=str(exc),
                provenance=prov,
            )
            gm.strategy_has_walkforward(strategy, run_id)
            return {
                "run_id": run_id, "strategy": strategy,
                "status": "insufficient_data", "message": str(exc),
            }

        if bootstrap:
            all_oos = np.concatenate([w.oos_returns for w in result.windows])
            result.bootstrap_p_value = bootstrap_sharpe_pvalue(
                all_oos, result.aggregate_sharpe
            )
            result.bootstrap_n_permutations = 10_000

        n_profitable = sum(
            1 for w in result.windows
            if float(np.prod(1.0 + w.oos_returns)) > 1.0
        )
        gm.upsert_walkforward_run(
            run_id, strategy,
            created_at=created_at, status="completed",
            train_months=result.train_months,
            test_months=result.test_months,
            step_months=result.step_months,
            mode=result.mode,
            n_windows=len(result.windows),
            n_windows_profitable=n_profitable,
            pct_profitable=result.pct_windows_profitable,
            pct_windows_positive_sharpe=result.pct_windows_positive_sharpe,
            aggregate_sharpe=result.aggregate_sharpe,
            aggregate_cagr=result.aggregate_cagr,
            aggregate_max_drawdown=result.aggregate_max_drawdown,
            bootstrap_p_value=result.bootstrap_p_value,
            bootstrap_n_permutations=result.bootstrap_n_permutations,
            provenance=prov,
        )
        for w in result.windows:
            window_id = f"{run_id}_w{w.window_index}"
            gm.upsert_walkforward_window(
                window_id, run_id,
                window_index=w.window_index,
                train_start=w.train_start, train_end=w.train_end,
                test_start=w.test_start, test_end=w.test_end,
                sharpe=w.sharpe, cagr=w.cagr,
                max_drawdown=w.max_drawdown, n_trades=w.n_trades,
                provenance=prov,
            )
            gm.walkforward_run_has_window(run_id, window_id)
        gm.strategy_has_walkforward(strategy, run_id)

        backtest = latest_backtest_for_strategy(strategy)
        if backtest and backtest.get("run_id"):
            gm.walkforward_validates_backtest(run_id, backtest["run_id"])

        payload = dataclasses.asdict(result)
        # Per-window OOS arrays are large and not JSON-friendly; summarize.
        payload["windows"] = [
            {k: v for k, v in w.items() if k != "oos_returns"}
            for w in payload["windows"]
        ]
        payload["run_id"] = run_id
        payload["status"] = "completed"
        return payload
