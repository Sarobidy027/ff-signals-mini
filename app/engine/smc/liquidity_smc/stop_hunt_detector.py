"""Détecteur de Stop Hunts SMC."""
from typing import List, Dict, Any
from app.data.market_providers import CandleData


class StopHuntDetectorSMC:
    """Détection des chasses aux stops."""
    
    @staticmethod
    def detect(candles: List[CandleData]) -> List[Dict[str, Any]]:
        hunts = []
        if len(candles) < 10:
            return hunts
        
        avg_range = sum(c.range for c in candles[-10:]) / 10
        avg_vol = sum(c.volume for c in candles[-10:]) / 10
        
        for i in range(-5, 0):
            c = candles[i]
            if c.range > avg_range * 1.5 and c.volume > avg_vol * 1.3:
                if c.lower_wick > c.body_size * 2:
                    hunts.append({"type": "BULLISH_STOP_HUNT", "price": c.low, "confidence": 75})
                if c.upper_wick > c.body_size * 2:
                    hunts.append({"type": "BEARISH_STOP_HUNT", "price": c.high, "confidence": 75})
        
        return hunts