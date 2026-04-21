"""Détection de captures de liquidité."""
from typing import List, Dict, Any
from app.data.market_providers import CandleData


class LiquidityGrabDetector:
    """Détecteur de Liquidity Grabs."""
    
    @staticmethod
    def detect(candles: List[CandleData]) -> List[Dict[str, Any]]:
        grabs = []
        if len(candles) < 20:
            return grabs
        
        highs = [c.high for c in candles[-20:]]
        lows = [c.low for c in candles[-20:]]
        recent_high = max(highs)
        recent_low = min(lows)
        
        for i in range(-10, 0):
            c = candles[i]
            
            if c.high > recent_high * 1.002:
                for j in range(i+1, 0):
                    if j < len(candles) and candles[j].close < recent_high:
                        grabs.append({
                            "type": "LIQUIDITY_GRAB_ABOVE", "timestamp": c.timestamp,
                            "grabbed_level": recent_high, "direction": "SELL", "confidence": 75,
                        })
                        break
            
            if c.low < recent_low * 0.998:
                for j in range(i+1, 0):
                    if j < len(candles) and candles[j].close > recent_low:
                        grabs.append({
                            "type": "LIQUIDITY_GRAB_BELOW", "timestamp": c.timestamp,
                            "grabbed_level": recent_low, "direction": "BUY", "confidence": 75,
                        })
                        break
        
        return grabs