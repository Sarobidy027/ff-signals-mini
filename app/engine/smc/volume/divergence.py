"""Divergence volume/prix."""
from typing import List, Dict, Any, Tuple
import numpy as np
from app.data.market_providers import CandleData


class VolumeDivergence:
    """Détection des divergences entre volume et prix."""
    
    @staticmethod
    def detect(candles: List[CandleData]) -> Dict[str, Any]:
        if len(candles) < 10:
            return {"detected": False}
        
        prices = [c.close for c in candles]
        volumes = [c.volume for c in candles]
        
        price_trend = VolumeDivergence._trend(prices)
        volume_trend = VolumeDivergence._trend(volumes)
        
        if price_trend == "UP" and volume_trend == "DOWN":
            return {"detected": True, "type": "BEARISH_DIVERGENCE",
                   "confidence": 70, "signal": "Potential reversal down"}
        elif price_trend == "DOWN" and volume_trend == "UP":
            return {"detected": True, "type": "BULLISH_DIVERGENCE",
                   "confidence": 70, "signal": "Potential reversal up"}
        
        return {"detected": False}
    
    @staticmethod
    def _trend(data: List[float]) -> str:
        first = sum(data[:3]) / 3
        last = sum(data[-3:]) / 3
        return "UP" if last > first * 1.05 else ("DOWN" if last < first * 0.95 else "FLAT")
    
    @staticmethod
    def find_divergences(candles: List[CandleData]) -> List[Dict[str, Any]]:
        """Trouve toutes les divergences dans l'historique."""
        divergences = []
        for i in range(10, len(candles)):
            window = candles[i-10:i+1]
            result = VolumeDivergence.detect(window)
            if result["detected"]:
                result["index"] = i
                result["timestamp"] = candles[i].timestamp
                divergences.append(result)
        return divergences