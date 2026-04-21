"""Détection des Swing Points."""
from typing import List
import numpy as np
from app.data.market_providers import CandleData
from app.models.swing_point import SwingPoint


class SwingPoints:
    @staticmethod
    def detect(candles: List[CandleData], left: int = 3, right: int = 3) -> List[SwingPoint]:
        if len(candles) < left + right + 1:
            return []
        highs = np.array([c.high for c in candles])
        lows = np.array([c.low for c in candles])
        swings = []
        for i in range(left, len(candles) - right):
            if all(highs[i] > highs[i-j] for j in range(1, left+1)) and \
               all(highs[i] > highs[i+j] for j in range(1, right+1)):
                swings.append(SwingPoint(
                    index=i, price=highs[i], timestamp=candles[i].timestamp,
                    point_type="HIGH", strength=left+right, is_fractal=True,
                    volume=candles[i].volume,
                ))
            if all(lows[i] < lows[i-j] for j in range(1, left+1)) and \
               all(lows[i] < lows[i+j] for j in range(1, right+1)):
                swings.append(SwingPoint(
                    index=i, price=lows[i], timestamp=candles[i].timestamp,
                    point_type="LOW", strength=left+right, is_fractal=True,
                    volume=candles[i].volume,
                ))
        return swings