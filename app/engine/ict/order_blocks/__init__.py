"""Order Blocks module."""
from app.engine.ict.order_blocks.base_ob import BaseOrderBlock
from app.engine.ict.order_blocks.breaker import BreakerBlock
from app.engine.ict.order_blocks.mitigation import MitigationBlock
from app.engine.ict.order_blocks.rejection import RejectionBlock
from app.engine.ict.order_blocks.vacuum import VacuumBlock


class OrderBlockDetector:
    @staticmethod
    def find_all(candles, instrument: str, timeframe: str):
        base = BaseOrderBlock.detect(candles, instrument, timeframe)
        breaker = BreakerBlock.detect(candles, base, instrument, timeframe)
        mitigation = MitigationBlock.detect(candles, base, instrument, timeframe)
        rejection = RejectionBlock.detect(candles, instrument, timeframe)
        vacuum = VacuumBlock.detect(candles, instrument, timeframe)
        return base + breaker + mitigation + rejection + vacuum


__all__ = ["BaseOrderBlock", "BreakerBlock", "MitigationBlock", "RejectionBlock", "VacuumBlock", "OrderBlockDetector"]