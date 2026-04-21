"""Stop Hunt detector."""
from typing import List, Dict, Any
import numpy as np
from app.data.market_providers import CandleData


class StopHuntDetector:
    @staticmethod
    def detect(candles: List[CandleData]) -> List[Dict[str, Any]]:
        hunts = []
        if len(candles) < 10:
            return hunts
        
        for i in range(5, len(candles) - 3):
            recent = candles[i-5:i]
            curr = candles[i]
            nxt = candles[i+1:i+4]
            
            avg_range = np.mean([c.range for c in recent])
            
            if curr.range > avg_range * 1.5:
                if curr.lower_wick > curr.body_size * 2:
                    if all(c.close > c.open for c in nxt):
                        hunts.append({
                            "type": "BULLISH_STOP_HUNT", "timestamp": curr.timestamp,
                            "wick_low": curr.low, "reversal_price": curr.close,
                            "strength": curr.lower_wick / curr.range,
                        })
                
                if curr.upper_wick > curr.body_size * 2:
                    if all(c.close < c.open for c in nxt):
                        hunts.append({
                            "type": "BEARISH_STOP_HUNT", "timestamp": curr.timestamp,
                            "wick_high": curr.high, "reversal_price": curr.close,
                            "strength": curr.upper_wick / curr.range,
                        })
        return hunts