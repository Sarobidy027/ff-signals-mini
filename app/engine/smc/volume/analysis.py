"""Analyse de volume SMC."""
from typing import List, Dict, Any
import numpy as np
from app.data.market_providers import CandleData


class VolumeAnalysis:
    """Analyse complète du volume."""
    
    def __init__(self, candles: List[CandleData]):
        self.candles = candles
        self.avg_volume = self._calc_avg()
    
    def _calc_avg(self, period: int = 20) -> float:
        vols = [c.volume for c in self.candles[-period:]]
        return sum(vols) / len(vols) if vols else 1.0
    
    def analyze(self) -> Dict[str, Any]:
        return {
            "trend": self._volume_trend(),
            "relative": self._relative_volume(),
            "pressure": self._buying_selling_pressure(),
            "spike": self._detect_spike(),
            "confidence": self._calc_confidence(),
        }
    
    def _volume_trend(self) -> str:
        if len(self.candles) < 10:
            return "stable"
        recent = sum(c.volume for c in self.candles[-5:]) / 5
        older = sum(c.volume for c in self.candles[-10:-5]) / 5
        ratio = recent / older if older > 0 else 1.0
        return "increasing" if ratio > 1.3 else ("decreasing" if ratio < 0.7 else "stable")
    
    def _relative_volume(self) -> float:
        return self.candles[-1].volume / self.avg_volume if self.avg_volume > 0 else 1.0
    
    def _buying_selling_pressure(self) -> Dict[str, float]:
        buy = sum(c.volume for c in self.candles[-20:] if c.close > c.open)
        sell = sum(c.volume for c in self.candles[-20:] if c.close < c.open)
        total = buy + sell
        return {"buying": buy/total if total > 0 else 0.5,
                "selling": sell/total if total > 0 else 0.5}
    
    def _detect_spike(self) -> Dict[str, Any]:
        recent = self.candles[-1]
        if recent.volume > self.avg_volume * 2:
            return {"detected": True, "ratio": recent.volume/self.avg_volume,
                   "direction": "up" if recent.close > recent.open else "down"}
        return {"detected": False}
    
    def _calc_confidence(self) -> float:
        score = 50
        if self._volume_trend() != "stable":
            score += 15
        if self._relative_volume() > 1.5:
            score += 15
        return min(score, 95)