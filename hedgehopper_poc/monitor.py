"""Monitoring helpers for balances and safety flags."""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Dict, List

from .models import PortfolioSnapshot, SimulatedFill


@dataclass
class AlertFlags:
    usdt_trend: str
    base_skew: Dict[str, float]
    consecutive_loss_flag: bool
    loss_cut_flag: bool


@dataclass
class PortfolioMonitor:
    base_assets: List[str]
    snapshots: List[PortfolioSnapshot] = field(default_factory=list)
    fills: List[SimulatedFill] = field(default_factory=list)

    def record_snapshot(self, snapshot: PortfolioSnapshot) -> None:
        self.snapshots.append(snapshot)

    def record_fills(self, fills: List[SimulatedFill]) -> None:
        self.fills.extend(fills)

    def _compute_usdt_trend(self) -> str:
        if len(self.snapshots) < 2:
            return "neutral"
        usdt_totals = [sum(balances.get("USDT", 0.0) for balances in snap.exchange_balances.values()) for snap in self.snapshots]
        if usdt_totals[-1] > usdt_totals[0]:
            return "up"
        if usdt_totals[-1] < usdt_totals[0]:
            return "down"
        return "flat"

    def _compute_base_skew(self) -> Dict[str, float]:
        if not self.snapshots:
            return {asset: 0.0 for asset in self.base_assets}
        latest = self.snapshots[-1].exchange_balances
        totals: Dict[str, float] = {asset: 0.0 for asset in self.base_assets}
        for balances in latest.values():
            for asset in self.base_assets:
                totals[asset] += balances.get(asset, 0.0)
        baseline = statistics.mean(totals.values()) if totals else 0.0
        return {asset: (totals[asset] - baseline) for asset in self.base_assets}

    def compute_flags(self, consecutive_loss_limit: int, loss_cut_usd: float) -> AlertFlags:
        consecutive_losses = 0
        for fill in reversed(self.fills):
            if fill.pnl_usd < 0:
                consecutive_losses += 1
            else:
                break
        total_pnl = sum(fill.pnl_usd for fill in self.fills)
        return AlertFlags(
            usdt_trend=self._compute_usdt_trend(),
            base_skew=self._compute_base_skew(),
            consecutive_loss_flag=consecutive_losses >= consecutive_loss_limit,
            loss_cut_flag=total_pnl <= -abs(loss_cut_usd),
        )


__all__ = ["AlertFlags", "PortfolioMonitor"]
