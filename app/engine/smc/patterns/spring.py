"""Détection des Springs (faux breakdown)."""
from typing import List, Optional
from datetime import datetime
from app.data.market_providers import CandleData
from app.engine.smc.models import SpringUpthrust, SpringUpthrustType


class SpringDetector:
    """Détecteur de Springs."""
    
    @staticmethod
    def detect(candles: List[CandleData], support: float) -> Optional[SpringUpthrust]:
        if len(candles) < 5:
            return None
        
        recent = candles[-10:]
        avg_vol = sum(c.volume for c in candles[-20:]) / 20 if len(candles) >= 20 else sum(c.volume for c in candles) / len(candles)
        
        for i in range(len(recent) - 3):
            if recent[i].low < support:
                for j in range(i+1, min(i+4, len(recent))):
                    if recent[j].close > support:
                        penetration = (support - recent[i].low) / support * 100
                        vol_conf = recent[i].volume > avg_vol * 1.2
                        recovery = (recent[j].close - support) / support * 100
                        
                        confidence = 70
                        if vol_conf:
                            confidence += 15
                        if penetration > 0.2:
                            confidence += 10
                        
                        return SpringUpthrust(
                            pattern_type=SpringUpthrustType.SPRING, direction="BUY",
                            confidence=min(confidence, 95), timestamp=recent[i].timestamp,
                            level=support, penetration_depth=penetration,
                            volume_confirmation=vol_conf, recovery_strength=min(recovery*50, 100),
                            entry_price=recent[j].close,
                            stop_loss=recent[i].low * 0.998,
                            take_profit=support + (support - recent[i].low) * 2,
                        )
        return None