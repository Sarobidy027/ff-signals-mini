"""Détection de climax de volume."""
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.data.market_providers import CandleData


class VolumeClimaxDetector:
    """Détecteur de Buying/Selling Climax."""
    
    def __init__(self, candles: List[CandleData]):
        self.candles = candles
    
    def detect(self) -> Optional[Dict[str, Any]]:
        if len(self.candles) < 20:
            return None
        
        avg_vol = sum(c.volume for c in self.candles[-20:]) / 20
        recent = self.candles[-1]
        
        if recent.volume > avg_vol * 2.5:
            if recent.close > recent.open:
                climax_type = "BUYING_CLIMAX"
                expected = "BEARISH"
                confidence = 75
                if recent.upper_wick > recent.body_size * 1.5:
                    confidence += 15
            else:
                climax_type = "SELLING_CLIMAX"
                expected = "BULLISH"
                confidence = 75
                if recent.lower_wick > recent.body_size * 1.5:
                    confidence += 15
            
            return {
                "type": climax_type, "expected_reversal": expected,
                "confidence": min(confidence, 95), "timestamp": recent.timestamp,
                "volume_ratio": recent.volume / avg_vol, "price": recent.close,
            }
        return None
    
    def detect_historical(self, lookback: int = 50) -> List[Dict[str, Any]]:
        """Détecte tous les climax dans l'historique."""
        climaxes = []
        if len(self.candles) < 20:
            return climaxes
        
        for i in range(20, len(self.candles)):
            window = self.candles[i-20:i]
            avg_vol = sum(c.volume for c in window) / 20
            c = self.candles[i]
            
            if c.volume > avg_vol * 2.5:
                climaxes.append({
                    "index": i, "timestamp": c.timestamp,
                    "type": "BUYING" if c.close > c.open else "SELLING",
                    "ratio": c.volume / avg_vol, "price": c.close,
                })
        return climaxes