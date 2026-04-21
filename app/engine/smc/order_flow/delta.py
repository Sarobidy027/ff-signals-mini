"""Analyse du Delta (volume acheteur - vendeur)."""
from typing import List, Dict, Any
from app.data.market_providers import CandleData


class DeltaAnalyzer:
    """Analyseur de Delta."""
    
    @staticmethod
    def calculate(candles: List[CandleData]) -> Dict[str, Any]:
        if len(candles) < 10:
            return {"value": 0, "trend": "neutral"}
        
        buying = 0
        selling = 0
        
        for c in candles[-20:]:
            if c.close > c.open:
                buying += c.volume
            else:
                selling += c.volume
        
        total = buying + selling
        delta = (buying - selling) / total if total > 0 else 0
        
        if delta > 0.2:
            trend = "bullish"
        elif delta < -0.2:
            trend = "bearish"
        else:
            trend = "neutral"
        
        return {"value": round(delta, 3), "trend": trend,
                "buying": buying, "selling": selling, "total": total}
    
    @staticmethod
    def delta_divergence(candles: List[CandleData]) -> Dict[str, Any]:
        """Détecte une divergence entre prix et delta."""
        if len(candles) < 10:
            return {"detected": False}
        
        prices = [c.close for c in candles[-10:]]
        deltas = []
        for c in candles[-10:]:
            d = 1 if c.close > c.open else -1
            deltas.append(d * c.volume)
        
        price_up = prices[-1] > prices[0]
        delta_up = sum(deltas[-5:]) > sum(deltas[:5])
        
        if price_up and not delta_up:
            return {"detected": True, "type": "BEARISH_DIVERGENCE", "confidence": 70}
        elif not price_up and delta_up:
            return {"detected": True, "type": "BULLISH_DIVERGENCE", "confidence": 70}
        
        return {"detected": False}