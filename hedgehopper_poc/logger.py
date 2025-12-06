"""Logging utilities for simulated fills and simple PnL summaries."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable, List

import pandas as pd

from .models import SimulatedFill


class SimulationLogger:
    def __init__(self, fills_path: Path):
        self.fills_path = Path(fills_path)
        self.fills_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.fills_path.exists():
            with open(self.fills_path, "w", newline="", encoding="utf-8") as fp:
                writer = csv.writer(fp)
                writer.writerow(
                    [
                        "timestamp",
                        "symbol",
                        "buy_exchange",
                        "sell_exchange",
                        "notional_usd",
                        "buy_avg_price",
                        "sell_avg_price",
                        "gross_spread_bps",
                        "effective_spread_bps",
                        "buy_slippage_bps",
                        "sell_slippage_bps",
                        "pnl_usd",
                        "latency_ms",
                        "buy_best_bid",
                        "buy_best_ask",
                        "sell_best_bid",
                        "sell_best_ask",
                        "buy_cumulative_depth_base",
                        "sell_cumulative_depth_base",
                        "time_of_day_sec",
                        "trade_base_size",
                        "mid_price",
                    ]
                )

    def log_fills(self, fills: Iterable[SimulatedFill]) -> None:
        with open(self.fills_path, "a", newline="", encoding="utf-8") as fp:
            writer = csv.writer(fp)
            for fill in fills:
                writer.writerow(
                    [
                        fill.signal.timestamp,
                        fill.signal.symbol,
                        fill.signal.buy_exchange,
                        fill.signal.sell_exchange,
                        fill.signal.notional_usd,
                        fill.buy_avg_price,
                        fill.sell_avg_price,
                        fill.signal.expected_gross_spread_bps,
                        fill.signal.expected_effective_spread_bps,
                        fill.buy_slippage_bps,
                        fill.sell_slippage_bps,
                        fill.pnl_usd,
                        fill.latency_ms,
                        fill.features.get("buy_best_bid", 0.0),
                        fill.features.get("buy_best_ask", 0.0),
                        fill.features.get("sell_best_bid", 0.0),
                        fill.features.get("sell_best_ask", 0.0),
                        fill.features.get("buy_cumulative_depth_base", 0.0),
                        fill.features.get("sell_cumulative_depth_base", 0.0),
                        fill.features.get("time_of_day_sec", 0.0),
                        fill.features.get("trade_base_size", 0.0),
                        fill.features.get("mid_price", 0.0),
                    ]
                )


def summarize(log_file: Path) -> None:
    df = pd.read_csv(log_file)
    print("=== PnL Summary ===")
    print(df.groupby("symbol").agg(trades=("pnl_usd", "count"), pnl_usd=("pnl_usd", "sum")))
    print("Total PnL:", df["pnl_usd"].sum())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize simulated fills log")
    parser.add_argument("--log-file", type=Path, required=True, help="CSV file with simulated fills")
    args = parser.parse_args()
    summarize(args.log_file)
