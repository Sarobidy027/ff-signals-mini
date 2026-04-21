"""Détection des barres Upthrust."""
from typing import List, Dict, Any
from app.data.market_providers import CandleData


class UpthrustBarDetector:
    """Détecteur d'Upthrust bars."""
    
    @staticmethod
    def detect(candles: List[CandleData]) -> List[Dict[str, Any]]:
        upthrusts = []
        for i in range(1, len(candles)):
            c = candles[i]
            prev = candles[i-1]
            
            if c.high > prev.high and c.close < c.open and c.upper_wick > c.body_size * 1.5:
                confidence = 70
                if c.volume > sum(x.volume for x in candles[max(0, i-10):i]) / min(10, i):
                    confidence += 15
                
                upthrusts.append({
                    "timestamp": c.timestamp, "price": c.close,
                    "direction": "SELL", "confidence": min(confidence, 90),
                    "entry": c.close, "stop": c.high * 1.002,
                    "target": c.close - (c.high - c.low) * 1.5,
                })
        return upthrusts