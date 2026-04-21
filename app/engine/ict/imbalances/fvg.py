"""Fair Value Gap detector."""
from typing import List
import uuid
import numpy as np
from app.data.market_providers import CandleData
from app.models.fvg import FairValueGap


class FVGDetector:
    @staticmethod
    def find(candles: List[CandleData], instrument: str, timeframe: str) -> List[FairValueGap]:
        fvgs = []
        for i in range(len(candles) - 2):
            c1, c2, c3 = candles[i], candles[i+1], candles[i+2]
            
            if c1.high < c3.low:
                imbalance = (c1.volume + c2.volume + c3.volume) / 3
                max_vol = max(c1.volume, c2.volume, c3.volume)
                vol_imbalance = max_vol / imbalance if imbalance > 0 else 1.0
                quality = min(50 + abs(c3.low - c1.high) * 10000, 100)
                
                fvgs.append(FairValueGap(
                    id=str(uuid.uuid4()), instrument=instrument, direction="BULLISH",
                    gap_top=c3.low, gap_bottom=c1.high,
                    start_timestamp=c1.timestamp, end_timestamp=c3.timestamp,
                    timeframe=timeframe, volume_imbalance=vol_imbalance, quality_score=quality,
                ))
            
            if c1.low > c3.high:
                imbalance = (c1.volume + c2.volume + c3.volume) / 3
                max_vol = max(c1.volume, c2.volume, c3.volume)
                vol_imbalance = max_vol / imbalance if imbalance > 0 else 1.0
                quality = min(50 + abs(c1.low - c3.high) * 10000, 100)
                
                fvgs.append(FairValueGap(
                    id=str(uuid.uuid4()), instrument=instrument, direction="BEARISH",
                    gap_top=c1.low, gap_bottom=c3.high,
                    start_timestamp=c1.timestamp, end_timestamp=c3.timestamp,
                    timeframe=timeframe, volume_imbalance=vol_imbalance, quality_score=quality,
                ))
        return fvgs
    
    @staticmethod
    def check_if_filled(fvg: FairValueGap, candles: List[CandleData]) -> bool:
        for c in candles:
            if c.timestamp <= fvg.end_timestamp:
                continue
            if fvg.direction == "BULLISH" and c.low <= fvg.gap_top:
                return True
            if fvg.direction == "BEARISH" and c.high >= fvg.gap_bottom:
                return True
        return False
    
    @staticmethod
    def find_unfilled_fvgs(fvgs: List[FairValueGap], candles: List[CandleData]) -> List[FairValueGap]:
        return [f for f in fvgs if not FVGDetector.check_if_filled(f, candles)]
    
    @staticmethod
    def find_nearest_fvg(fvgs: List[FairValueGap], price: float, direction: str) -> FairValueGap:
        relevant = [f for f in fvgs if f.direction == direction and not f.is_filled]
        if not relevant:
            return None
        if direction == "BULLISH":
            below = [f for f in relevant if f.gap_top < price]
            return max(below, key=lambda f: f.gap_top) if below else None
        else:
            above = [f for f in relevant if f.gap_bottom > price]
            return min(above, key=lambda f: f.gap_bottom) if above else None