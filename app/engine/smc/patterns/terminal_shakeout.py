"""Détection du Terminal Shakeout."""
from typing import List, Optional
from app.data.market_providers import CandleData
from app.engine.smc.models import SpringUpthrust, SpringUpthrustType


class TerminalShakeoutDetector:
    """Détecteur de Terminal Shakeout (Spring violent)."""
    
    @staticmethod
    def detect(candles: List[CandleData]) -> Optional[SpringUpthrust]:
        if len(candles) < 10:
            return None
        
        recent = candles[-5:]
        avg_vol = sum(c.volume for c in candles[-20:]) / 20 if len(candles) >= 20 else sum(c.volume for c in candles) / len(candles)
        
        for c in recent:
            if c.lower_wick > c.body_size * 3 and c.volume > avg_vol * 2:
                return SpringUpthrust(
                    pattern_type=SpringUpthrustType.TERMINAL_SHAKEOUT, direction="BUY",
                    confidence=85, timestamp=c.timestamp, level=c.low,
                    penetration_depth=(c.low - c.close) / c.close * 100,
                    volume_confirmation=True, recovery_strength=90,
                    entry_price=c.close, stop_loss=c.low * 0.995,
                    take_profit=c.close + (c.close - c.low * 0.995) * 3,
                )
        return None