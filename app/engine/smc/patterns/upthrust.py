"""Détection des Upthrusts (faux breakout)."""
from typing import List, Optional
from app.data.market_providers import CandleData
from app.engine.smc.models import SpringUpthrust, SpringUpthrustType


class UpthrustDetector:
    """Détecteur d'Upthrusts."""
    
    @staticmethod
    def detect(candles: List[CandleData], resistance: float) -> Optional[SpringUpthrust]:
        if len(candles) < 5:
            return None
        
        recent = candles[-10:]
        avg_vol = sum(c.volume for c in candles[-20:]) / 20 if len(candles) >= 20 else sum(c.volume for c in candles) / len(candles)
        
        for i in range(len(recent) - 3):
            if recent[i].high > resistance:
                for j in range(i+1, min(i+4, len(recent))):
                    if recent[j].close < resistance:
                        penetration = (recent[i].high - resistance) / resistance * 100
                        vol_conf = recent[i].volume > avg_vol * 1.2
                        rejection = (resistance - recent[j].close) / resistance * 100
                        
                        confidence = 70
                        if vol_conf:
                            confidence += 15
                        if penetration > 0.2:
                            confidence += 10
                        
                        return SpringUpthrust(
                            pattern_type=SpringUpthrustType.UPTHRUST, direction="SELL",
                            confidence=min(confidence, 95), timestamp=recent[i].timestamp,
                            level=resistance, penetration_depth=penetration,
                            volume_confirmation=vol_conf, recovery_strength=min(rejection*50, 100),
                            entry_price=recent[j].close,
                            stop_loss=recent[i].high * 1.002,
                            take_profit=resistance - (recent[i].high - resistance) * 2,
                        )
        return None