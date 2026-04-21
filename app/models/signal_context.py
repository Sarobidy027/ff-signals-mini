"""
Modèle Signal Context.
"""
from typing import Optional, List
from datetime import datetime

from pydantic import BaseModel

from app.models.order_block import OrderBlock
from app.models.fvg import FairValueGap


class SignalContext(BaseModel):
    """Contexte complet d'un signal."""
    instrument: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    trade_type: str
    entry_time: datetime
    risk_reward_ratio: float
    
    active_order_blocks: List[OrderBlock] = []
    active_fvgs: List[FairValueGap] = []
    nearest_liquidity: Optional[float] = None
    htf_bias: Optional[str] = None
    in_killzone: bool = False
    fundamental_ok: bool = True
    
    anticipation_minutes: int = 5
    signal_source: str = "ICT"