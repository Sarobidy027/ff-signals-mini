"""Liquidity Pools detector."""
from typing import List, Dict, Any, Optional
import numpy as np
from app.data.market_providers import CandleData
from app.models.swing_point import SwingPoint


class LiquidityPools:
    @staticmethod
    def find(candles: List[CandleData], swings: List[SwingPoint]) -> Dict[str, Any]:
        highs = [s.price for s in swings if s.point_type == "HIGH"]
        lows = [s.price for s in swings if s.point_type == "LOW"]
        
        equal_highs = LiquidityPools._find_equal_levels([s for s in swings if s.point_type == "HIGH"])
        equal_lows = LiquidityPools._find_equal_levels([s for s in swings if s.point_type == "LOW"])
        
        pools = equal_highs + equal_lows
        
        recent_high = max(highs) if highs else max(c.high for c in candles[-20:])
        recent_low = min(lows) if lows else min(c.low for c in candles[-20:])
        
        pools.append({"price": recent_high * 1.002, "type": "BUY_STOPS", "strength": 0.7, "count": 1})
        pools.append({"price": recent_low * 0.998, "type": "SELL_STOPS", "strength": 0.7, "count": 1})
        
        return {
            "equal_highs": equal_highs, "equal_lows": equal_lows,
            "buy_stops": recent_high * 1.002, "sell_stops": recent_low * 0.998,
            "pools": pools,
        }
    
    @staticmethod
    def _find_equal_levels(points: List[SwingPoint], tolerance: float = 0.0002) -> List[Dict]:
        groups = []
        used = set()
        for i, p in enumerate(points):
            if i in used:
                continue
            group = [p]
            for j, other in enumerate(points[i+1:], i+1):
                if abs(p.price - other.price) / p.price <= tolerance:
                    group.append(other)
                    used.add(j)
            if len(group) >= 2:
                avg = sum(pt.price for pt in group) / len(group)
                groups.append({
                    "price": avg, "count": len(group),
                    "type": "EQUAL_HIGHS" if p.point_type == "HIGH" else "EQUAL_LOWS",
                    "strength": min(len(group) / 3, 1.0),
                })
        return groups
    
    @staticmethod
    def find_nearest_liquidity(pools: List[Dict], price: float, direction: str) -> Optional[Dict]:
        if direction == "ABOVE":
            above = [p for p in pools if p["price"] > price]
            return min(above, key=lambda p: p["price"]) if above else None
        else:
            below = [p for p in pools if p["price"] < price]
            return max(below, key=lambda p: p["price"]) if below else None