"""Détection de chasses aux stops."""
from typing import List, Dict, Any
from app.data.market_providers import CandleData


class StopHuntDetector:
    """Détecteur de Stop Hunts."""
    
    @staticmethod
    def detect(candles: List[CandleData]) -> List[Dict[str, Any]]:
        hunts = []
        if len(candles) < 10:
            return hunts
        
        for i in range(5, len(candles) - 3):
            recent = candles[i-5:i]
            curr = candles[i]
            nxt = candles[i+1:i+4]
            
            avg_range = sum(c.range for c in recent) / 5
            avg_vol = sum(c.volume for c in recent) / 5
            
            if curr.range > avg_range * 1.5 and curr.volume > avg_vol * 1.3:
                if curr.lower_wick > curr.body_size * 2:
                    if all(c.close > c.open for c in nxt):
                        hunts.append({
                            "type": "BULLISH_STOP_HUNT", "timestamp": curr.timestamp,
                            "wick_low": curr.low, "reversal_price": curr.close,
                            "strength": curr.lower_wick / curr.range, "confidence": 80,
                        })
                
                if curr.upper_wick > curr.body_size * 2:
                    if all(c.close < c.open for c in nxt):
                        hunts.append({
                            "type": "BEARISH_STOP_HUNT", "timestamp": curr.timestamp,
                            "wick_high": curr.high, "reversal_price": curr.close,
                            "strength": curr.upper_wick / curr.range, "confidence": 80,
                        })
        return hunts