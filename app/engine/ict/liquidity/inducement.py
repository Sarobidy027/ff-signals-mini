"""Inducement detector."""
from typing import List, Dict, Any
from app.data.market_providers import CandleData
from app.models.swing_point import SwingPoint


class InducementDetector:
    @staticmethod
    def detect(candles: List[CandleData], swings: List[SwingPoint]) -> List[Dict[str, Any]]:
        inducements = []
        if len(swings) < 3:
            return inducements
        
        for i in range(len(swings) - 2):
            s1, s2, s3 = swings[i], swings[i+1], swings[i+2]
            
            if s1.point_type == "HIGH" and s2.point_type == "HIGH" and s2.price > s1.price:
                reversal = InducementDetector._check_reversal(candles, s2, "BEARISH")
                if reversal:
                    inducements.append({
                        "type": "BULL_TRAP", "inducement_zone": {"top": s2.price, "bottom": s1.price},
                        "timestamp": s2.timestamp, "target": s3.price if s3.point_type == "LOW" else s1.price,
                        "strength": 0.8,
                    })
            
            if s1.point_type == "LOW" and s2.point_type == "LOW" and s2.price < s1.price:
                reversal = InducementDetector._check_reversal(candles, s2, "BULLISH")
                if reversal:
                    inducements.append({
                        "type": "BEAR_TRAP", "inducement_zone": {"top": s1.price, "bottom": s2.price},
                        "timestamp": s2.timestamp, "target": s3.price if s3.point_type == "HIGH" else s1.price,
                        "strength": 0.8,
                    })
        return inducements
    
    @staticmethod
    def _check_reversal(candles: List[CandleData], swing: SwingPoint, direction: str) -> bool:
        for c in candles:
            if c.timestamp <= swing.timestamp:
                continue
            if direction == "BEARISH":
                if c.close < c.open and c.close < swing.price:
                    return True
            else:
                if c.close > c.open and c.close > swing.price:
                    return True
        return False