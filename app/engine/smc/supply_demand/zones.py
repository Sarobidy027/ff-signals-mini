"""Zones Supply/Demand."""
from typing import List
from datetime import datetime
from app.data.market_providers import CandleData
from app.engine.smc.models import SupplyDemandZone


class SupplyDemandZones:
    """Détection des zones Supply/Demand."""
    
    @staticmethod
    def find_all(candles: List[CandleData]) -> List[SupplyDemandZone]:
        zones = []
        zones.extend(SupplyDemandZones._find_demand(candles))
        zones.extend(SupplyDemandZones._find_supply(candles))
        return zones
    
    @staticmethod
    def _find_demand(candles: List[CandleData]) -> List[SupplyDemandZone]:
        zones = []
        for i in range(2, len(candles) - 1):
            if candles[i].is_bearish and candles[i+1].is_bullish:
                if candles[i+1].close > candles[i].high:
                    strength = SupplyDemandZones._calc_strength(candles, i, "DEMAND")
                    if strength > 50:
                        zones.append(SupplyDemandZone(
                            zone_type="DEMAND", top_price=candles[i].high,
                            bottom_price=candles[i].low, strength=strength,
                            created_at=candles[i].timestamp, fresh=True,
                            volume_on_creation=candles[i].volume,
                        ))
        return zones
    
    @staticmethod
    def _find_supply(candles: List[CandleData]) -> List[SupplyDemandZone]:
        zones = []
        for i in range(2, len(candles) - 1):
            if candles[i].is_bullish and candles[i+1].is_bearish:
                if candles[i+1].close < candles[i].low:
                    strength = SupplyDemandZones._calc_strength(candles, i, "SUPPLY")
                    if strength > 50:
                        zones.append(SupplyDemandZone(
                            zone_type="SUPPLY", top_price=candles[i].high,
                            bottom_price=candles[i].low, strength=strength,
                            created_at=candles[i].timestamp, fresh=True,
                            volume_on_creation=candles[i].volume,
                        ))
        return zones
    
    @staticmethod
    def _calc_strength(candles: List[CandleData], idx: int, zone_type: str) -> float:
        c = candles[idx]
        nxt = candles[idx+1]
        strength = 50
        
        move = abs(nxt.close - c.close) / c.close * 100
        strength += min(move * 20, 30)
        
        start = max(0, idx-10)
        avg_vol = sum(x.volume for x in candles[start:idx]) / (idx-start) if idx > 0 else c.volume
        vol_ratio = c.volume / avg_vol if avg_vol > 0 else 1.0
        strength += min(vol_ratio * 10, 20)
        
        return min(strength, 100)