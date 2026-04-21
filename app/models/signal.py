"""
Modèles de signaux.
"""
from typing import Optional, Literal, List
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Direction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class TradeType(str, Enum):
    SCALP = "SCALP"
    DAY = "DAY"
    SWING = "SWING"


class SignalStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class SignalResult(str, Enum):
    WIN = "WIN"
    LOSS = "LOSS"


class Signal(BaseModel):
    """Signal de trading complet."""
    id: str
    instrument: str
    direction: Direction
    entry_price: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    take_profit: float = Field(gt=0)
    confidence: float = Field(ge=0, le=100)
    trade_type: TradeType
    estimated_duration: str
    entry_time: datetime
    exit_time: Optional[datetime] = None
    status: SignalStatus
    result: Optional[SignalResult] = None
    pips_gained: Optional[float] = None
    risk_reward_ratio: float = Field(ge=0)
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class SignalCreate(BaseModel):
    """Données pour créer un signal."""
    instrument: str
    direction: Direction
    entry_price: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    take_profit: float = Field(gt=0)
    confidence: float = Field(ge=0, le=100)
    trade_type: TradeType
    entry_time: datetime


class SignalUpdate(BaseModel):
    """Mise à jour d'un signal."""
    status: Optional[SignalStatus] = None
    result: Optional[SignalResult] = None
    exit_time: Optional[datetime] = None
    pips_gained: Optional[float] = None


class SignalsResponse(BaseModel):
    """Réponse pour la liste des signaux."""
    active: List[Signal] = []
    pending: List[Signal] = []
    total: int = 0