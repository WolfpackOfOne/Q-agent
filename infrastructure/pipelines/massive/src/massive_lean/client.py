"""Thin wrapper around the official `massive` Python client.

Massive.com (https://massive.com) is a market-data API provider whose REST
surface mirrors Polygon.io's shape closely (same `list_aggs` aggregate-bar
conventions, same `O:`-prefixed options ticker format, same pagination
style). The official client is `pip install -U massive` and exposes
`from massive import RESTClient`.

This module centralizes:
  - Reading `MASSIVE_API_KEY` from the environment with a clear error if unset.
  - Constructing a `RESTClient`.
  - Thin helper methods for the futures and options endpoints this pipeline
    needs, so `transform.py` and the pipeline scripts never touch the raw
    `massive` SDK directly.

IMPORTANT — untested against the live API
-------------------------------------------
This module was written without an active Massive.com API key (the
"Advanced" tier required for options data has not been purchased yet — see
`claude.md`). Method names, signatures, and response model fields
(`list_futures_aggregates`, `list_futures_contracts`, `list_aggs`,
`list_snapshot_options_chain`, `list_options_contracts`, and the
`FuturesAgg`/`FuturesContract`/`OptionContractSnapshot`/`Agg` models) were
cross-checked against the `massive==2.8.0` package source on PyPI
(`massive/rest/futures.py`, `massive/rest/snapshot.py`,
`massive/rest/reference.py`, `massive/rest/models/*.py`), so the *shapes*
below should be accurate. What remains unverified is *behavior*: actual
HTTP responses, pagination edge cases, rate limits, and whether endpoints
return data for the requested tickers/date ranges on your subscription
tier. Search for "ASSUMPTION" comments below for the specific spots to
double-check once a key is available.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Iterable, Iterator

MASSIVE_API_KEY_ENV = "MASSIVE_API_KEY"

_SIGNUP_HELP = (
    "MASSIVE_API_KEY is not set.\n"
    "\n"
    "This pipeline requires a Massive.com API key:\n"
    "  1. Sign up at https://massive.com (the 'Advanced' tier, ~$199/mo, is\n"
    "     required for US options data — futures data may be available on a\n"
    "     lower tier; check https://massive.com/pricing).\n"
    "  2. Generate an API key from your dashboard at https://massive.com/dashboard.\n"
    "  3. Copy infrastructure/pipelines/massive/.env.example to .env and set\n"
    "     MASSIVE_API_KEY=<your key>, OR export it directly:\n"
    "       export MASSIVE_API_KEY=\"<your key>\"\n"
    "\n"
    "See infrastructure/pipelines/massive/claude.md for full setup notes."
)


class MassiveAuthError(RuntimeError):
    """Raised when MASSIVE_API_KEY is missing or invalid."""


def get_api_key(api_key: str | None = None) -> str:
    """Resolve the Massive API key from an explicit arg or the environment.

    Raises `MassiveAuthError` with an actionable message if no key is found.
    """
    key = api_key or os.environ.get(MASSIVE_API_KEY_ENV)
    if not key:
        raise MassiveAuthError(_SIGNUP_HELP)
    return key


@dataclass
class MassiveClient:
    """Wraps `massive.RESTClient` with pipeline-specific helper methods.

    Construction raises `MassiveAuthError` immediately if no API key is
    configured, so pipeline scripts fail fast with an actionable message
    rather than dying deep inside an HTTP call.
    """

    api_key: str | None = None
    _client: Any = field(default=None, repr=False, init=False)

    def __post_init__(self) -> None:
        resolved_key = get_api_key(self.api_key)
        try:
            from massive import RESTClient  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - import guard
            raise ImportError(
                "The 'massive' package is not installed. Run "
                "`pip install -e infrastructure/pipelines/massive` (or "
                "`bash infrastructure/setup.sh`) after adding 'massive' to "
                "infrastructure/requirements.txt."
            ) from exc
        self._client = RESTClient(api_key=resolved_key)

    # ------------------------------------------------------------------
    # Futures — /futures/v1/... (per massive-com/client-python README)
    # ------------------------------------------------------------------
    def list_futures_contracts(
        self,
        product_code: str | None = None,
        ticker: str | None = None,
        active: bool | None = None,
        **kwargs: Any,
    ) -> Iterator[Any]:
        """List futures contracts (`GET /futures/v1/contracts`), optionally
        filtered by product code (root symbol, e.g. "ES").

        Verified against `massive==2.8.0` source
        (`massive/rest/futures.py::list_futures_contracts`): `product_code`,
        `ticker`, and `active` are real keyword arguments, along with
        `*_gt/_gte/_lt/_lte/_any_of` range filters not exposed here. Returns
        an iterator of `FuturesContract` objects with fields `ticker`,
        `product_code`, `trading_venue`, `name`, `type`, `date`, `active`,
        `first_trade_date`, `last_trade_date`, `settlement_date`, etc. —
        NOTE there is no `expiration_date` field; use `last_trade_date` or
        `settlement_date` as the expiration proxy
        (see `transform.transform_futures_contracts`).
        """
        params: dict[str, Any] = {}
        if product_code is not None:
            params["product_code"] = product_code
        if ticker is not None:
            params["ticker"] = ticker
        if active is not None:
            params["active"] = active
        params.update(kwargs)
        return self._client.list_futures_contracts(**params)

    def list_futures_aggregates(
        self,
        ticker: str,
        resolution: str = "day",
        from_: str | None = None,
        to: str | None = None,
        limit: int = 50_000,
        **kwargs: Any,
    ) -> Iterator[Any]:
        """Daily OHLCV aggregate bars for a single futures contract ticker
        (`GET /futures/v1/aggs/{ticker}`).

        Verified against `massive==2.8.0` source
        (`massive/rest/futures.py::list_futures_aggregates`): the real
        keyword arguments are `resolution`, `window_start_gte`,
        `window_start_lte` (underscored, NOT dotted `.gte`/`.lte`). `to`
        maps to `window_start_lte`.

        ASSUMPTION (still unverified — confirm once a key is available):
        the accepted `resolution` values for EOD bars. By analogy with the
        stocks/options `timespan` argument ("day"/"week"/etc.) `"day"` is
        the most likely value, but the futures endpoint may instead expect
        a multiplier+unit pair (e.g. `"1d"`) or a fixed enum like
        `"daily"`/`"session"`. Check
        https://massive.com/docs/rest/futures/aggregates if `"day"` 400s.

        Returns an iterator of `FuturesAgg` objects with fields `ticker`,
        `open`, `high`, `low`, `close`, `volume`, `dollar_volume`,
        `transactions`, `window_start` (int, nanoseconds since epoch UTC),
        `session_end_date`, `settlement_price`.
        """
        params: dict[str, Any] = {"ticker": ticker, "resolution": resolution, "limit": limit}
        if from_ is not None:
            params["window_start_gte"] = from_
        if to is not None:
            params["window_start_lte"] = to
        params.update(kwargs)
        return self._client.list_futures_aggregates(**params)

    # ------------------------------------------------------------------
    # Options — Polygon-style /v3 reference + /v2 aggs endpoints
    # ------------------------------------------------------------------
    def list_options_contracts(
        self,
        underlying_ticker: str,
        expired: bool | None = None,
        **kwargs: Any,
    ) -> Iterator[Any]:
        """List option contracts for an underlying (`GET /v3/reference/options/contracts`).

        `underlying_ticker`, `expired`, `contract_type`, `expiration_date`,
        `strike_price` (and `_lt/_lte/_gt/_gte` variants), and `as_of` are
        real keyword arguments per `massive==2.8.0`
        (`massive/rest/reference.py::list_options_contracts`).
        `expired=False` (the API default) restricts to live contracts; pass
        `expired=True` if historical (expired) contracts are needed for EOD
        backfills of past option chains.
        """
        params: dict[str, Any] = {"underlying_ticker": underlying_ticker}
        if expired is not None:
            params["expired"] = expired
        params.update(kwargs)
        return self._client.list_options_contracts(**params)

    def list_snapshot_options_chain(
        self,
        underlying_ticker: str,
        params: dict[str, Any] | None = None,
    ) -> Iterator[Any]:
        """Snapshot of an underlying's options chain: quotes, greeks, IV, OI
        (`GET /v3/snapshot/options/{underlying_asset}`).

        Verified against `massive==2.8.0` source
        (`massive/rest/snapshot.py::list_snapshot_options_chain` and
        `massive/rest/models/snapshot.py::OptionContractSnapshot`). Returns
        an iterator of `OptionContractSnapshot` objects with:
          - `details`: `OptionDetails(ticker, contract_type, expiration_date,
            strike_price, exercise_style, shares_per_contract)`
          - `greeks`: `Greeks(delta, gamma, theta, vega)`
          - `implied_volatility` (top-level float)
          - `open_interest` (top-level float)
          - `day`: `DayOptionContractSnapshot(open, high, low, close, volume, vwap, ...)`
          - `last_quote`: `LastQuoteOptionContractSnapshot(bid, ask, midpoint, ...)`
          - `last_trade`: `LastTradeOptionContractSnapshot(price, size, ...)`

        This is a *current* snapshot, not a historical EOD series — useful
        for capturing today's chain (greeks/IV/OI) as a point-in-time
        alternative-data row. For historical EOD price bars per contract,
        use `list_aggs` with an `O:`-prefixed option ticker instead.
        """
        return self._client.list_snapshot_options_chain(underlying_ticker, params=params or {})

    def list_aggs(
        self,
        ticker: str,
        multiplier: int = 1,
        timespan: str = "day",
        from_: str | None = None,
        to: str | None = None,
        limit: int = 50_000,
        **kwargs: Any,
    ) -> Iterator[Any]:
        """Daily OHLCV aggregate bars for a single ticker (stocks, options, etc.)
        (`GET /v2/aggs/ticker/{ticker}/range/{multiplier}/{timespan}/{from}/{to}`).

        For options, `ticker` uses the `O:`-prefixed OSI-style format, e.g.
        `O:SPY251219C00650000`. Confirmed against the official example at
        https://github.com/massive-com/client-python/blob/master/examples/rest/options-aggregates_bars.py
        and the `massive==2.8.0` `list_aggs` signature
        (`massive/rest/aggs.py`) — `ticker, multiplier, timespan, from_, to`
        are positional. Returns an iterator of `Agg` objects with fields
        `open, high, low, close, volume, vwap, timestamp` (ms since epoch
        UTC), `transactions, otc`.
        """
        return self._client.list_aggs(
            ticker, multiplier, timespan, from_, to, limit=limit, **kwargs
        )


def iter_to_list(items: Iterable[Any], limit: int | None = None) -> list[Any]:
    """Materialize a (possibly paginated) iterator into a list, optionally capped."""
    out: list[Any] = []
    for i, item in enumerate(items):
        if limit is not None and i >= limit:
            break
        out.append(item)
    return out
