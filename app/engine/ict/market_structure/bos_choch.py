"""Détection BOS et CHoCH."""
from typing import List, Optional, Dict, Any
from app.data.market_providers import CandleData
from app.models.swing_point import SwingPoint


class BOSChoCH:
    @staticmethod
    def detect_bos(candles: List[CandleData], swings: List[SwingPoint], direction: str) -> List[Dict]:
        bos = []
        points = [s for s in swings if s.point_type == ("HIGH" if direction == "BULLISH" else "LOW")]
        points.sort(key=lambda s: s.timestamp)
        for i in range(1, len(points)):
            if (direction == "BULLISH" and points[i].price > points[i-1].price) or \
               (direction == "BEARISH" and points[i].price < points[i-1].price):
                bos.append({
                    "type": "BOS", "direction": direction,
                    "broken": points[i-1], "break": points[i],
                    "timestamp": points[i].timestamp, "price": points[i].price,
                })
        return bos
    
    @staticmethod
    def detect_choch(candles: List[CandleData], swings: List[SwingPoint]) -> Optional[Dict]:
        if len(swings) < 3:
            return None
        recent = sorted(swings, key=lambda s: s.timestamp)[-5:]
        highs = [s for s in recent if s.point_type == "HIGH"]
        lows = [s for s in recent if s.point_type == "LOW"]
        
        if len(lows) >= 2 and lows[-1].price > lows[-2].price:
            if highs and candles[-1].close > max(h.price for h in highs[-3:]):
                return {"type": "CHoCH", "direction": "BULLISH", 
                       "timestamp": lows[-1].timestamp, "price": lows[-1].price}
        
        if len(highs) >= 2 and highs[-1].price < highs[-2].price:
            if lows and candles[-1].close < min(l.price for l in lows[-3:]):
                return {"type": "CHoCH", "direction": "BEARISH",
                       "timestamp": highs[-1].timestamp, "price": highs[-1].price}
        return None