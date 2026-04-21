"""Mitigation Blocks."""
from typing import List
import uuid
from app.data.market_providers import CandleData
from app.models.order_block import OrderBlock


class MitigationBlock:
    @staticmethod
    def detect(candles: List[CandleData], base_obs: List[OrderBlock], instrument: str, timeframe: str) -> List[OrderBlock]:
        mitigations = []
        for ob in base_obs:
            test_count = MitigationBlock._count_tests(candles, ob)
            if test_count >= 1:
                mitigations.append(OrderBlock(
                    id=str(uuid.uuid4()), instrument=instrument, direction=ob.direction, ob_type="MITIGATION",
                    high_price=ob.high_price, low_price=ob.low_price, open_price=ob.open_price,
                    close_price=ob.close_price, volume=ob.volume, timestamp=ob.timestamp,
                    timeframe=timeframe, strength=ob.strength * (1 - test_count * 0.2),
                    tested_count=test_count, is_active=test_count < 3, mitigated=test_count >= 3,
                ))
        return mitigations
    
    @staticmethod
    def _count_tests(candles: List[CandleData], ob: OrderBlock) -> int:
        test_count = 0
        ob_found = False
        for c in candles:
            if not ob_found and c.timestamp <= ob.timestamp:
                continue
            ob_found = True
            if ob.low_price <= c.high <= ob.high_price or ob.low_price <= c.low <= ob.high_price:
                test_count += 1
        return test_count