"""
Modèles pour le Volume Spread Analysis (VSA).
"""
from typing import Literal, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class SpreadAnalysis(BaseModel):
    """Analyse du spread d'une bougie."""
    spread_type: Literal["NARROW", "NORMAL", "WIDE", "ULTRA_WIDE"]
    spread_value: float
    relative_to_avg: float
    significance: float = Field(ge=0, le=100)


class VolumeClimax(BaseModel):
    """Climax de volume détecté."""
    climax_type: Literal["BUYING", "SELLING"]
    volume_ratio: float
    spread_ratio: float
    confidence: float = Field(ge=0, le=100)
    timestamp: datetime
    price: float
    expected_reversal: Literal["BULLISH", "BEARISH"]


class EffortResult(BaseModel):
    """Analyse Effort vs Résultat."""
    effort: float
    result: float
    ratio: float
    signal: Literal["CONTINUATION", "REVERSAL", "NEUTRAL"]
    direction: Optional[Literal["BULLISH", "BEARISH"]] = None
    confidence: float = Field(ge=0, le=100)


class VSASignal(BaseModel):
    """Signal VSA complet."""
    id: str
    instrument: str
    direction: Literal["BUY", "SELL"]
    confidence: float = Field(ge=0, le=100)
    
    spread_analysis: Optional[SpreadAnalysis] = None
    volume_climax: Optional[VolumeClimax] = None
    stopping_volume: Optional[dict] = None
    effort_result: Optional[EffortResult] = None
    
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    
    timeframe: str
    created_at: datetime
    validation_score: float = Field(ge=0, le=100)