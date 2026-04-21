"""Pools de liquidité SMC."""
from typing import List, Dict, Any, Optional
from app.data.market_providers import CandleData


class LiquidityPoolsSMC:
    """Détection des pools de liquidité."""
    
    @staticmethod
    def find_pools(candles: List[CandleData]) -> Dict[str, Any]:
        if len(candles) < 20:
            return {"pools": [], "buy_stops": None, "sell_stops": None}
        
        highs = [c.high for c in candles[-20:]]
        lows = [c.low for c in candles[-20:]]
        
        equal_highs = LiquidityPoolsSMC._find_equal_levels(highs, "HIGH")
        equal_lows = LiquidityPoolsSMC._find_equal_levels(lows, "LOW")
        
        pools = equal_highs + equal_lows
        
        recent_high = max(highs)
        recent_low = min(lows)
        
        pools.append({"price": recent_high * 1.002, "type": "BUY_STOPS", "strength": 0.7})
        pools.append({"price": recent_low * 0.998, "type": "SELL_STOPS", "strength": 0.7})
        
        return {"pools": pools, "buy_stops": recent_high * 1.002, "sell_stops": recent_low * 0.998,
                "equal_highs": equal_highs, "equal_lows": equal_lows}
    
    @staticmethod
    def _find_equal_levels(prices: List[float], level_type: str, tolerance: float = 0.002) -> List[Dict]:
        groups = []
        used = set()
        sorted_prices = sorted(prices)
        
        for i, p in enumerate(sorted_prices):
            if i in used:
                continue
            group = [p]
            for j, other in enumerate(sorted_prices[i+1:], i+1):
                if abs(p - other) / p <= tolerance:
                    group.append(other)
                    used.add(j)
            if len(group) >= 2:
                groups.append({
                    "price": sum(group) / len(group), "count": len(group),
                    "type": f"EQUAL_{level_type}S", "strength": min(len(group) / 3, 1.0),
                })
        return groups
    
    @staticmethod
    def find_nearest(pools: List[Dict], price: float, direction: str) -> Optional[Dict]:
        if direction == "ABOVE":
            above = [p for p in pools if p["price"] > price]
            return min(above, key=lambda x: x["price"]) if above else None
        below = [p for p in pools if p["price"] < price]
        return max(below, key=lambda x: x["price"]) if below else None