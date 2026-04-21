"""Analyse Footprint (empreinte de volume)."""
from typing import List, Dict, Any
from app.data.market_providers import CandleData


class FootprintAnalyzer:
    """Analyseur Footprint."""
    
    @staticmethod
    def analyze(candles: List[CandleData]) -> Dict[str, Any]:
        if len(candles) < 5:
            return {"imbalance": False}
        
        recent = candles[-5:]
        imbalances = []
        
        for c in recent:
            if c.close > c.open:
                upper = c.high - c.close
                lower = c.open - c.low
                if upper > lower * 2:
                    imbalances.append({"type": "SELLING_ABSORPTION", "candle": c.timestamp})
                elif lower > upper * 2:
                    imbalances.append({"type": "BUYING_PRESSURE", "candle": c.timestamp})
            else:
                upper = c.high - c.open
                lower = c.close - c.low
                if upper > lower * 2:
                    imbalances.append({"type": "SELLING_PRESSURE", "candle": c.timestamp})
                elif lower > upper * 2:
                    imbalances.append({"type": "BUYING_ABSORPTION", "candle": c.timestamp})
        
        return {"imbalance": len(imbalances) > 0, "patterns": imbalances,
                "confidence": min(50 + len(imbalances) * 15, 90)}