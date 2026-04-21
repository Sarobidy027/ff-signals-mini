"""
Configuration de l'application.
Compatible Pydantic v2.
"""
from typing import List, Optional
import os

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Paramètres de configuration."""
    
    APP_NAME: str = "FF SIGNALS MINI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    PIN_CODE: str = "08042026"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "https://ff-signals-mini.netlify.app",
    ]
    
    ALPHA_VANTAGE_API_KEY: str = ""
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/ff_signals.db"
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    SCALP_ANTICIPATION_MINUTES: int = 5
    DAY_ANTICIPATION_MINUTES: int = 15
    SWING_ANTICIPATION_HOURS: int = 3
    
    SCALP_MULTIPLIER: int = 2
    FOREX_PAIRS_COUNT: int = 12
    CRYPTO_PAIRS_COUNT: int = 4
    TOTAL_INSTRUMENTS: int = 16
    
    TARGET_DAILY_SIGNALS: int = 75
    TARGET_WIN_RATE: float = 0.90
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()