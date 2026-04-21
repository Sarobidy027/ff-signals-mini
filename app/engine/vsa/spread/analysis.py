"""Analyse du spread (range des bougies)."""
from typing import List, Optional
from app.data.market_providers import CandleData
from app.engine.vsa.models import SpreadAnalysis as SpreadAnalysisModel


class SpreadAnalyzer:
    """Analyseur de spread."""
    
    def __init__(self, candles: List[CandleData]):
        self.candles = candles
        self.avg_spread = self._calc_avg_spread()
    
    def _calc_avg_spread(self, period: int = 20) -> float:
        spreads = [c.range for c in self.candles[-period:]] if len(self.candles) >= period else [c.range for c in self.candles]
        return sum(spreads) / len(spreads) if spreads else 0.0
    
    def analyze(self, candle: Optional[CandleData] = None) -> SpreadAnalysisModel:
        if candle is None:
            candle = self.candles[-1]
        
        spread = candle.range
        relative = spread / self.avg_spread if self.avg_spread > 0 else 1.0
        
        if relative < 0.5:
            spread_type, significance = "NARROW", 60
        elif relative < 0.8:
            spread_type, significance = "NARROW", 40
        elif relative < 1.3:
            spread_type, significance = "NORMAL", 30
        elif relative < 2.0:
            spread_type, significance = "WIDE", 70
        else:
            spread_type, significance = "ULTRA_WIDE", 90
        
        if candle.close > candle.open and candle.close > candle.high * 0.9:
            significance = min(significance + 10, 100)
        elif candle.close < candle.open and candle.close < candle.low * 1.1:
            significance = min(significance + 10, 100)
        
        return SpreadAnalysisModel(
            spread_type=spread_type, spread_value=spread,
            relative_to_avg=round(relative, 2), significance=significance,
        )
    
    def get_spread_trend(self, period: int = 5) -> str:
        """Tendance du spread."""
        if len(self.candles) < period * 2:
            return "stable"
        recent = sum(c.range for c in self.candles[-period:]) / period
        older = sum(c.range for c in self.candles[-period*2:-period]) / period
        ratio = recent / older if older > 0 else 1.0
        return "increasing" if ratio > 1.2 else ("decreasing" if ratio < 0.8 else "stable")