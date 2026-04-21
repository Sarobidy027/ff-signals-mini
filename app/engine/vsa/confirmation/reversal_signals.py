"""Signaux de retournement."""
from typing import List, Dict, Any, Optional
from app.data.market_providers import CandleData


class ReversalSignals:
    """Détecteur de signaux de retournement."""
    
    @staticmethod
    def detect(candles: List[CandleData]) -> Optional[Dict[str, Any]]:
        if len(candles) < 5:
            return None
        
        recent = candles[-1]
        avg_vol = sum(c.volume for c in candles[-20:]) / 20 if len(candles) >= 20 else recent.volume
        avg_range = sum(c.range for c in candles[-20:]) / 20 if len(candles) >= 20 else recent.range
        
        # Climax + petite bougie suivante = retournement
        if recent.volume > avg_vol * 2.5 and recent.range > avg_range * 1.5:
            if len(candles) >= 2:
                next_c = candles[-2]
                if next_c.range < avg_range * 0.7:
                    return {
                        "signal": "CLIMAX_REVERSAL",
                        "direction": "BEARISH" if recent.close > recent.open else "BULLISH",
                        "confidence": 80,
                    }
        
        # Divergence volume/prix
        if len(candles) >= 5:
            price_change = (candles[-1].close - candles[-5].close) / candles[-5].close
            vol_change = (candles[-1].volume - candles[-5].volume) / candles[-5].volume if candles[-5].volume > 0 else 0
            
            if price_change > 0.01 and vol_change < -0.2:
                return {"signal": "BEARISH_DIVERGENCE", "direction": "BEARISH", "confidence": 70}
            if price_change < -0.01 and vol_change > 0.2:
                return {"signal": "BULLISH_DIVERGENCE", "direction": "BULLISH", "confidence": 70}
        
        return None