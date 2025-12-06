"""YAML configuration loaders for exchanges, pairs, and engine settings."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml


@dataclass
class ExchangeConfig:
    id: str
    name: str
    ccxt_id: str
    taker_fee_bps: float
    maker_fee_bps: float
    enabled: bool = True


@dataclass
class PairConfig:
    symbol: str
    base: str
    quote: str
    min_notional_usd: float
    max_notional_usd: float
    base_threshold_bps: float


@dataclass
class EngineConfig:
    loop_interval_sec: float
    orderbook_depth_levels: int
    max_total_notional_usd: float
    max_notional_per_trade_usd: float
    max_open_trades: int
    daily_loss_cut_usd: float
    max_consecutive_losses: int
    dry_run: bool = True


@dataclass
class ConfigBundle:
    exchanges: List[ExchangeConfig]
    pairs: List[PairConfig]
    engine: EngineConfig


class ConfigLoader:
    """Helper class to load configuration from a directory."""

    def __init__(self, config_dir: Path):
        self.config_dir = Path(config_dir)

    def load(self) -> ConfigBundle:
        return ConfigBundle(
            exchanges=self.load_exchanges(),
            pairs=self.load_pairs(),
            engine=self.load_engine(),
        )

    def load_exchanges(self) -> List[ExchangeConfig]:
        with open(self.config_dir / "exchanges.yml", "r", encoding="utf-8") as fp:
            raw = yaml.safe_load(fp) or {}
        return [ExchangeConfig(**item) for item in raw.get("exchanges", []) if item.get("enabled", True)]

    def load_pairs(self) -> List[PairConfig]:
        with open(self.config_dir / "pairs.yml", "r", encoding="utf-8") as fp:
            raw = yaml.safe_load(fp) or {}
        return [PairConfig(**item) for item in raw.get("pairs", [])]

    def load_engine(self) -> EngineConfig:
        with open(self.config_dir / "engine.yml", "r", encoding="utf-8") as fp:
            raw = yaml.safe_load(fp) or {}
        return EngineConfig(**(raw.get("engine", {})))


__all__ = [
    "ExchangeConfig",
    "PairConfig",
    "EngineConfig",
    "ConfigBundle",
    "ConfigLoader",
]
