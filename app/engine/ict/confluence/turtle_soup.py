"""Turtle Soup pattern."""
from typing import List, Optional, Dict, Any
from app.data.market_providers import CandleData
from app.models.swing_point import SwingPoint


class TurtleSoup:
    @staticmethod
    def detect(candles: List[CandleData], swings: List[SwingPoint]) -> Optional[Dict[str, Any]]:
        if len(candles) < 10 or len(swings) < 3:
            return None
        
        recent_candles = candles[-10:]
        recent_swings = sorted(swings, key=lambda s: s.timestamp)[-3:]
        
        lows = [s for s in recent_swings if s.point_type == "LOW"]
        if lows:
            recent_low = lows[-1]
            for i, c in enumerate(recent_candles):
                if c.low < recent_low.price:
                    for j in range(i+1, min(i+4, len(recent_candles))):
                        if recent_candles[j].close > recent_low.price:
                            return {
                                "pattern": "BULLISH_TURTLE_SOUP", "broken_level": recent_low.price,
                                "entry": recent_candles[j].close, "stop": c.low,
                                "target": recent_low.price + (recent_low.price - c.low) * 2,
                                "confidence": 0.7,
                            }
        
        highs = [s for s in recent_swings if s.point_type == "HIGH"]
        if highs:
            recent_high = highs[-1]
            for i, c in enumerate(recent_candles):
                if c.high > recent_high.price:
                    for j in range(i+1, min(i+4, len(recent_candles))):
                        if recent_candles[j].close < recent_high.price:
                            return {
                                "pattern": "BEARISH_TURTLE_SOUP", "broken_level": recent_high.price,
                                "entry": recent_candles[j].close, "stop": c.high,
                                "target": recent_high.price - (c.high - recent_high.price) * 2,
                                "confidence": 0.7,
                            }
        return None