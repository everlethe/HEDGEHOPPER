"""Utilities for collecting orderbooks across exchanges."""
from __future__ import annotations

from typing import Dict, Iterable, Tuple

from .exchange_client import ExchangeClient
from .models import OrderbookSnapshot

OrderbookMap = Dict[Tuple[str, str], OrderbookSnapshot]


def collect_all_orderbooks(
    pairs: Iterable[str], exchanges: Iterable[ExchangeClient], depth: int
) -> OrderbookMap:
    """Collect orderbooks for each pair/exchange combination."""
    snapshots: OrderbookMap = {}
    for exchange in exchanges:
        for symbol in pairs:
            try:
                snapshot = exchange.fetch_orderbook(symbol, depth)
                snapshots[(exchange.id, symbol)] = snapshot
            except Exception as exc:  # pragma: no cover - defensive logging only
                print(f"Failed to fetch orderbook for {exchange.id} {symbol}: {exc}")
    return snapshots


__all__ = ["collect_all_orderbooks", "OrderbookMap"]
