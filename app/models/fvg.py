"""
Modèle Fair Value Gap.
"""
from typing import Literal, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class FairValueGap(BaseModel):
    """Fair Value Gap (FVG)."""
    id: str
    instrument: str
    direction: Literal["BULLISH", "BEARISH"]
    gap_top: float
    gap_bottom: float
    start_timestamp: datetime
    end_timestamp: datetime
    timeframe: str
    is_filled: bool = False
    filled_timestamp: Optional[datetime] = None
    volume_imbalance: float = 0.0
    quality_score: float = Field(ge=0, le=100, default=50)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
