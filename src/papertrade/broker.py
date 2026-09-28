"""Minimal Alpaca PAPER-only client (standard library only).

Safety: the trading base URL is hard-locked to the paper endpoint; any other
URL raises.  Alpaca issues paper and live keys separately, so paper keys
cannot place real-money trades.

NOTE: endpoint paths follow Alpaca's public v2 API as known at build time.
They were not reachable from the build environment, so verify on first use
(a dry run is safe: it only reads account, positions and prices).
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence

from .config import KEY_ENV, MARKET_DATA_BASE_URL, PAPER_TRADING_BASE_URL, SECRET_ENV


class PaperOnlyError(RuntimeError):
    pass


class PaperBroker:
    def __init__(self, key_id: str, secret_key: str, base_url: str = PAPER_TRADING_BASE_URL):
        if base_url.rstrip("/") != PAPER_TRADING_BASE_URL:
            raise PaperOnlyError("only the Alpaca PAPER endpoint is allowed")
        if not key_id or not secret_key:
            raise PaperOnlyError(f"set {KEY_ENV} and {SECRET_ENV} to your PAPER keys")
        self._headers = {
            "APCA-API-KEY-ID": key_id,
            "APCA-API-SECRET-KEY": secret_key,
            "Accept": "application/json",
        }
        self.base_url = PAPER_TRADING_BASE_URL

    @classmethod
    def from_env(cls) -> "PaperBroker":
        return cls(os.environ.get(KEY_ENV, ""), os.environ.get(SECRET_ENV, ""))

    def _request(self, method: str, url: str, body: dict | None = None) -> Any:
        data = None if body is None else json.dumps(body).encode()
        headers = dict(self._headers)
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode() or "null")

    def account(self) -> dict:
        return self._request("GET", f"{self.base_url}/v2/account")

    def position_values(self) -> dict[str, float]:
        positions = self._request("GET", f"{self.base_url}/v2/positions") or []
        return {p["symbol"]: float(p["market_value"]) for p in positions}

    def open_orders(self) -> list[dict]:
        """Orders not yet filled or cancelled (e.g. waiting for the market to open)."""
        return self._request("GET", f"{self.base_url}/v2/orders?status=open") or []

    def monthly_closes(self, symbols: Sequence[str], months: int) -> dict[str, list[float]]:
        """Completed monthly closes (the current, unfinished month is dropped)."""
        start = (datetime.now(timezone.utc) - timedelta(days=31 * (months + 2))).date().isoformat()
        query = urllib.parse.urlencode({
            "symbols": ",".join(symbols),
            "timeframe": "1Month",
            "start": start,
            "adjustment": "all",
            "feed": "iex",
            "limit": 10000,
        })
        payload = self._request("GET", f"{MARKET_DATA_BASE_URL}/v2/stocks/bars?{query}")
        this_month = datetime.now(timezone.utc).strftime("%Y-%m")
        out: dict[str, list[float]] = {}
        for symbol, bars in (payload.get("bars") or {}).items():
            done = [b for b in bars if not str(b["t"]).startswith(this_month)]
            out[symbol] = [float(b["c"]) for b in done]
        return out

    def daily_equity(self) -> list[tuple[str, float]]:
        """End-of-day account value for the last year, as (YYYY-MM-DD, equity)."""
        query = urllib.parse.urlencode({"period": "1A", "timeframe": "1D"})
        payload = self._request("GET", f"{self.base_url}/v2/account/portfolio/history?{query}") or {}
        out = []
        for ts, eq in zip(payload.get("timestamp") or [], payload.get("equity") or []):
            if eq is None:
                continue
            day = datetime.fromtimestamp(int(ts), timezone.utc).date().isoformat()
            out.append((day, float(eq)))
        return out

    def daily_closes(self, symbol: str, start: str) -> list[tuple[str, float]]:
        """Dividend-adjusted daily closes from `start` (YYYY-MM-DD), as (date, close)."""
        query = urllib.parse.urlencode({
            "symbols": symbol,
            "timeframe": "1Day",
            "start": start,
            "adjustment": "all",
            "feed": "iex",
            "limit": 10000,
        })
        payload = self._request("GET", f"{MARKET_DATA_BASE_URL}/v2/stocks/bars?{query}") or {}
        bars = (payload.get("bars") or {}).get(symbol) or []
        return [(str(b["t"])[:10], float(b["c"])) for b in bars]

    def submit_notional_order(self, symbol: str, side: str, notional: float) -> dict:
        if side not in {"buy", "sell"}:
            raise ValueError("side must be buy or sell")
        return self._request("POST", f"{self.base_url}/v2/orders", {
            "symbol": symbol,
            "side": side,
            "type": "market",
            "time_in_force": "day",
            "notional": f"{notional:.2f}",
        })
