"""
Configuration des instruments de trading.
16 instruments : 12 Forex + 4 Crypto.
"""
from typing import List, Dict, Any
import structlog

from app.core.config import settings

logger = structlog.get_logger()

FOREX_PAIRS: List[str] = [
    "EUR/USD", "USD/JPY", "GBP/USD", "AUD/USD", "USD/CAD", "USD/CHF",
    "NZD/USD", "EUR/GBP", "GBP/JPY", "EUR/JPY", "AUD/NZD", "EUR/CHF",
]

CRYPTO_PAIRS: List[str] = [
    "BTC/USD", "ETH/USD", "XRP/USD", "LTC/USD",
]

ALL_INSTRUMENTS: List[str] = FOREX_PAIRS + CRYPTO_PAIRS

INSTRUMENT_CONFIG: Dict[str, Dict[str, Any]] = {
    "EUR/USD": {"pip_value": 0.0001, "spread": 0.0001, "digits": 5, "base_price": 1.0850, "volatility": 0.006},
    "USD/JPY": {"pip_value": 0.01, "spread": 0.02, "digits": 3, "base_price": 148.50, "volatility": 0.007},
    "GBP/USD": {"pip_value": 0.0001, "spread": 0.00015, "digits": 5, "base_price": 1.2650, "volatility": 0.008},
    "AUD/USD": {"pip_value": 0.0001, "spread": 0.00012, "digits": 5, "base_price": 0.6550, "volatility": 0.007},
    "USD/CAD": {"pip_value": 0.0001, "spread": 0.00015, "digits": 5, "base_price": 1.3550, "volatility": 0.006},
    "USD/CHF": {"pip_value": 0.0001, "spread": 0.00015, "digits": 5, "base_price": 0.8750, "volatility": 0.006},
    "NZD/USD": {"pip_value": 0.0001, "spread": 0.00015, "digits": 5, "base_price": 0.6050, "volatility": 0.007},
    "EUR/GBP": {"pip_value": 0.0001, "spread": 0.00012, "digits": 5, "base_price": 0.8575, "volatility": 0.005},
    "GBP/JPY": {"pip_value": 0.01, "spread": 0.025, "digits": 3, "base_price": 187.50, "volatility": 0.010},
    "EUR/JPY": {"pip_value": 0.01, "spread": 0.02, "digits": 3, "base_price": 161.00, "volatility": 0.008},
    "AUD/NZD": {"pip_value": 0.0001, "spread": 0.0002, "digits": 5, "base_price": 1.0825, "volatility": 0.006},
    "EUR/CHF": {"pip_value": 0.0001, "spread": 0.00015, "digits": 5, "base_price": 0.9500, "volatility": 0.004},
    "BTC/USD": {"pip_value": 1.0, "spread": 5.0, "digits": 2, "base_price": 43500.00, "volatility": 0.025},
    "ETH/USD": {"pip_value": 0.01, "spread": 0.05, "digits": 2, "base_price": 2250.00, "volatility": 0.030},
    "XRP/USD": {"pip_value": 0.0001, "spread": 0.0002, "digits": 4, "base_price": 0.5200, "volatility": 0.025},
    "LTC/USD": {"pip_value": 0.01, "spread": 0.03, "digits": 2, "base_price": 68.00, "volatility": 0.028},
}


async def refresh_instrument_config() -> None:
    """Rafraîchit la configuration avec les prix réels."""
    from app.data.market_providers import MarketProviderFactory
    
    logger.info("refreshing_instrument_config")
    
    for symbol in ALL_INSTRUMENTS:
        try:
            info = await MarketProviderFactory.get_instrument_info(symbol)
            current = await MarketProviderFactory.get_current_price(symbol)
            
            if current > 0:
                INSTRUMENT_CONFIG[symbol]["base_price"] = current
                INSTRUMENT_CONFIG[symbol]["spread"] = info.get("spread", INSTRUMENT_CONFIG[symbol]["spread"])
            
            logger.debug("instrument_config_updated", symbol=symbol, price=current)
            
        except Exception as e:
            logger.warning("instrument_config_refresh_failed", symbol=symbol, error=str(e))
    
    logger.info("instrument_config_refreshed", count=len(ALL_INSTRUMENTS))


def get_pip_value(instrument: str) -> float:
    """Retourne la valeur d'un pip."""
    return INSTRUMENT_CONFIG.get(instrument, {}).get("pip_value", 0.0001)


def get_spread(instrument: str) -> float:
    """Retourne le spread moyen."""
    return INSTRUMENT_CONFIG.get(instrument, {}).get("spread", 0.0001)


def get_digits(instrument: str) -> int:
    """Retourne le nombre de décimales."""
    return INSTRUMENT_CONFIG.get(instrument, {}).get("digits", 5)


def calculate_pips(entry: float, exit: float, instrument: str) -> float:
    """Calcule le nombre de pips gagnés ou perdus."""
    pip_value = get_pip_value(instrument)
    if pip_value == 0:
        return 0.0
    return (exit - entry) / pip_value


async def get_current_price(instrument: str) -> float:
    """Récupère le prix actuel d'un instrument."""
    from app.data.market_providers import MarketProviderFactory
    return await MarketProviderFactory.get_current_price(instrument)


async def get_instrument_info(instrument: str) -> Dict[str, Any]:
    """Récupère les informations complètes d'un instrument."""
    from app.data.market_providers import MarketProviderFactory
    
    info = await MarketProviderFactory.get_instrument_info(instrument)
    config = INSTRUMENT_CONFIG.get(instrument, {})
    
    return {
        "symbol": instrument,
        "pip_value": config.get("pip_value", 0.0001),
        "spread": config.get("spread", 0.0001),
        "digits": config.get("digits", 5),
        "base_price": info.get("base_price", 1.0),
        "volatility": config.get("volatility", 0.001),
        "type": "forex" if instrument in FOREX_PAIRS else "crypto",
    }