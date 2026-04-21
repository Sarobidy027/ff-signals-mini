"""Zones fraîches (non testées)."""
from typing import List
from app.data.market_providers import CandleData
from app.engine.smc.models import SupplyDemandZone


class FreshZones:
    """Filtre pour zones fraîches."""
    
    @staticmethod
    def filter_fresh(zones: List[SupplyDemandZone], candles: List[CandleData]) -> List[SupplyDemandZone]:
        """Retourne uniquement les zones non testées."""
        fresh = []
        current_price = candles[-1].close
        
        for zone in zones:
            tested = False
            for c in candles:
                if c.timestamp <= zone.created_at:
                    continue
                if zone.bottom_price <= c.low <= zone.top_price or \
                   zone.bottom_price <= c.high <= zone.top_price:
                    tested = True
                    break
            
            if not tested:
                zone.fresh = True
                if (zone.zone_type == "DEMAND" and zone.top_price < current_price) or \
                   (zone.zone_type == "SUPPLY" and zone.bottom_price > current_price):
                    fresh.append(zone)
        
        return fresh