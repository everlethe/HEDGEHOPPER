"""Risk guardrails for paper trading.

Current implementation contains lightweight checks for maximum notionals and
consecutive losses. The module is intentionally simple and can be extended to
include production-grade controls.
"""
from __future__ import annotations

from typing import List

from .models import SimulatedFill


def enforce_notional_limit(fills: List[SimulatedFill], max_total_notional_usd: float) -> bool:
    """Return True if cumulative notional in the current loop is within limits."""
    total_notional = sum(fill.signal.notional_usd for fill in fills)
    return total_notional <= max_total_notional_usd


def detect_consecutive_losses(fills: List[SimulatedFill], limit: int) -> bool:
    losses = 0
    for fill in reversed(fills):
        if fill.pnl_usd < 0:
            losses += 1
        else:
            break
    return losses >= limit


def loss_cut_trigger(fills: List[SimulatedFill], daily_loss_cut_usd: float) -> bool:
    return sum(fill.pnl_usd for fill in fills) <= -abs(daily_loss_cut_usd)


__all__ = [
    "enforce_notional_limit",
    "detect_consecutive_losses",
    "loss_cut_trigger",
]
