"""
Modèle Order Block.
"""
from typing import Literal, Optional
from datetime import datetime

from pydantic import BaseModel, Field


class OrderBlock(BaseModel):
    """Order Block ICT."""
    id: str
    instrument: str
    direction: Literal["BULLISH", "BEARISH"]
    ob_type: Literal["BASE", "BREAKER", "MITIGATION", "REJECTION", "VACUUM"]
    high_price: float
    low_price: float
    open_price: float
    close_price: float
    volume: Optional[float] = None
    timestamp: datetime
    timeframe: str
    strength: float = Field(ge=0, le=1)
    tested_count: int = 0
    is_active: bool = True
    mitigated: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }