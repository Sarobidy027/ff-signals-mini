"""Modèles de Market Maker (MMM Buy/Sell)."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.data.market_providers import CandleData
from app.engine.smc.models import MarketMakerModel, MarketMakerModelType


class MarketMakerModels:
    """Détection des modèles MMM."""
    
    @staticmethod
    def detect(candles: List[CandleData]) -> Optional[MarketMakerModel]:
        if len(candles) < 30:
            return None
        
        range_info = MarketMakerModels._detect_range(candles)
        if not range_info:
            return None
        
        manipulation = MarketMakerModels._detect_manipulation(candles, range_info)
        if not manipulation:
            return None
        
        return MarketMakerModels._build_model(range_info, manipulation)
    
    @staticmethod
    def _detect_range(candles: List[CandleData]) -> Optional[dict]:
        recent = candles[-20:]
        high = max(c.high for c in recent)
        low = min(c.low for c in recent)
        size = high - low
        
        if size / low > 0.03:
            return None
        
        older = candles[-40:-20]
        if older:
            older_avg = sum(c.close for c in older) / len(older)
            recent_avg = sum(c.close for c in recent) / len(recent)
            phase = "accumulation" if recent_avg < older_avg else "distribution"
            direction = "BULLISH" if phase == "accumulation" else "BEARISH"
        else:
            phase, direction = "accumulation", "BULLISH"
        
        return {"phase": phase, "direction": direction, "high": high, "low": low,
                "mid": (high + low) / 2, "size": size}
    
    @staticmethod
    def _detect_manipulation(candles: List[CandleData], range_info: dict) -> Optional[dict]:
        for i in range(-10, 0):
            c = candles[i]
            if range_info["direction"] == "BULLISH":
                if c.low < range_info["low"]:
                    for j in range(i+1, 0):
                        if j < len(candles) and candles[j].close > range_info["low"]:
                            return {"type": "STOP_HUNT_DOWN", "low": c.low, "confidence": 80}
            else:
                if c.high > range_info["high"]:
                    for j in range(i+1, 0):
                        if j < len(candles) and candles[j].close < range_info["high"]:
                            return {"type": "STOP_HUNT_UP", "high": c.high, "confidence": 80}
        return None
    
    @staticmethod
    def _build_model(range_info: dict, manipulation: dict) -> MarketMakerModel:
        if range_info["direction"] == "BULLISH":
            model_type = MarketMakerModelType.MMM_BUY
            entry_zone = (range_info["low"], range_info["mid"])
            sl = manipulation.get("low", range_info["low"]) * 0.998
            targets = [range_info["high"], range_info["high"] + range_info["size"] * 0.5,
                      range_info["high"] + range_info["size"]]
        else:
            model_type = MarketMakerModelType.MMM_SELL
            entry_zone = (range_info["mid"], range_info["high"])
            sl = manipulation.get("high", range_info["high"]) * 1.002
            targets = [range_info["low"], range_info["low"] - range_info["size"] * 0.5,
                      range_info["low"] - range_info["size"]]
        
        return MarketMakerModel(
            model_type=model_type, direction=range_info["direction"], confidence=75,
            phase="manipulation", entry_zone=entry_zone, stop_loss=sl,
            targets=targets, timestamp=datetime.utcnow(),
        )