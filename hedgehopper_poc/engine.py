"""Arbitrage detection and paper-trading simulation engine."""
from __future__ import annotations

import itertools
import math
import time
from typing import Dict, Iterable, List, Tuple

from .config_loader import EngineConfig, ExchangeConfig, PairConfig
from .models import OrderbookLevel, OrderbookSnapshot, SimulatedFill, TradeSignal


def compute_avg_fill_price(orderbook_side: List[OrderbookLevel], size: float) -> float:
    remaining = size
    cost = 0.0
    for level in orderbook_side:
        take = min(level.size, remaining)
        cost += take * level.price
        remaining -= take
        if remaining <= 0:
            break
    if remaining > 0:
        raise ValueError("Insufficient depth to satisfy trade size")
    return cost / size


def available_size(orderbook_side: List[OrderbookLevel]) -> float:
    return sum(level.size for level in orderbook_side)


def compute_slippage_bps(best_price: float, avg_price: float, side: str) -> float:
    if best_price == 0:
        return 0.0
    if side == "buy":
        return (avg_price - best_price) / best_price * 10_000
    return (best_price - avg_price) / best_price * 10_000


def evaluate_opportunities(
    orderbooks: Dict[Tuple[str, str], OrderbookSnapshot],
    pairs: Iterable[PairConfig],
    exchanges: Dict[str, ExchangeConfig],
    engine_config: EngineConfig,
) -> List[SimulatedFill]:
    fills: List[SimulatedFill] = []
    for pair in pairs:
        pair_books = {ex: ob for (ex, sym), ob in orderbooks.items() if sym == pair.symbol}
        for buy_ex, sell_ex in itertools.permutations(pair_books.keys(), 2):
            buy_book = pair_books[buy_ex]
            sell_book = pair_books[sell_ex]
            if not buy_book.asks or not sell_book.bids:
                continue

            buy_best_ask = buy_book.best_ask
            sell_best_bid = sell_book.best_bid
            mid_price = (buy_best_ask + sell_best_bid) / 2
            target_notional = min(pair.max_notional_usd, engine_config.max_notional_per_trade_usd)
            size = target_notional / mid_price

            max_buy_size = available_size(buy_book.asks)
            max_sell_size = available_size(sell_book.bids)
            size = min(size, max_buy_size, max_sell_size)
            if size * mid_price < pair.min_notional_usd:
                continue

            try:
                buy_avg = compute_avg_fill_price(buy_book.asks, size)
                sell_avg = compute_avg_fill_price(sell_book.bids, size)
            except ValueError:
                continue

            gross_spread = (sell_avg - buy_avg) / mid_price
            gross_bps = gross_spread * 10_000
            buy_fee = exchanges[buy_ex].taker_fee_bps / 10_000
            sell_fee = exchanges[sell_ex].taker_fee_bps / 10_000
            effective_spread = gross_spread - buy_fee - sell_fee
            effective_bps = effective_spread * 10_000

            if effective_bps < pair.base_threshold_bps:
                continue

            buy_slip = compute_slippage_bps(buy_best_ask, buy_avg, "buy")
            sell_slip = compute_slippage_bps(sell_best_bid, sell_avg, "sell")
            pnl = (sell_avg - buy_avg) * size - (buy_fee + sell_fee) * mid_price * size

            signal = TradeSignal(
                symbol=pair.symbol,
                buy_exchange=buy_ex,
                sell_exchange=sell_ex,
                notional_usd=mid_price * size,
                expected_gross_spread_bps=gross_bps,
                expected_effective_spread_bps=effective_bps,
                timestamp=time.time(),
            )

            features = build_features(buy_book, sell_book, size, mid_price)
            fill = SimulatedFill(
                signal=signal,
                buy_avg_price=buy_avg,
                sell_avg_price=sell_avg,
                buy_slippage_bps=buy_slip,
                sell_slippage_bps=sell_slip,
                pnl_usd=pnl,
                latency_ms=random_latency_ms(),
                features=features,
            )
            fills.append(fill)
    return fills


def build_features(
    buy_book: OrderbookSnapshot, sell_book: OrderbookSnapshot, size: float, mid_price: float
) -> Dict[str, float]:
    buy_depth = cumulative_depth(buy_book.asks, size)
    sell_depth = cumulative_depth(sell_book.bids, size)
    timestamp = time.time()
    time_of_day = timestamp % 86_400
    return {
        "buy_best_bid": buy_book.best_bid,
        "buy_best_ask": buy_book.best_ask,
        "sell_best_bid": sell_book.best_bid,
        "sell_best_ask": sell_book.best_ask,
        "buy_cumulative_depth_base": buy_depth,
        "sell_cumulative_depth_base": sell_depth,
        "time_of_day_sec": time_of_day,
        "trade_base_size": size,
        "mid_price": mid_price,
    }


def cumulative_depth(levels: List[OrderbookLevel], target_size: float) -> float:
    remaining = target_size
    depth_taken = 0.0
    for level in levels:
        take = min(level.size, remaining)
        depth_taken += take
        remaining -= take
        if remaining <= 0:
            break
    return depth_taken


def random_latency_ms() -> int:
    return int(abs(math.sin(time.time())) * 150) + 50


__all__ = [
    "evaluate_opportunities",
    "compute_avg_fill_price",
    "cumulative_depth",
]
