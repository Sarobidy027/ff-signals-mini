"""
Modèles pour le Smart Money Concept (SMC).
"""
from typing import Literal, Optional, List, Tuple
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class WyckoffPhaseType(str, Enum):
    ACCUMULATION_A = "ACCUMULATION_A"
    ACCUMULATION_B = "ACCUMULATION_B"
    ACCUMULATION_C = "ACCUMULATION_C"
    ACCUMULATION_D = "ACCUMULATION_D"
    ACCUMULATION_E = "ACCUMULATION_E"
    DISTRIBUTION_A = "DISTRIBUTION_A"
    DISTRIBUTION_B = "DISTRIBUTION_B"
    DISTRIBUTION_C = "DISTRIBUTION_C"
    DISTRIBUTION_D = "DISTRIBUTION_D"
    DISTRIBUTION_E = "DISTRIBUTION_E"


class SpringUpthrustType(str, Enum):
    SPRING = "SPRING"
    UPTHRUST = "UPTHRUST"
    TERMINAL_SHAKEOUT = "TERMINAL_SHAKEOUT"


class MarketMakerModelType(str, Enum):
    MMM_BUY = "MMM_BUY"
    MMM_SELL = "MMM_SELL"
    STOP_HUNT = "STOP_HUNT"
    LIQUIDITY_GRAB = "LIQUIDITY_GRAB"


class WyckoffPhase(BaseModel):
    """Phase Wyckoff détectée."""
    phase_type: WyckoffPhaseType
    confidence: float = Field(ge=0, le=100)
    start_time: datetime
    end_time: Optional[datetime] = None
    price_range: Tuple[float, float]
    volume_profile: str
    key_levels: dict = Field(default_factory=dict)


class SpringUpthrust(BaseModel):
    """Spring ou Upthrust détecté."""
    pattern_type: SpringUpthrustType
    direction: Literal["BUY", "SELL"]
    confidence: float = Field(ge=0, le=100)
    timestamp: datetime
    level: float
    penetration_depth: float
    volume_confirmation: bool
    recovery_strength: float = Field(ge=0, le=100)
    entry_price: float
    stop_loss: float
    take_profit: float


class SupplyDemandZone(BaseModel):
    """Zone d'offre ou de demande."""
    zone_type: Literal["SUPPLY", "DEMAND"]
    top_price: float
    bottom_price: float
    strength: float = Field(ge=0, le=100)
    created_at: datetime
    tested_count: int = 0
    fresh: bool = True
    volume_on_creation: float


class MarketMakerModel(BaseModel):
    """Modèle de Market Maker."""
    model_type: MarketMakerModelType
    direction: Literal["BULLISH", "BEARISH"]
    confidence: float = Field(ge=0, le=100)
    phase: str
    entry_zone: Tuple[float, float]
    stop_loss: float
    targets: List[float]
    timestamp: datetime


class SMCSignal(BaseModel):
    """Signal SMC complet."""
    id: str
    instrument: str
    direction: Literal["BUY", "SELL"]
    confidence: float = Field(ge=0, le=100)
    
    wyckoff_phase: Optional[WyckoffPhase] = None
    spring_upthrust: Optional[SpringUpthrust] = None
    supply_demand_zone: Optional[SupplyDemandZone] = None
    market_maker_model: Optional[MarketMakerModel] = None
    
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_reward_ratio: float
    
    timeframe: str
    created_at: datetime
    validation_score: float = Field(ge=0, le=100)