"""
Fournisseur Yahoo Finance.
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from app.data.market_providers.base_provider import BaseMarketProvider, CandleData

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    yf = None


class YahooFinanceProvider(BaseMarketProvider):
    """Fournisseur Yahoo Finance."""
    
    _SYMBOL_MAPPING = {
        "EUR/USD": "EURUSD=X", "GBP/USD": "GBPUSD=X", "USD/JPY": "JPY=X",
        "AUD/USD": "AUDUSD=X", "USD/CAD": "CAD=X", "USD/CHF": "CHF=X",
        "NZD/USD": "NZDUSD=X", "EUR/GBP": "EURGBP=X", "GBP/JPY": "GBPJPY=X",
        "EUR/JPY": "EURJPY=X", "AUD/NZD": "AUDNZD=X", "EUR/CHF": "EURCHF=X",
        "BTC/USD": "BTC-USD", "ETH/USD": "ETH-USD", "XRP/USD": "XRP-USD", "LTC/USD": "LTC-USD",
    }
    
    _INSTRUMENT_CONFIG = {
        "EUR/USD": {"pip_value": 0.0001, "spread": 0.0001, "digits": 5},
        "USD/JPY": {"pip_value": 0.01, "spread": 0.02, "digits": 3},
        "GBP/USD": {"pip_value": 0.0001, "spread": 0.00015, "digits": 5},
        "BTC/USD": {"pip_value": 1.0, "spread": 5.0, "digits": 2},
    }
    
    def __init__(self):
        super().__init__()
        self._executor = ThreadPoolExecutor(max_workers=4)
    
    def _normalize_symbol(self, symbol: str) -> str:
        return self._SYMBOL_MAPPING.get(symbol, symbol)
    
    async def fetch_candles(self, symbol: str, interval: str = "15m", count: int = 200) -> List[CandleData]:
        if not YFINANCE_AVAILABLE:
            return []
        
        try:
            yf_symbol = self._normalize_symbol(symbol)
            period = "1mo" if interval in ["1m", "5m", "15m", "30m"] else "3mo"
            yf_interval = self._convert_timeframe(interval)
            
            loop = asyncio.get_event_loop()
            
            def _fetch():
                ticker = yf.Ticker(yf_symbol)
                return ticker.history(period=period, interval=yf_interval)
            
            df = await loop.run_in_executor(self._executor, _fetch)
            
            if df.empty:
                return []
            
            candles = []
            for idx, row in df.iterrows():
                candles.append(CandleData(
                    timestamp=idx.to_pydatetime() if hasattr(idx, 'to_pydatetime') else idx,
                    open=float(row['Open']), high=float(row['High']),
                    low=float(row['Low']), close=float(row['Close']),
                    volume=float(row['Volume']) if 'Volume' in row else 0.0,
                ))
            
            candles.sort(key=lambda c: c.timestamp)
            return candles[-count:]
        except Exception as e:
            return []
    
    async def fetch_current_price(self, symbol: str) -> float:
        if not YFINANCE_AVAILABLE:
            return 0.0
        
        try:
            yf_symbol = self._normalize_symbol(symbol)
            loop = asyncio.get_event_loop()
            
            def _fetch():
                ticker = yf.Ticker(yf_symbol)
                try:
                    info = ticker.fast_info
                    if hasattr(info, 'last_price') and info.last_price:
                        return float(info.last_price)
                except Exception:
                    pass
                df = ticker.history(period="1d", interval="1m")
                if not df.empty:
                    return float(df['Close'].iloc[-1])
                return 0.0
            
            return await loop.run_in_executor(self._executor, _fetch)
        except Exception:
            return 0.0
    
    async def get_instrument_info(self, symbol: str) -> Dict[str, Any]:
        config = self._INSTRUMENT_CONFIG.get(symbol, {"pip_value": 0.0001, "spread": 0.0001, "digits": 5})
        price = await self.get_current_price_with_cache(symbol)
        return {
            "symbol": symbol, "pip_value": config["pip_value"],
            "spread": config["spread"], "digits": config["digits"],
            "base_price": price if price > 0 else 1.0, "volatility": 0.001,
        }