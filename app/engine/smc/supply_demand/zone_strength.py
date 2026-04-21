"""Calcul de la force des zones."""
from typing import List
from app.engine.smc.models import SupplyDemandZone


class ZoneStrength:
    """Évaluation de la force des zones."""
    
    @staticmethod
    def evaluate(zone: SupplyDemandZone, candles: List[CandleData]) -> float:
        """Évalue la force d'une zone."""
        strength = zone.strength
        
        age_hours = (candles[-1].timestamp - zone.created_at).total_seconds() / 3600
        if age_hours < 1:
            strength += 10
        elif age_hours < 4:
            strength += 5
        
        avg_vol = sum(c.volume for c in candles[-20:]) / 20 if len(candles) >= 20 else zone.volume_on_creation
        if zone.volume_on_creation > avg_vol * 1.5:
            strength += 10
        
        return min(strength, 100)
    
    @staticmethod
    def get_strongest(zones: List[SupplyDemandZone], candles: List[CandleData], zone_type: str) -> SupplyDemandZone:
        """Retourne la zone la plus forte d'un type donné."""
        filtered = [z for z in zones if z.zone_type == zone_type]
        if not filtered:
            return None
        
        for z in filtered:
            z.strength = ZoneStrength.evaluate(z, candles)
        
        return max(filtered, key=lambda z: z.strength)