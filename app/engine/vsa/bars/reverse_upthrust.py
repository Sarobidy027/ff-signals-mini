"""Détection des Reverse Upthrust (Springs)."""
from typing import List, Dict, Any
from app.data.market_providers import CandleData


class ReverseUpthrustDetector:
    """Détecteur de Reverse Upthrust (Springs)."""
    
    @staticmethod
    def detect(candles: List[CandleData]) -> List[Dict[str, Any]]:
        springs = []
        for i in range(1, len(candles)):
            c = candles[i]
            prev = candles[i-1]
            
            if c.low < prev.low and c.close > c.open and c.lower_wick > c.body_size * 1.5:
                confidence = 70
                if c.volume > sum(x.volume for x in candles[max(0, i-10):i]) / min(10, i):
                    confidence += 15
                
                springs.append({
                    "timestamp": c.timestamp, "price": c.close,
                    "direction": "BUY", "confidence": min(confidence, 90),
                    "entry": c.close, "stop": c.low * 0.998,
                    "target": c.close + (c.high - c.low) * 1.5,
                })
        return springs