"""Analyse de l'absorption."""
from typing import List, Dict, Any
from app.data.market_providers import CandleData


class AbsorptionAnalyzer:
    """Analyseur d'absorption (volume élevé, petit range)."""
    
    @staticmethod
    def detect(candles: List[CandleData]) -> List[Dict[str, Any]]:
        absorptions = []
        if len(candles) < 20:
            return absorptions
        
        avg_vol = sum(c.volume for c in candles[-20:]) / 20
        avg_range = sum(c.range for c in candles[-20:]) / 20
        
        for i in range(-10, 0):
            c = candles[i]
            if c.volume > avg_vol * 1.8 and c.range < avg_range * 0.7:
                direction = "BULLISH" if c.close > c.open else "BEARISH"
                absorptions.append({
                    "timestamp": c.timestamp, "price": c.close,
                    "direction": direction, "confidence": 75,
                    "volume_ratio": c.volume / avg_vol,
                    "range_ratio": c.range / avg_range,
                })
        return absorptions