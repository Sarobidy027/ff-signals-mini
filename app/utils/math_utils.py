"""
Utilitaires mathématiques.
"""
import math
from typing import List


def round_to_pip(price: float, instrument: str) -> float:
    if "JPY" in instrument:
        return round(price, 3)
    elif any(c in instrument for c in ["BTC", "ETH", "XRP", "LTC"]):
        if "BTC" in instrument:
            return round(price, 2)
        return round(price, 2)
    return round(price, 5)


def calculate_moving_average(prices: List[float], period: int) -> List[float]:
    if len(prices) < period:
        return []
    return [sum(prices[i:i+period]) / period for i in range(len(prices) - period + 1)]


def calculate_standard_deviation(values: List[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return math.sqrt(variance)


def normalize(value: float, min_val: float, max_val: float) -> float:
    if max_val == min_val:
        return 0.5
    return (value - min_val) / (max_val - min_val)