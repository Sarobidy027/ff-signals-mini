"""Smart Money Reversal."""
from typing import List, Optional, Dict, Any
from app.data.market_providers import CandleData
from app.models.swing_point import SwingPoint


class SmartMoneyReversal:
    @staticmethod
    def detect(candles: List[CandleData], swings: List[SwingPoint]) -> Optional[Dict[str, Any]]:
        if len(swings) < 4:
            return None
        
        recent = sorted(swings, key=lambda s: s.timestamp)[-4:]
        highs = [s for s in recent if s.point_type == "HIGH"]
        lows = [s for s in recent if s.point_type == "LOW"]
        
        if len(highs) >= 2 and len(lows) >= 2:
            if highs[-1].price > highs[-2].price:
                if lows[-1].price < lows[-2].price:
                    recent_low = min(c.low for c in candles[-5:])
                    if recent_low > lows[-1].price:
                        return {
                            "pattern": "BULLISH_SMR", "confidence": 0.75,
                            "entry": recent_low, "stop": lows[-1].price, "target": highs[-1].price,
                        }
            
            if lows[-1].price < lows[-2].price:
                if highs[-1].price > highs[-2].price:
                    recent_high = max(c.high for c in candles[-5:])
                    if recent_high < highs[-1].price:
                        return {
                            "pattern": "BEARISH_SMR", "confidence": 0.75,
                            "entry": recent_high, "stop": highs[-1].price, "target": lows[-1].price,
                        }
        return None