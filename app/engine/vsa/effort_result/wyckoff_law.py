"""Loi de Wyckoff : Effort vs Résultat."""
from typing import List, Optional
from app.data.market_providers import CandleData
from app.engine.vsa.models import EffortResult


class WyckoffLawAnalyzer:
    """Analyseur de la loi Effort vs Résultat."""
    
    def __init__(self, candles: List[CandleData]):
        self.candles = candles
    
    def analyze(self) -> Optional[EffortResult]:
        if len(self.candles) < 20:
            return None
        
        avg_vol = sum(c.volume for c in self.candles[-20:]) / 20
        avg_spread = sum(c.range for c in self.candles[-20:]) / 20
        
        results = []
        for i in range(-3, 0):
            c = self.candles[i]
            effort = c.volume / avg_vol if avg_vol > 0 else 1.0
            result = c.range / avg_spread if avg_spread > 0 else 1.0
            ratio = effort / result if result > 0 else 1.0
            
            if ratio > 2.0:
                signal, direction = "REVERSAL", "BEARISH" if c.close > c.open else "BULLISH"
                confidence = 70 + min(ratio * 5, 20)
            elif ratio < 0.5:
                signal, direction = "CONTINUATION", "BULLISH" if c.close > c.open else "BEARISH"
                confidence = 60 + min((1-ratio) * 30, 20)
            else:
                signal, direction, confidence = "NEUTRAL", None, 50
            
            results.append({
                "effort": effort, "result": result, "ratio": ratio,
                "signal": signal, "direction": direction, "confidence": confidence,
            })
        
        best = max(results, key=lambda x: x["confidence"])
        return EffortResult(
            effort=round(best["effort"], 2), result=round(best["result"], 2),
            ratio=round(best["ratio"], 2), signal=best["signal"],
            direction=best["direction"], confidence=min(best["confidence"], 95),
        )