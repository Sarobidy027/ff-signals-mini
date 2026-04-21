"""Volume Imbalance detector."""
from typing import List, Dict, Any
import numpy as np
from app.data.market_providers import CandleData


class VolumeImbalanceDetector:
    @staticmethod
    def detect(candles: List[CandleData]) -> List[Dict[str, Any]]:
        imbalances = []
        if len(candles) < 20:
            return imbalances
        
        baseline = np.mean([c.volume for c in candles[-20:]])
        
        for i in range(20, len(candles)):
            c = candles[i]
            if c.volume > baseline * 2:
                pressure = "BUYING" if c.close > c.open else "SELLING"
                strength = (c.close - c.low) / c.range if c.range > 0 and c.close > c.open else \
                          (c.high - c.close) / c.range if c.range > 0 else 0.5
                
                imbalances.append({
                    "timestamp": c.timestamp, "volume": c.volume, "baseline": baseline,
                    "ratio": c.volume / baseline, "pressure": pressure, "strength": strength,
                    "price": c.close,
                })
        return imbalances