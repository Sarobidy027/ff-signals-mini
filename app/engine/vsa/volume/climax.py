"""Détection des Climax de volume."""
from typing import List, Optional
from datetime import datetime
from app.data.market_providers import CandleData
from app.engine.vsa.models import VolumeClimax


class ClimaxDetector:
    """Détecteur de Buying/Selling Climax."""
    
    def __init__(self, candles: List[CandleData]):
        self.candles = candles
    
    def detect(self) -> Optional[VolumeClimax]:
        if len(self.candles) < 20:
            return None
        
        avg_vol = sum(c.volume for c in self.candles[-20:]) / 20
        avg_spread = sum(c.range for c in self.candles[-20:]) / 20
        recent = self.candles[-1]
        
        vol_ratio = recent.volume / avg_vol if avg_vol > 0 else 1.0
        spread_ratio = recent.range / avg_spread if avg_spread > 0 else 1.0
        
        if vol_ratio > 2.5 and spread_ratio > 1.5:
            if recent.close > recent.open:
                climax_type = "BUYING"
                expected = "BEARISH"
                confidence = 75
                if recent.upper_wick > recent.body_size * 1.5:
                    confidence += 15
            else:
                climax_type = "SELLING"
                expected = "BULLISH"
                confidence = 75
                if recent.lower_wick > recent.body_size * 1.5:
                    confidence += 15
            
            return VolumeClimax(
                climax_type=climax_type, volume_ratio=round(vol_ratio, 2),
                spread_ratio=round(spread_ratio, 2), confidence=min(confidence, 95),
                timestamp=recent.timestamp, price=recent.close, expected_reversal=expected,
            )
        return None
    
    def detect_historical(self, lookback: int = 50) -> List[VolumeClimax]:
        """Détecte tous les climax dans l'historique."""
        climaxes = []
        if len(self.candles) < 20:
            return climaxes
        
        for i in range(20, len(self.candles)):
            window = self.candles[i-20:i]
            avg_vol = sum(c.volume for c in window) / 20
            avg_spread = sum(c.range for c in window) / 20
            c = self.candles[i]
            
            vol_ratio = c.volume / avg_vol if avg_vol > 0 else 1.0
            spread_ratio = c.range / avg_spread if avg_spread > 0 else 1.0
            
            if vol_ratio > 2.5 and spread_ratio > 1.5:
                climaxes.append(VolumeClimax(
                    climax_type="BUYING" if c.close > c.open else "SELLING",
                    volume_ratio=round(vol_ratio, 2), spread_ratio=round(spread_ratio, 2),
                    confidence=75, timestamp=c.timestamp, price=c.close,
                    expected_reversal="BEARISH" if c.close > c.open else "BULLISH",
                ))
        return climaxes