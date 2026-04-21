"""Zones d'induction SMC."""
from typing import List, Dict, Any
from app.data.market_providers import CandleData


class InducementDetectorSMC:
    """Détecteur de zones d'induction."""
    
    @staticmethod
    def detect(candles: List[CandleData]) -> List[Dict[str, Any]]:
        inducements = []
        if len(candles) < 20:
            return inducements
        
        recent_high = max(c.high for c in candles[-10:])
        recent_low = min(c.low for c in candles[-10:])
        
        inducements.append({
            "type": "BULLISH_INDUCEMENT", "price": recent_low * 0.998,
            "description": "Piège vendeur", "confidence": 65,
        })
        inducements.append({
            "type": "BEARISH_INDUCEMENT", "price": recent_high * 1.002,
            "description": "Piège acheteur", "confidence": 65,
        })
        
        return inducements