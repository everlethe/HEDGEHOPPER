"""Core data models for the HEDGEHOPPER paper-trading PoC."""
from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class OrderbookLevel(BaseModel):
    price: float
    size: float


class OrderbookSnapshot(BaseModel):
    exchange_id: str
    symbol: str
    bids: List[OrderbookLevel] = Field(default_factory=list)
    asks: List[OrderbookLevel] = Field(default_factory=list)
    best_bid: float
    best_ask: float
    timestamp: float


class TradeSignal(BaseModel):
    symbol: str
    buy_exchange: str
    sell_exchange: str
    notional_usd: float
    expected_gross_spread_bps: float
    expected_effective_spread_bps: float
    timestamp: float


class SimulatedFill(BaseModel):
    signal: TradeSignal
    buy_avg_price: float
    sell_avg_price: float
    buy_slippage_bps: float
    sell_slippage_bps: float
    pnl_usd: float
    latency_ms: int
    features: Dict[str, float] = Field(default_factory=dict)


class PortfolioSnapshot(BaseModel):
    timestamp: float
    exchange_balances: Dict[str, Dict[str, float]]
