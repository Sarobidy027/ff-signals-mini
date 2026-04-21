"""Breaker Blocks."""
from typing import List
import uuid
from app.data.market_providers import CandleData
from app.models.order_block import OrderBlock


class BreakerBlock:
    @staticmethod
    def detect(candles: List[CandleData], base_obs: List[OrderBlock], instrument: str, timeframe: str) -> List[OrderBlock]:
        breakers = []
        for ob in base_obs:
            ob_idx = BreakerBlock._find_ob_index(candles, ob)
            if ob_idx is None or ob_idx >= len(candles) - 5:
                continue
            
            for i in range(ob_idx + 1, len(candles)):
                if ob.direction == "BULLISH":
                    if candles[i].close < ob.low_price:
                        if BreakerBlock._check_retest(candles, i, ob, "BEARISH"):
                            breakers.append(OrderBlock(
                                id=str(uuid.uuid4()), instrument=instrument, direction="BEARISH", ob_type="BREAKER",
                                high_price=ob.high_price, low_price=ob.low_price, open_price=ob.open_price,
                                close_price=ob.close_price, volume=ob.volume, timestamp=candles[i].timestamp,
                                timeframe=timeframe, strength=ob.strength * 0.8, is_active=True,
                            ))
                            break
                else:
                    if candles[i].close > ob.high_price:
                        if BreakerBlock._check_retest(candles, i, ob, "BULLISH"):
                            breakers.append(OrderBlock(
                                id=str(uuid.uuid4()), instrument=instrument, direction="BULLISH", ob_type="BREAKER",
                                high_price=ob.high_price, low_price=ob.low_price, open_price=ob.open_price,
                                close_price=ob.close_price, volume=ob.volume, timestamp=candles[i].timestamp,
                                timeframe=timeframe, strength=ob.strength * 0.8, is_active=True,
                            ))
                            break
        return breakers
    
    @staticmethod
    def _find_ob_index(candles: List[CandleData], ob: OrderBlock) -> int:
        for i, c in enumerate(candles):
            if c.timestamp == ob.timestamp and abs(c.open - ob.open_price) < 0.00001:
                return i
        return -1
    
    @staticmethod
    def _check_retest(candles: List[CandleData], start: int, ob: OrderBlock, direction: str) -> bool:
        for i in range(start, min(start + 10, len(candles))):
            if direction == "BULLISH":
                if ob.low_price <= candles[i].low <= ob.high_price:
                    return True
            else:
                if ob.low_price <= candles[i].high <= ob.high_price:
                    return True
        return False