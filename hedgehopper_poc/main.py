"""CLI entrypoint for the HEDGEHOPPER paper trading PoC."""
from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Dict, List

from .collector import collect_all_orderbooks
from .config_loader import ConfigLoader, ExchangeConfig
from .engine import evaluate_opportunities
from .exchange_client import MockExchangeClient
from .logger import SimulationLogger
from .models import PortfolioSnapshot, SimulatedFill
from .monitor import PortfolioMonitor
from .risk import detect_consecutive_losses, enforce_notional_limit, loss_cut_trigger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HEDGEHOPPER paper trading PoC")
    parser.add_argument("--config-dir", type=Path, default=Path("./config"), help="Directory containing YAML configs")
    parser.add_argument("--duration-sec", type=int, default=30, help="How long to run the simulation loop")
    parser.add_argument("--log-dir", type=Path, default=Path("./logs"), help="Directory to store CSV logs")
    return parser.parse_args()


def build_exchange_clients(exchange_ids: List[str]):
    return {eid: MockExchangeClient(exchange_id=eid) for eid in exchange_ids}


def snapshot_portfolio(clients: List[MockExchangeClient]) -> PortfolioSnapshot:
    balances: Dict[str, Dict[str, float]] = {}
    for client in clients:
        balances[client.id] = client.fetch_balances()
    return PortfolioSnapshot(timestamp=time.time(), exchange_balances=balances)


def apply_fills_to_portfolio(
    fills: List[SimulatedFill], clients: Dict[str, MockExchangeClient], exchanges: Dict[str, ExchangeConfig]
) -> None:
    for fill in fills:
        mid_price = fill.features.get("mid_price") or (
            (fill.buy_avg_price + fill.sell_avg_price) / 2
        )
        size = fill.features.get("trade_base_size") or fill.signal.notional_usd / mid_price
        buy_fee = exchanges[fill.signal.buy_exchange].taker_fee_bps / 10_000
        sell_fee = exchanges[fill.signal.sell_exchange].taker_fee_bps / 10_000
        buy_cost = -size * fill.buy_avg_price * (1 + buy_fee)
        sell_proceeds = size * fill.sell_avg_price * (1 - sell_fee)

        buy_client = clients[fill.signal.buy_exchange]
        sell_client = clients[fill.signal.sell_exchange]
        buy_client.apply_fill(fill.signal.symbol, base_delta=size, usdt_delta=buy_cost)
        sell_client.apply_fill(fill.signal.symbol, base_delta=-size, usdt_delta=sell_proceeds)


def main():
    args = parse_args()
    config = ConfigLoader(args.config_dir).load()
    exchanges = {ex.id: ex for ex in config.exchanges}
    exchange_clients = build_exchange_clients(list(exchanges.keys()))
    symbols = [pair.symbol for pair in config.pairs]

    logger = SimulationLogger(args.log_dir / "fills.csv")
    monitor = PortfolioMonitor(base_assets=[pair.base for pair in config.pairs])

    start = time.time()
    while time.time() - start < args.duration_sec:
        orderbooks = collect_all_orderbooks(
            symbols, exchange_clients.values(), config.engine.orderbook_depth_levels
        )
        fills = evaluate_opportunities(orderbooks, config.pairs, exchanges, config.engine)

        if not enforce_notional_limit(fills, config.engine.max_total_notional_usd):
            print("Skipped logging due to notional limit")
            fills = []

        apply_fills_to_portfolio(fills, exchange_clients, exchanges)
        logger.log_fills(fills)
        monitor.record_fills(fills)
        portfolio = snapshot_portfolio(list(exchange_clients.values()))
        monitor.record_snapshot(portfolio)
        flags = monitor.compute_flags(config.engine.max_consecutive_losses, config.engine.daily_loss_cut_usd)
        print(
            f"Loop complete. Fills: {len(fills)} | USDT trend: {flags.usdt_trend} | "
            f"Loss flags: consecutive={flags.consecutive_loss_flag}, loss_cut={flags.loss_cut_flag}"
        )

        if detect_consecutive_losses(monitor.fills, config.engine.max_consecutive_losses):
            print("Consecutive loss limit reached; stopping simulation")
            break
        if loss_cut_trigger(monitor.fills, config.engine.daily_loss_cut_usd):
            print("Daily loss cut triggered; stopping simulation")
            break
        time.sleep(config.engine.loop_interval_sec)


if __name__ == "__main__":
    main()
