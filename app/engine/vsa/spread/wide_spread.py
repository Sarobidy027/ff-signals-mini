"""Détection des spreads larges."""
from typing import List, Dict, Any
from app.data.market_providers import CandleData


class WideSpreadDetector:
    """Détecteur de spreads larges."""
    
    def __init__(self, candles: List[CandleData]):
        self.candles = candles
        self.avg_spread = self._calc_avg_spread()
    
    def _calc_avg_spread(self, period: int = 20) -> float:
        spreads = [c.range for c in self.candles[-period:]] if len(self.candles) >= period else [c.range for c in self.candles]
        return sum(spreads) / len(spreads) if spreads else 0.0
    
    def detect(self) -> List[Dict[str, Any]]:
        """Détecte les spreads larges récents."""
        wides = []
        for i in range(-10, 0):
            c = self.candles[i]
            relative = c.range / self.avg_spread if self.avg_spread > 0 else 1.0
            
            if relative > 1.5:
                signal = "STRONG_MOMENTUM"
                direction = "BULLISH" if c.close > c.open else "BEARISH"
                
                wides.append({
                    "timestamp": c.timestamp, "range": c.range,
                    "relative": round(relative, 2), "signal": signal,
                    "direction": direction, "volume": c.volume, "price": c.close,
                })
        return wides