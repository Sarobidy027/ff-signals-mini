"""Point of Control (POC) - Niveau avec le plus de volume."""
from typing import List, Dict, Any
import numpy as np
from app.data.market_providers import CandleData


class POCAnalyzer:
    """Analyseur de Point of Control."""
    
    @staticmethod
    def find_poc(candles: List[CandleData], levels: int = 10) -> Dict[str, Any]:
        if len(candles) < 20:
            return {"poc": None, "value_area": None}
        
        recent = candles[-20:]
        all_prices = []
        for c in recent:
            all_prices.extend([c.high, c.low, c.close])
        
        min_p = min(all_prices)
        max_p = max(all_prices)
        step = (max_p - min_p) / levels
        
        volume_profile = {}
        for c in recent:
            level = min_p + int((c.close - min_p) / step) * step
            volume_profile[level] = volume_profile.get(level, 0) + c.volume
        
        if not volume_profile:
            return {"poc": None, "value_area": None}
        
        poc = max(volume_profile, key=volume_profile.get)
        
        total_vol = sum(volume_profile.values())
        sorted_levels = sorted(volume_profile.items(), key=lambda x: x[1], reverse=True)
        cum_vol = 0
        value_area = []
        for level, vol in sorted_levels:
            cum_vol += vol
            value_area.append(level)
            if cum_vol >= total_vol * 0.7:
                break
        
        return {"poc": poc, "poc_volume": volume_profile[poc],
                "value_area": [min(value_area), max(value_area)],
                "value_area_percent": 70}