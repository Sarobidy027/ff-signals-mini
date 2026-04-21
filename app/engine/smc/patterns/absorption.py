"""Détection de l'absorption (volume élevé, petit range)."""
from typing import List, Dict, Any
from app.data.market_providers import CandleData


class AbsorptionDetector:
    """Détecteur d'absorption."""
    
    @staticmethod
    def detect(candles: List[CandleData]) -> List[Dict[str, Any]]:
        if len(candles) < 5:
            return []
        
        absorptions = []
        avg_vol = sum(c.volume for c in candles[-20:]) / 20 if len(candles) >= 20 else sum(c.volume for c in candles) / len(candles)
        avg_range = sum(c.range for c in candles[-20:]) / 20 if len(candles) >= 20 else sum(c.range for c in candles) / len(candles)
        
        for i in range(-10, 0):
            c = candles[i]
            if c.volume > avg_vol * 1.8 and c.range < avg_range * 0.7:
                absorptions.append({
                    "price": c.close, "timestamp": c.timestamp,
                    "volume_ratio": c.volume / avg_vol, "range_ratio": c.range / avg_range,
                    "direction": "bullish" if c.close > c.open else "bearish",
                    "confidence": 75,
                })
        return absorptions