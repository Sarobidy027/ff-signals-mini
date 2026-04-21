"""Analyseur de sentiment."""
from typing import Dict, Any
from app.data.news import get_sentiment


class SentimentAnalyzer:
    @staticmethod
    async def analyze(instrument: str) -> Dict[str, Any]:
        raw = await get_sentiment(instrument)
        
        if raw > 0.3:
            sentiment, strength = "BULLISH", raw
        elif raw < -0.3:
            sentiment, strength = "BEARISH", abs(raw)
        else:
            sentiment, strength = "NEUTRAL", 0.5 - abs(raw)
        
        return {
            "instrument": instrument, "sentiment": sentiment,
            "raw_score": round(raw, 3), "strength": round(strength, 3),
            "confidence": round(strength * 100, 1),
        }
    
    @staticmethod
    def is_aligned(sentiment: str, direction: str) -> bool:
        if sentiment == "NEUTRAL":
            return True
        return (sentiment == "BULLISH" and direction == "BUY") or \
               (sentiment == "BEARISH" and direction == "SELL")