"""Exchange client interface and a mock implementation."""
from __future__ import annotations

import random
import time
from typing import Dict, List, Protocol

from .models import OrderbookLevel, OrderbookSnapshot


class ExchangeClient(Protocol):
    id: str

    def fetch_orderbook(self, symbol: str, depth: int) -> OrderbookSnapshot:
        """Return an orderbook snapshot for a symbol with the given depth."""

    def fetch_balances(self) -> Dict[str, float]:
        """Return currency balances for this exchange."""


class MockExchangeClient:
    """Lightweight mock that fabricates plausible orderbook snapshots.

    Replace this class with a real ccxt-backed client when connecting to
    production exchanges.
    """

    def __init__(self, exchange_id: str):
        self.id = exchange_id
        self._base_prices = {
            "TRX/USDT": 0.1,
            "XRP/USDT": 0.6,
            "LTC/USDT": 70.0,
        }
        self._balances = {"USDT": 10000.0, "TRX": 0.0, "XRP": 0.0, "LTC": 0.0}

    def fetch_orderbook(self, symbol: str, depth: int) -> OrderbookSnapshot:
        base_price = self._base_prices.get(symbol, 1.0)
        midpoint = base_price * random.uniform(0.995, 1.005)
        spread = midpoint * random.uniform(0.0005, 0.0015)
        best_bid = midpoint - spread / 2
        best_ask = midpoint + spread / 2

        bids: List[OrderbookLevel] = []
        asks: List[OrderbookLevel] = []
        price = best_bid
        for _ in range(depth):
            bids.append(OrderbookLevel(price=price, size=random.uniform(500, 2000) / price))
            price -= midpoint * random.uniform(0.0002, 0.0005)
        price = best_ask
        for _ in range(depth):
            asks.append(OrderbookLevel(price=price, size=random.uniform(500, 2000) / price))
            price += midpoint * random.uniform(0.0002, 0.0005)

        return OrderbookSnapshot(
            exchange_id=self.id,
            symbol=symbol,
            bids=bids,
            asks=asks,
            best_bid=bids[0].price,
            best_ask=asks[0].price,
            timestamp=time.time() * 1000,
        )

    def fetch_balances(self) -> Dict[str, float]:
        # TODO: Replace with real balances fetch when wired to exchanges.
        return dict(self._balances)

    def apply_fill(self, symbol: str, base_delta: float, usdt_delta: float) -> None:
        base_currency = symbol.split("/")[0]
        self._balances[base_currency] = self._balances.get(base_currency, 0.0) + base_delta
        self._balances["USDT"] = self._balances.get("USDT", 0.0) + usdt_delta


__all__ = ["ExchangeClient", "MockExchangeClient"]
