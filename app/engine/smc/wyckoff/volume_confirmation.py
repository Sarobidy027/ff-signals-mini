"""Confirmation par le volume des phases Wyckoff."""
from typing import List, Dict, Any
from app.data.market_providers import CandleData


class VolumeConfirmation:
    """Analyse du volume pour confirmer les phases Wyckoff."""
    
    @staticmethod
    def confirm_phase(candles: List[CandleData], phase_type: str) -> Dict[str, Any]:
        volume_profile = VolumeConfirmation._get_volume_profile(candles)
        
        if "ACCUMULATION" in phase_type:
            expected = "increasing" if "E" not in phase_type else "increasing"
            confirmed = volume_profile["trend"] == expected
            confidence = 75 if confirmed else 50
        elif "DISTRIBUTION" in phase_type:
            expected = "decreasing" if "E" not in phase_type else "increasing"
            confirmed = volume_profile["trend"] == expected
            confidence = 75 if confirmed else 50
        else:
            confirmed, confidence = False, 50
        
        return {"confirmed": confirmed, "confidence": confidence,
                "volume_trend": volume_profile["trend"], "climax": volume_profile["climax"]}
    
    @staticmethod
    def _get_volume_profile(candles: List[CandleData]) -> dict:
        volumes = [c.volume for c in candles[-20:]]
        avg = sum(volumes) / len(volumes)
        recent = sum(volumes[-5:]) / 5
        trend = "increasing" if recent > avg * 1.2 else ("decreasing" if recent < avg * 0.8 else "stable")
        return {"trend": trend, "avg": avg, "recent": recent, "climax": max(volumes) > avg * 2.5}
    
    @staticmethod
    def detect_climax(candles: List[CandleData]) -> Dict[str, Any]:
        volumes = [c.volume for c in candles[-20:]]
        avg = sum(volumes) / len(volumes)
        recent = candles[-1]
        
        if recent.volume > avg * 2.5:
            climax_type = "BUYING" if recent.close > recent.open else "SELLING"
            return {"detected": True, "type": climax_type, "ratio": recent.volume / avg}
        return {"detected": False}