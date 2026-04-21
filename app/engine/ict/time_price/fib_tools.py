"""Fibonacci tools."""
from typing import Dict, List, Tuple


class FibonacciTools:
    RETRACEMENT_LEVELS = [0, 0.236, 0.382, 0.5, 0.618, 0.705, 0.786, 0.886, 1.0]
    EXTENSION_LEVELS = [-0.272, -0.618, -1.0, -1.272, -1.618, -2.0, -2.618]
    
    @classmethod
    def retracements(cls, high: float, low: float) -> Dict[float, float]:
        rng = high - low
        return {lvl: low + rng * lvl if high > low else high - rng * lvl for lvl in cls.RETRACEMENT_LEVELS}
    
    @classmethod
    def extensions(cls, high: float, low: float, direction: str = "UP") -> Dict[float, float]:
        rng = abs(high - low)
        if direction == "UP":
            return {abs(lvl): high + rng * abs(lvl) for lvl in cls.EXTENSION_LEVELS}
        return {abs(lvl): low - rng * abs(lvl) for lvl in cls.EXTENSION_LEVELS}
    
    @classmethod
    def find_nearest_level(cls, price: float, levels: Dict[float, float]) -> Tuple[float, float]:
        nearest = None
        min_dist = float('inf')
        for lvl, lvl_price in levels.items():
            dist = abs(price - lvl_price)
            if dist < min_dist:
                min_dist = dist
                nearest = lvl
        return nearest, levels[nearest] if nearest else None
    
    @classmethod
    def get_ote_targets(cls, high: float, low: float) -> Dict[str, float]:
        rng = abs(high - low)
        if high > low:
            return {
                "entry_618": low + rng * 0.618, "entry_705": low + rng * 0.705,
                "entry_790": low + rng * 0.790, "stop": low - rng * 0.1,
                "target_1": high + rng * 0.272, "target_2": high + rng * 0.618,
            }
        return {
            "entry_618": high - rng * 0.618, "entry_705": high - rng * 0.705,
            "entry_790": high - rng * 0.790, "stop": high + rng * 0.1,
            "target_1": low - rng * 0.272, "target_2": low - rng * 0.618,
        }