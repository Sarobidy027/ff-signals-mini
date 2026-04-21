"""Détection du Stopping Volume."""
from typing import List, Optional, Dict, Any
from app.data.market_providers import CandleData


class StoppingVolumeDetector:
    """Détecteur de Stopping Volume (fin de tendance)."""
    
    def __init__(self, candles: List[CandleData]):
        self.candles = candles
    
    def detect(self) -> Optional[Dict[str, Any]]:
        if len(self.candles) < 20:
            return None
        
        avg_vol = sum(c.volume for c in self.candles[-20:]) / 20
        recent = self.candles[-1]
        avg_range = sum(c.range for c in self.candles[-20:]) / 20
        
        high_vol = recent.volume > avg_vol * 2.0
        small_range = recent.range < avg_range * 0.7
        small_body = recent.body_size < recent.range * 0.4
        
        if high_vol and small_range and small_body:
            trend = self._determine_trend()
            
            if trend == "UPTREND":
                return {
                    "type": "STOPPING_VOLUME", "direction": "BEARISH", "confidence": 75,
                    "entry": recent.close, "stop": recent.high * 1.002,
                    "target": recent.close - (recent.high - recent.low) * 2,
                    "volume_ratio": recent.volume / avg_vol,
                }
            elif trend == "DOWNTREND":
                return {
                    "type": "STOPPING_VOLUME", "direction": "BULLISH", "confidence": 75,
                    "entry": recent.close, "stop": recent.low * 0.998,
                    "target": recent.close + (recent.high - recent.low) * 2,
                    "volume_ratio": recent.volume / avg_vol,
                }
        return None
    
    def _determine_trend(self) -> str:
        closes = [c.close for c in self.candles[-10:]]
        sma_5 = sum(closes[-5:]) / 5
        sma_10 = sum(closes) / 10
        if sma_5 > sma_10 * 1.01:
            return "UPTREND"
        elif sma_5 < sma_10 * 0.99:
            return "DOWNTREND"
        return "NEUTRAL"