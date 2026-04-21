"""Analyse du volume relatif."""
from typing import List, Dict, Any
from app.data.market_providers import CandleData


class RelativeVolumeAnalyzer:
    """Analyseur de volume relatif."""
    
    def __init__(self, candles: List[CandleData]):
        self.candles = candles
        self.avg_volume = self._calc_avg()
    
    def _calc_avg(self, period: int = 20) -> float:
        vols = [c.volume for c in self.candles[-period:]]
        return sum(vols) / len(vols) if vols else 1.0
    
    def analyze(self) -> Dict[str, Any]:
        """Analyse complète du volume relatif."""
        recent = self.candles[-1]
        relative = recent.volume / self.avg_volume if self.avg_volume > 0 else 1.0
        
        if relative < 0.5:
            level, significance = "VERY_LOW", 70
        elif relative < 0.8:
            level, significance = "LOW", 50
        elif relative < 1.5:
            level, significance = "NORMAL", 30
        elif relative < 2.5:
            level, significance = "HIGH", 70
        else:
            level, significance = "VERY_HIGH", 90
        
        trend = self._volume_trend()
        
        return {
            "level": level, "relative": round(relative, 2),
            "significance": significance, "trend": trend,
            "current": recent.volume, "average": self.avg_volume,
        }
    
    def _volume_trend(self) -> str:
        if len(self.candles) < 10:
            return "stable"
        recent = sum(c.volume for c in self.candles[-5:]) / 5
        older = sum(c.volume for c in self.candles[-10:-5]) / 5
        ratio = recent / older if older > 0 else 1.0
        return "increasing" if ratio > 1.2 else ("decreasing" if ratio < 0.8 else "stable")
    
    def get_volume_pressure(self) -> Dict[str, float]:
        """Pression acheteuse/vendeuse basée sur le volume."""
        buy = sum(c.volume for c in self.candles[-20:] if c.close > c.open)
        sell = sum(c.volume for c in self.candles[-20:] if c.close < c.open)
        total = buy + sell
        return {"buying": buy/total if total > 0 else 0.5,
                "selling": sell/total if total > 0 else 0.5}