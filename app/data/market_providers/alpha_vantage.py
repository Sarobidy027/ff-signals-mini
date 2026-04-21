"""
Fournisseur Alpha Vantage.
"""
import os
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.data.market_providers.base_provider import BaseMarketProvider, CandleData


class AlphaVantageProvider(BaseMarketProvider):
    """Fournisseur Alpha Vantage."""
    
    BASE_URL = "https://www.alphavantage.co/query"
    _SYMBOL_MAPPING = {
        "EUR/USD": ("EUR", "USD"), "GBP/USD": ("GBP", "USD"),
        "USD/JPY": ("USD", "JPY"), "AUD/USD": ("AUD", "USD"),
        "USD/CAD": ("USD", "CAD"), "USD/CHF": ("USD", "CHF"),
        "NZD/USD": ("NZD", "USD"), "EUR/GBP": ("EUR", "GBP"),
        "GBP/JPY": ("GBP", "JPY"), "EUR/JPY": ("EUR", "JPY"),
        "AUD/NZD": ("AUD", "NZD"), "EUR/CHF": ("EUR", "CHF"),
    }
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("ALPHA_VANTAGE_API_KEY", ""))
        self._session: Optional[aiohttp.ClientSession] = None
        self._request_count = 0
        self._last_request = datetime.utcnow()
        self._rate_lock = asyncio.Lock()
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def _respect_rate_limit(self) -> None:
        async with self._rate_lock:
            self._request_count += 1
            if self._request_count >= 5:
                elapsed = (datetime.utcnow() - self._last_request).total_seconds()
                if elapsed < 60:
                    await asyncio.sleep(60 - elapsed + 1)
                self._request_count = 0
                self._last_request = datetime.utcnow()
    
    async def _make_request(self, params: Dict[str, str]) -> Dict[str, Any]:
        if not self.api_key:
            return {}
        await self._respect_rate_limit()
        params["apikey"] = self.api_key
        try:
            session = await self._get_session()
            async with session.get(self.BASE_URL, params=params) as resp:
                return await resp.json()
        except Exception:
            return {}
    
    async def fetch_candles(self, symbol: str, interval: str = "15m", count: int = 200) -> List[CandleData]:
        if symbol not in self._SYMBOL_MAPPING:
            return []
        from_cur, to_cur = self._SYMBOL_MAPPING[symbol]
        av_interval = {"1m": "1min", "5m": "5min", "15m": "15min", "1H": "60min"}.get(interval, "15min")
        
        params = {"function": "FX_INTRADAY", "from_symbol": from_cur, "to_symbol": to_cur,
                  "interval": av_interval, "outputsize": "compact" if count <= 100 else "full"}
        data = await self._make_request(params)
        
        time_series = data.get(f"Time Series FX ({av_interval})", {})
        candles = []
        for ts_str, values in time_series.items():
            candles.append(CandleData(
                timestamp=datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S"),
                open=float(values["1. open"]), high=float(values["2. high"]),
                low=float(values["3. low"]), close=float(values["4. close"]), volume=0.0,
            ))
        candles.sort(key=lambda c: c.timestamp)
        return candles[-count:]
    
    async def fetch_current_price(self, symbol: str) -> float:
        if symbol not in self._SYMBOL_MAPPING:
            return 0.0
        from_cur, to_cur = self._SYMBOL_MAPPING[symbol]
        params = {"function": "CURRENCY_EXCHANGE_RATE", "from_currency": from_cur, "to_currency": to_cur}
        data = await self._make_request(params)
        try:
            return float(data.get("Realtime Currency Exchange Rate", {}).get("5. Exchange Rate", 0))
        except (ValueError, TypeError):
            return 0.0
    
    async def get_instrument_info(self, symbol: str) -> Dict[str, Any]:
        configs = {"EUR/USD": {"pip_value": 0.0001, "spread": 0.0001, "digits": 5}}
        config = configs.get(symbol, {"pip_value": 0.0001, "spread": 0.0001, "digits": 5})
        price = await self.get_current_price_with_cache(symbol)
        return {"symbol": symbol, "pip_value": config["pip_value"], "spread": config["spread"],
                "digits": config["digits"], "base_price": price if price > 0 else 1.0, "volatility": 0.001}