"""Schémas Wyckoff - Points clés (PS, SC, AR, ST, SOS, SOW, LPS, LPSY)."""
from typing import List, Dict, Any, Optional, Tuple
from app.data.market_providers import CandleData


class WyckoffSchematics:
    """Identification des points clés du schéma Wyckoff."""
    
    @staticmethod
    def identify_points(candles: List[CandleData]) -> Dict[str, Any]:
        points = {"PS": None, "SC": None, "AR": None, "ST": None,
                 "SOS": None, "SOW": None, "LPS": None, "LPSY": None}
        
        if len(candles) < 50:
            return points
        
        swings = WyckoffSchematics._find_swings(candles)
        
        if swings["highs"] and swings["lows"]:
            points["PS"] = swings["lows"][0] if len(swings["lows"]) > 0 else None
            points["SC"] = min(swings["lows"], key=lambda x: x["price"]) if swings["lows"] else None
            points["AR"] = swings["highs"][0] if len(swings["highs"]) > 0 else None
        
        return points
    
    @staticmethod
    def _find_swings(candles: List[CandleData]) -> Dict[str, List]:
        highs = []
        lows = []
        
        for i in range(3, len(candles) - 3):
            c = candles[i]
            if all(c.high > candles[i-j].high for j in range(1, 4)) and \
               all(c.high > candles[i+j].high for j in range(1, 4)):
                highs.append({"price": c.high, "index": i, "timestamp": c.timestamp})
            if all(c.low < candles[i-j].low for j in range(1, 4)) and \
               all(c.low < candles[i+j].low for j in range(1, 4)):
                lows.append({"price": c.low, "index": i, "timestamp": c.timestamp})
        
        return {"highs": highs, "lows": lows}
    
    @staticmethod
    def is_spring(candles: List[CandleData], support: float) -> Tuple[bool, float]:
        """Détecte un Spring (faux breakdown)."""
        for i in range(len(candles) - 3):
            if candles[i].low < support:
                for j in range(i+1, min(i+4, len(candles))):
                    if candles[j].close > support:
                        confidence = 70 + (10 if candles[i].volume > sum(c.volume for c in candles[-20:])/20 else 0)
                        return True, min(confidence, 90)
        return False, 0
    
    @staticmethod
    def is_upthrust(candles: List[CandleData], resistance: float) -> Tuple[bool, float]:
        """Détecte un Upthrust (faux breakout)."""
        for i in range(len(candles) - 3):
            if candles[i].high > resistance:
                for j in range(i+1, min(i+4, len(candles))):
                    if candles[j].close < resistance:
                        confidence = 70 + (10 if candles[i].volume > sum(c.volume for c in candles[-20:])/20 else 0)
                        return True, min(confidence, 90)
        return False, 0