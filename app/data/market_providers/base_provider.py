"""
Fournisseur de données de base.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import structlog

logger = structlog.get_logger()


@dataclass
class CandleData:
    """Structure de bougie standardisée."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    @property
    def is_bullish(self) -> bool:
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        return self.close < self.open
    
    @property
    def body_size(self) -> float:
        return abs(self.close - self.open)
    
    @property
    def upper_wick(self) -> float:
        return self.high - max(self.open, self.close)
    
    @property
    def lower_wick(self) -> float:
        return min(self.open, self.close) - self.low
    
    @property
    def range(self) -> float:
        return self.high - self.low
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


class BaseMarketProvider(ABC):
    """Classe abstraite pour les fournisseurs de données."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._cache: Dict[str, tuple] = {}
        self._cache_ttl = timedelta(minutes=1)
        self._price_cache: Dict[str, tuple] = {}
        self._price_cache_ttl = timedelta(seconds=10)
        self._lock = asyncio.Lock()
    
    @abstractmethod
    async def fetch_candles(self, symbol: str, interval: str = "15m", count: int = 200) -> List[CandleData]:
        """Récupère les bougies."""
        pass
    
    @abstractmethod
    async def fetch_current_price(self, symbol: str) -> float:
        """Récupère le prix actuel."""
        pass
    
    @abstractmethod
    async def get_instrument_info(self, symbol: str) -> Dict[str, Any]:
        """Récupère les informations de l'instrument."""
        pass
    
    async def get_candles_with_cache(self, symbol: str, interval: str = "15m", count: int = 200) -> List[CandleData]:
        """Récupère les bougies avec cache."""
        cache_key = f"{symbol}_{interval}"
        
        async with self._lock:
            if cache_key in self._cache:
                candles, cache_time = self._cache[cache_key]
                if datetime.utcnow() - cache_time < self._cache_ttl and len(candles) >= count:
                    return candles[-count:]
        
        try:
            candles = await self.fetch_candles(symbol, interval, count)
            if candles:
                async with self._lock:
                    self._cache[cache_key] = (candles, datetime.utcnow())
                logger.debug("candles_fetched", symbol=symbol, interval=interval, count=len(candles))
            return candles[-count:] if len(candles) >= count else candles
        except Exception as e:
            logger.error("candles_fetch_failed", symbol=symbol, error=str(e))
            async with self._lock:
                if cache_key in self._cache:
                    candles, _ = self._cache[cache_key]
                    return candles[-count:] if len(candles) >= count else candles
            return []
    
    async def get_current_price_with_cache(self, symbol: str) -> float:
        """Récupère le prix actuel avec cache."""
        cache_key = f"price_{symbol}"
        
        async with self._lock:
            if cache_key in self._price_cache:
                price, cache_time = self._price_cache[cache_key]
                if datetime.utcnow() - cache_time < self._price_cache_ttl:
                    return price
        
        try:
            price = await self.fetch_current_price(symbol)
            if price > 0:
                async with self._lock:
                    self._price_cache[cache_key] = (price, datetime.utcnow())
            return price
        except Exception as e:
            logger.error("price_fetch_failed", symbol=symbol, error=str(e))
            async with self._lock:
                if cache_key in self._price_cache:
                    price, _ = self._price_cache[cache_key]
                    return price
            return 0.0
    
    def _normalize_symbol(self, symbol: str) -> str:
        return symbol
    
    def _convert_timeframe(self, interval: str) -> str:
        mapping = {
            "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m",
            "1H": "1h", "1h": "1h", "4H": "4h", "1D": "1d",
        }
        return mapping.get(interval, "15m")