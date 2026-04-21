"""Vacuum Blocks."""
from typing import List
import uuid
import numpy as np
from app.data.market_providers import CandleData
from app.models.order_block import OrderBlock


class VacuumBlock:
    @staticmethod
    def detect(candles: List[CandleData], instrument: str, timeframe: str) -> List[OrderBlock]:
        vacuums = []
        if len(candles) < 5:
            return vacuums
        
        avg_volume = np.mean([c.volume for c in candles])
        
        for i in range(len(candles) - 3):
            c1, c2, c3 = candles[i], candles[i+1], candles[i+2]
            avg_vol = (c1.volume + c2.volume + c3.volume) / 3
            
            if avg_vol < avg_volume * 0.5:
                high = max(c1.high, c2.high, c3.high)
                low = min(c1.low, c2.low, c3.low)
                direction = "BULLISH" if c3.close > c1.open else "BEARISH"
                
                vacuums.append(OrderBlock(
                    id=str(uuid.uuid4()), instrument=instrument, direction=direction, ob_type="VACUUM",
                    high_price=high, low_price=low, open_price=c1.open, close_price=c3.close,
                    volume=avg_vol, timestamp=c1.timestamp, timeframe=timeframe,
                    strength=0.5, is_active=True,
                ))
        return vacuums