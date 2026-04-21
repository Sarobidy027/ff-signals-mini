"""Détection des spreads étroits."""
from typing import List, Dict, Any
from app.data.market_providers import CandleData


class NarrowSpreadDetector:
    """Détecteur de spreads étroits."""
    
    def __init__(self, candles: List[CandleData]):
        self.candles = candles
        self.avg_spread = self._calc_avg_spread()
    
    def _calc_avg_spread(self, period: int = 20) -> float:
        spreads = [c.range for c in self.candles[-period:]] if len(self.candles) >= period else [c.range for c in self.candles]
        return sum(spreads) / len(spreads) if spreads else 0.0
    
    def detect(self) -> List[Dict[str, Any]]:
        """Détecte les spreads étroits récents."""
        narrows = []
        for i in range(-10, 0):
            c = self.candles[i]
            relative = c.range / self.avg_spread if self.avg_spread > 0 else 1.0
            
            if relative < 0.7:
                signal = "INDECISION"
                if c.volume > self._avg_volume() * 1.5:
                    signal = "ABSORPTION"
                
                narrows.append({
                    "timestamp": c.timestamp, "range": c.range,
                    "relative": round(relative, 2), "signal": signal,
                    "volume": c.volume, "price": c.close,
                })
        return narrows
    
    def _avg_volume(self, period: int = 20) -> float:
        vols = [c.volume for c in self.candles[-period:]]
        return sum(vols) / len(vols) if vols else 1.0