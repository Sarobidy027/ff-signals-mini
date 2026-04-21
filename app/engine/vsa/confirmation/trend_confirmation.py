"""Confirmation de tendance."""
from typing import List, Dict, Any
from app.data.market_providers import CandleData


class TrendConfirmation:
    """Analyseur de confirmation de tendance."""
    
    @staticmethod
    def confirm(candles: List[CandleData]) -> Dict[str, Any]:
        if len(candles) < 10:
            return {"confirmed": False, "direction": None, "confidence": 0}
        
        closes = [c.close for c in candles]
        volumes = [c.volume for c in candles]
        
        price_up = closes[-1] > closes[0]
        vol_up = sum(volumes[-5:]) / 5 > sum(volumes[:5]) / 5
        
        if price_up and vol_up:
            return {"confirmed": True, "direction": "BULLISH", "confidence": 80}
        elif not price_up and vol_up:
            return {"confirmed": True, "direction": "BEARISH", "confidence": 80}
        elif price_up and not vol_up:
            return {"confirmed": False, "direction": "BULLISH", "confidence": 40,
                   "warning": "Price up but volume down - weak trend"}
        elif not price_up and not vol_up:
            return {"confirmed": False, "direction": None, "confidence": 30}
        
        return {"confirmed": False, "direction": None, "confidence": 0}