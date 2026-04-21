"""
Factory pour les fournisseurs de données.
"""
from typing import Dict, Any, List

from app.data.market_providers.base_provider import BaseMarketProvider, CandleData
from app.data.market_providers.yahoo_finance import YahooFinanceProvider, YFINANCE_AVAILABLE
from app.data.market_providers.alpha_vantage import AlphaVantageProvider
from app.data.market_providers.forex_provider import ForexProvider


class MarketProviderFactory:
    """Factory de fournisseurs."""
    
    _providers: Dict[str, BaseMarketProvider] = {}
    _status: Dict[str, str] = {}
    _initialized: bool = False
    
    @classmethod
    async def initialize(cls) -> None:
        if cls._initialized:
            return
        
        if YFINANCE_AVAILABLE:
            cls._providers["yahoo"] = YahooFinanceProvider()
            cls._status["yahoo"] = "healthy"
        else:
            cls._status["yahoo"] = "unavailable"
        
        av = AlphaVantageProvider()
        if av.api_key:
            cls._providers["alphavantage"] = av
            cls._status["alphavantage"] = "healthy"
        else:
            cls._status["alphavantage"] = "no_key"
        
        cls._providers["forex"] = ForexProvider()
        cls._status["forex"] = "healthy"
        cls._initialized = True
    
    @classmethod
    def get_provider(cls, symbol: str) -> BaseMarketProvider:
        if not cls._initialized:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(cls.initialize())
            except Exception:
                pass
        
        is_crypto = any(c in symbol for c in ["BTC", "ETH", "XRP", "LTC"])
        if is_crypto and "yahoo" in cls._providers:
            return cls._providers["yahoo"]
        if "alphavantage" in cls._providers:
            return cls._providers["alphavantage"]
        if "yahoo" in cls._providers:
            return cls._providers["yahoo"]
        return cls._providers.get("forex", ForexProvider())
    
    @classmethod
    async def get_candles(cls, symbol: str, interval: str = "15m", count: int = 200) -> List[CandleData]:
        await cls.initialize()
        provider = cls.get_provider(symbol)
        return await provider.get_candles_with_cache(symbol, interval, count)
    
    @classmethod
    async def get_current_price(cls, symbol: str) -> float:
        await cls.initialize()
        provider = cls.get_provider(symbol)
        return await provider.get_current_price_with_cache(symbol)
    
    @classmethod
    async def get_instrument_info(cls, symbol: str) -> Dict[str, Any]:
        await cls.initialize()
        provider = cls.get_provider(symbol)
        return await provider.get_instrument_info(symbol)
    
    @classmethod
    def get_status(cls) -> Dict[str, str]:
        return cls._status.copy()