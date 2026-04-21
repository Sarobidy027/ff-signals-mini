"""Multi-Timeframe Alignment."""
from typing import Dict, Any
from app.data.market_providers import MarketProviderFactory
from app.utils.numpy_utils import calculate_sma, calculate_ema


class MultiTFAlignment:
    @classmethod
    async def get_bias(cls, instrument: str) -> Dict[str, Any]:
        try:
            daily = await MarketProviderFactory.get_candles(instrument, "1D", 50)
            h4 = await MarketProviderFactory.get_candles(instrument, "4H", 50)
            
            daily_bias = cls._calculate_bias(daily) if daily else "NEUTRAL"
            h4_bias = cls._calculate_bias(h4) if h4 else "NEUTRAL"
            
            if daily_bias == h4_bias and daily_bias != "NEUTRAL":
                return {"direction": daily_bias, "strength": 0.9, "aligned": True,
                       "daily_bias": daily_bias, "h4_bias": h4_bias}
            elif daily_bias != "NEUTRAL":
                return {"direction": daily_bias, "strength": 0.7, "aligned": False,
                       "daily_bias": daily_bias, "h4_bias": h4_bias}
            elif h4_bias != "NEUTRAL":
                return {"direction": h4_bias, "strength": 0.5, "aligned": False,
                       "daily_bias": daily_bias, "h4_bias": h4_bias}
            return {"direction": "NEUTRAL", "strength": 0.3, "aligned": False,
                   "daily_bias": daily_bias, "h4_bias": h4_bias}
        except Exception:
            return {"direction": "NEUTRAL", "strength": 0.3, "aligned": False}
    
    @classmethod
    def _calculate_bias(cls, candles) -> str:
        if len(candles) < 20:
            return "NEUTRAL"
        closes = [c.close for c in candles]
        current = closes[-1]
        sma_10 = sum(closes[-10:]) / 10
        sma_20 = sum(closes[-20:]) / 20
        
        if current > sma_10 > sma_20:
            return "BULLISH"
        elif current < sma_10 < sma_20:
            return "BEARISH"
        return "NEUTRAL"