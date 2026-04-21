"""
Fournisseur d'actualités économiques.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import aiohttp
import asyncio
import json
import structlog

logger = structlog.get_logger()


class NewsEvent:
    """Événement économique."""
    
    def __init__(self, title: str, currency: str, impact: int, timestamp: datetime):
        self.title = title
        self.currency = currency
        self.impact = impact
        self.timestamp = timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "currency": self.currency,
            "impact": self.impact,
            "impact_label": "HIGH" if self.impact == 3 else "MEDIUM" if self.impact == 2 else "LOW",
            "timestamp": self.timestamp.isoformat(),
        }


class NewsProvider:
    """Fournisseur d'actualités économiques."""
    
    BASE_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    _cache: Dict[str, tuple] = {}
    _cache_ttl = timedelta(hours=1)
    _session: Optional[aiohttp.ClientSession] = None
    
    @classmethod
    async def _get_session(cls) -> aiohttp.ClientSession:
        if cls._session is None or cls._session.closed:
            cls._session = aiohttp.ClientSession()
        return cls._session
    
    @classmethod
    async def fetch_news(cls) -> List[NewsEvent]:
        """Récupère les actualités de la semaine."""
        cache_key = "weekly_news"
        
        if cache_key in cls._cache:
            events, cache_time = cls._cache[cache_key]
            if datetime.utcnow() - cache_time < cls._cache_ttl:
                return events
        
        events = []
        try:
            session = await cls._get_session()
            async with session.get(cls.BASE_URL) as response:
                text = await response.text()
                data = json.loads(text)
                
                for item in data:
                    try:
                        title = item.get("title", "Unknown Event")
                        currency = item.get("country", "USD")
                        impact_str = item.get("impact", "")
                        
                        impact = 3 if "High" in impact_str else (2 if "Medium" in impact_str else 1)
                        
                        date_str = item.get("date", "")
                        if date_str:
                            timestamp = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                            
                            if impact >= 2:
                                events.append(NewsEvent(
                                    title=title,
                                    currency=currency,
                                    impact=impact,
                                    timestamp=timestamp,
                                ))
                    except Exception as e:
                        logger.debug("news_parse_error", error=str(e))
                        continue
            
            events.sort(key=lambda e: e.timestamp)
            cls._cache[cache_key] = (events, datetime.utcnow())
            logger.info("news_fetched", count=len(events))
            
        except Exception as e:
            logger.error("news_fetch_failed", error=str(e))
        
        return events
    
    @classmethod
    async def close(cls):
        if cls._session and not cls._session.closed:
            await cls._session.close()
            cls._session = None


async def generate_news(hours_ahead: int = 48) -> List[NewsEvent]:
    """Récupère les actualités à venir."""
    all_events = await NewsProvider.fetch_news()
    now = datetime.utcnow()
    cutoff = now + timedelta(hours=hours_ahead)
    return [e for e in all_events if now <= e.timestamp <= cutoff]


async def has_major_news(instrument: str, within_hours: int = 2) -> bool:
    """Vérifie s'il y a des actualités majeures pour un instrument."""
    currencies = extract_currencies(instrument)
    events = await generate_news(within_hours)
    
    for event in events:
        if event.currency in currencies and event.impact >= 2:
            return True
    return False


def extract_currencies(instrument: str) -> List[str]:
    """Extrait les devises d'une paire."""
    parts = instrument.split('/')
    return parts if len(parts) == 2 else []


async def get_sentiment(instrument: str) -> float:
    """Calcule le sentiment de marché."""
    from app.data.market_providers import MarketProviderFactory
    
    try:
        candles = await MarketProviderFactory.get_candles(instrument, "1H", 24)
        if not candles or len(candles) < 5:
            return 0.0
        
        closes = [c.close for c in candles]
        current = closes[-1]
        
        sma_8 = sum(closes[-8:]) / min(8, len(closes))
        sma_21 = sum(closes[-21:]) / min(21, len(closes))
        
        if current > sma_8 > sma_21:
            trend_score = 0.4
        elif current > sma_8:
            trend_score = 0.2
        elif current < sma_8 < sma_21:
            trend_score = -0.4
        elif current < sma_8:
            trend_score = -0.2
        else:
            trend_score = 0.0
        
        if len(closes) >= 6:
            momentum = (current - closes[-6]) / closes[-6]
            momentum_score = min(max(momentum * 5, -0.3), 0.3)
        else:
            momentum_score = 0.0
        
        sentiment = trend_score + momentum_score
        return max(-1.0, min(1.0, sentiment))
        
    except Exception as e:
        logger.error("sentiment_calculation_failed", instrument=instrument, error=str(e))
        return 0.0