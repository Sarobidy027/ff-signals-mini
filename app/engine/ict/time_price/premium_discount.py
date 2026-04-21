"""Premium/Discount zones."""
from typing import Tuple, Dict
import numpy as np
from app.data.market_providers import CandleData


class PremiumDiscount:
    @staticmethod
    def calculate_ote_zone(high: float, low: float) -> Dict[str, float]:
        rng = high - low
        return {
            "high": high, "low": low,
            "fib_618": low + rng * 0.618,
            "fib_705": low + rng * 0.705,
            "fib_790": low + rng * 0.790,
            "ote_top": low + rng * 0.79,
            "ote_bottom": low + rng * 0.618,
        }
    
    @staticmethod
    def is_in_premium(price: float, high: float, low: float) -> bool:
        rng = high - low
        return price > low + rng * 0.5
    
    @staticmethod
    def is_in_discount(price: float, high: float, low: float) -> bool:
        rng = high - low
        return price < low + rng * 0.5
    
    @staticmethod
    def is_in_ote(price: float, high: float, low: float, direction: str) -> bool:
        ote = PremiumDiscount.calculate_ote_zone(high, low)
        return ote["ote_bottom"] <= price <= ote["ote_top"]
    
    @staticmethod
    def find_swing_range(candles: List[CandleData], lookback: int = 50) -> Tuple[float, float]:
        recent = candles[-lookback:] if len(candles) >= lookback else candles
        return max(c.high for c in recent), min(c.low for c in recent)