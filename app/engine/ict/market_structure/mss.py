"""Détection Market Structure Shift."""
from typing import List, Optional, Dict, Any
from app.data.market_providers import CandleData
from app.models.swing_point import SwingPoint


class MSS:
    @staticmethod
    def detect(candles: List[CandleData], swings: List[SwingPoint]) -> Optional[Dict]:
        if len(candles) < 10 or len(swings) < 3:
            return None
        recent_candles = candles[-10:]
        recent_swings = sorted(swings, key=lambda s: s.timestamp)[-3:]
        
        for swing in recent_swings:
            if swing.point_type == "HIGH":
                for i, c in enumerate(recent_candles):
                    if c.high > swing.price:
                        for j in range(i+1, min(i+4, len(recent_candles))):
                            if recent_candles[j].close < swing.price:
                                return {
                                    "type": "MSS", "direction": "BULLISH_TRAP",
                                    "swing": swing, "timestamp": recent_candles[j].timestamp,
                                    "price": swing.price, "confidence": 70,
                                    "signal": "Potential bullish reversal after stop hunt",
                                }
            else:
                for i, c in enumerate(recent_candles):
                    if c.low < swing.price:
                        for j in range(i+1, min(i+4, len(recent_candles))):
                            if recent_candles[j].close > swing.price:
                                return {
                                    "type": "MSS", "direction": "BEARISH_TRAP",
                                    "swing": swing, "timestamp": recent_candles[j].timestamp,
                                    "price": swing.price, "confidence": 70,
                                    "signal": "Potential bearish reversal after stop hunt",
                                }
        return None