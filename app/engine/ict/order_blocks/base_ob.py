"""Order Blocks de base."""
from typing import List, Optional
import numpy as np
import uuid
from app.data.market_providers import CandleData
from app.models.order_block import OrderBlock


class BaseOrderBlock:
    @staticmethod
    def detect(candles: List[CandleData], instrument: str, timeframe: str) -> List[OrderBlock]:
        obs = []
        for i in range(2, len(candles) - 1):
            if candles[i].is_bearish and candles[i+1].is_bullish and candles[i+1].close > candles[i].high:
                strength = BaseOrderBlock._calc_strength(candles, i)
                obs.append(OrderBlock(
                    id=str(uuid.uuid4()), instrument=instrument, direction="BULLISH", ob_type="BASE",
                    high_price=candles[i].high, low_price=candles[i].low, open_price=candles[i].open,
                    close_price=candles[i].close, volume=candles[i].volume, timestamp=candles[i].timestamp,
                    timeframe=timeframe, strength=strength, is_active=True,
                ))
            if candles[i].is_bullish and candles[i+1].is_bearish and candles[i+1].close < candles[i].low:
                strength = BaseOrderBlock._calc_strength(candles, i)
                obs.append(OrderBlock(
                    id=str(uuid.uuid4()), instrument=instrument, direction="BEARISH", ob_type="BASE",
                    high_price=candles[i].high, low_price=candles[i].low, open_price=candles[i].open,
                    close_price=candles[i].close, volume=candles[i].volume, timestamp=candles[i].timestamp,
                    timeframe=timeframe, strength=strength, is_active=True,
                ))
        return obs
    
    @staticmethod
    def _calc_strength(candles: List[CandleData], idx: int) -> float:
        c = candles[idx]
        nxt = candles[idx+1]
        avg_vol = np.mean([x.volume for x in candles[max(0, idx-10):idx]]) if idx > 0 else c.volume
        vol_factor = min(c.volume / avg_vol, 2.0) if avg_vol > 0 else 1.0
        impulse = abs(nxt.close - c.close) / c.range if c.range > 0 else 0
        impulse_factor = min(impulse * 10, 1.0)
        body_factor = c.body_size / c.range if c.range > 0 else 0
        return min(vol_factor * 0.4 + impulse_factor * 0.4 + body_factor * 0.2, 1.0)
    
    @staticmethod
    def find_nearest_ob(obs: List[OrderBlock], price: float, direction: str) -> Optional[OrderBlock]:
        relevant = [ob for ob in obs if ob.direction == direction and ob.is_active and not ob.mitigated]
        if not relevant:
            return None
        if direction == "BULLISH":
            below = [ob for ob in relevant if ob.low_price < price]
            return max(below, key=lambda ob: ob.low_price) if below else None
        else:
            above = [ob for ob in relevant if ob.high_price > price]
            return min(above, key=lambda ob: ob.high_price) if above else None