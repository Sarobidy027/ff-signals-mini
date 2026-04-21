"""
Modèles de performance.
"""
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class PerformanceStats(BaseModel):
    """Statistiques de performance."""
    win_rate: float = Field(ge=0, le=100)
    total_signals: int = Field(ge=0)
    wins: int = Field(ge=0)
    losses: int = Field(ge=0)
    average_pips_gained: float
    largest_win: float = Field(ge=0)
    largest_loss: float = Field(ge=0)
    profit_factor: float = Field(ge=0)
    last_updated: datetime
    win_rate_target: float = Field(default=90.0, ge=0, le=100)


class RecentSignal(BaseModel):
    """Signal récent pour affichage."""
    id: str
    instrument: str
    direction: str
    result: str
    pips_gained: float
    closed_at: datetime


class PerformanceHistory(BaseModel):
    """Historique quotidien des performances."""
    date: str
    win_rate: float
    total_signals: int
    wins: int
    losses: int
    profit_factor: float


class InstrumentPerformance(BaseModel):
    """Performance par instrument."""
    instrument: str
    win_rate: float
    total_signals: int
    wins: int
    losses: int
    average_pips: float


class TradeTypePerformance(BaseModel):
    """Performance par type de trade."""
    trade_type: str
    win_rate: float
    total_signals: int
    wins: int
    losses: int


class PerformanceSummary(BaseModel):
    """Résumé complet des performances."""
    overall: PerformanceStats
    by_instrument: Dict[str, InstrumentPerformance]
    by_trade_type: Dict[str, TradeTypePerformance]
    recent_signals: list[RecentSignal]
    history: list[PerformanceHistory]