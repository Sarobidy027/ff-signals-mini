"""Rejection Blocks."""
from typing import List
import uuid
from app.data.market_providers import CandleData
from app.models.order_block import OrderBlock


class RejectionBlock:
    @staticmethod
    def detect(candles: List[CandleData], instrument: str, timeframe: str) -> List[OrderBlock]:
        obs = []
        for c in candles:
            if c.lower_wick > c.body_size * 2 and c.upper_wick < c.body_size:
                strength = min(c.lower_wick / c.range * 0.7 + 0.3, 1.0) if c.range > 0 else 0.7
                obs.append(OrderBlock(
                    id=str(uuid.uuid4()), instrument=instrument, direction="BULLISH", ob_type="REJECTION",
                    high_price=c.high, low_price=c.low, open_price=c.open, close_price=c.close,
                    volume=c.volume, timestamp=c.timestamp, timeframe=timeframe, strength=strength, is_active=True,
                ))
            if c.upper_wick > c.body_size * 2 and c.lower_wick < c.body_size:
                strength = min(c.upper_wick / c.range * 0.7 + 0.3, 1.0) if c.range > 0 else 0.7
                obs.append(OrderBlock(
                    id=str(uuid.uuid4()), instrument=instrument, direction="BEARISH", ob_type="REJECTION",
                    high_price=c.high, low_price=c.low, open_price=c.open, close_price=c.close,
                    volume=c.volume, timestamp=c.timestamp, timeframe=timeframe, strength=strength, is_active=True,
                ))
        return obs