"""Analyseur d'impact des news."""
from typing import Dict, Any
from app.data.news import has_major_news, extract_currencies, generate_news


class NewsImpactAnalyzer:
    @staticmethod
    async def analyze(instrument: str, hours: int = 2) -> Dict[str, Any]:
        currencies = extract_currencies(instrument)
        events = await generate_news(hours)
        relevant = [e for e in events if e.currency in currencies]
        
        high = any(e.impact == 3 for e in relevant)
        medium = any(e.impact == 2 for e in relevant)
        
        return {
            "instrument": instrument, "currencies": currencies,
            "safe_to_trade": not high,
            "impact_score": 80 if high else (40 if medium else 0),
            "high_impact": high, "medium_impact": medium,
            "upcoming_events": [e.to_dict() for e in relevant[:5]],
            "has_major_news": await has_major_news(instrument, hours),
        }
    
    @staticmethod
    async def has_major_news(instrument: str, hours: int = 2) -> bool:
        return await has_major_news(instrument, hours)