"""Détection des barres No Demand."""
from typing import List, Dict, Any
from app.data.market_providers import CandleData


class NoDemandDetector:
    """Détecteur de No Demand bars."""
    
    @staticmethod
    def detect(candles: List[CandleData]) -> List[Dict[str, Any]]:
        no_demands = []
        avg_vol = sum(c.volume for c in candles[-20:]) / 20 if len(candles) >= 20 else 1.0
        
        for c in candles[-10:]:
            if c.close > c.open and c.volume < avg_vol * 0.7 and c.range < c.body_size * 1.5:
                no_demands.append({
                    "timestamp": c.timestamp, "price": c.close,
                    "direction": "SELL", "confidence": 65,
                    "signal": "NO_DEMAND", "volume_ratio": c.volume / avg_vol,
                })
        return no_demands