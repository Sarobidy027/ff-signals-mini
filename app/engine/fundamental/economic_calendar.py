"""Calendrier économique."""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.data.news import generate_news


class EconomicCalendar:
    @staticmethod
    async def get_events(instrument: str = None, hours: int = 24) -> List[Dict[str, Any]]:
        events = await generate_news(hours)
        return [e.to_dict() for e in events]
    
    @staticmethod
    async def get_high_impact(hours: int = 24) -> List[Dict[str, Any]]:
        events = await generate_news(hours)
        return [e.to_dict() for e in events if e.impact == 3]
    
    @staticmethod
    async def get_next_major(instrument: str = None) -> Dict[str, Any]:
        events = await generate_news(72)
        if events:
            return events[0].to_dict()
        return {"title": "No major events", "currency": "N/A", "impact": 0,
                "timestamp": (datetime.utcnow() + timedelta(days=1)).isoformat()}