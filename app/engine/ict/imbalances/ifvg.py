"""Implied FVG detector."""
from typing import List
import uuid
from app.data.market_providers import CandleData
from app.models.fvg import FairValueGap


class ImpliedFVGDetector:
    @staticmethod
    def detect(candles: List[CandleData], instrument: str, timeframe: str) -> List[FairValueGap]:
        ifvgs = []
        if len(candles) < 10:
            return ifvgs
        
        for i in range(5, len(candles) - 1):
            recent_high = max(c.high for c in candles[i-5:i])
            recent_low = min(c.low for c in candles[i-5:i])
            range_size = recent_high - recent_low
            
            if candles[i].close > recent_high and candles[i].range > range_size * 1.5:
                implied_top = candles[i].high + (candles[i].range * 0.5)
                ifvgs.append(FairValueGap(
                    id=str(uuid.uuid4()), instrument=instrument, direction="BULLISH",
                    gap_top=implied_top, gap_bottom=candles[i].high,
                    start_timestamp=candles[i].timestamp, end_timestamp=candles[i].timestamp,
                    timeframe=timeframe, volume_imbalance=2.0, quality_score=70,
                ))
            
            if candles[i].close < recent_low and candles[i].range > range_size * 1.5:
                implied_bottom = candles[i].low - (candles[i].range * 0.5)
                ifvgs.append(FairValueGap(
                    id=str(uuid.uuid4()), instrument=instrument, direction="BEARISH",
                    gap_top=candles[i].low, gap_bottom=implied_bottom,
                    start_timestamp=candles[i].timestamp, end_timestamp=candles[i].timestamp,
                    timeframe=timeframe, volume_imbalance=2.0, quality_score=70,
                ))
        return ifvgs