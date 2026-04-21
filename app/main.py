"""
Point d'entrée principal de l'application FastAPI.
FF SIGNALS MINI - Backend API
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any
import structlog

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.database import init_database, close_database
from app.api.endpoints import auth_router, signals_router, performance_router, ws_router
from app.api.rate_limiter import RateLimiter
from app.engine import scheduler
from app.data import refresh_instrument_config
from app.data.market_providers import MarketProviderFactory
from app.services.persistence_service import PersistenceService

setup_logging()
logger = structlog.get_logger()

rate_limiter = RateLimiter(max_requests=100, window_seconds=60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie."""
    logger.info("starting_application", app_name=settings.APP_NAME, version=settings.APP_VERSION)
    
    await init_database()
    logger.info("database_initialized")
    
    try:
        await MarketProviderFactory.initialize()
        status = MarketProviderFactory.get_status()
        logger.info("market_providers_initialized", status=status)
    except Exception as e:
        logger.error("market_providers_failed", error=str(e))
    
    try:
        await refresh_instrument_config()
        logger.info("instrument_config_refreshed")
    except Exception as e:
        logger.warning("instrument_config_failed", error=str(e))
    
    await PersistenceService.restore_state()
    logger.info("state_restored")
    
    try:
        await scheduler.start()
        logger.info("scheduler_started")
    except Exception as e:
        logger.error("scheduler_failed", error=str(e))
    
    logger.info("application_ready")
    
    yield
    
    logger.info("shutting_down")
    await PersistenceService.save_state()
    await scheduler.stop()
    await close_database()
    logger.info("shutdown_complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Plateforme de signaux ICT + SMC + VSA + Fondamental - Win Rate 90-94%",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Middleware de rate limiting."""
    client_ip = request.client.host if request.client else "unknown"
    
    if not rate_limiter.is_allowed(client_ip):
        logger.warning("rate_limit_exceeded", ip=client_ip)
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."}
        )
    
    response = await call_next(request)
    return response


app.include_router(auth_router, prefix="/api")
app.include_router(signals_router, prefix="/api")
app.include_router(performance_router, prefix="/api")
app.include_router(ws_router, prefix="")


@app.get("/")
async def root() -> Dict[str, Any]:
    """Endpoint racine."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "providers": MarketProviderFactory.get_status(),
        "win_rate_target": "90-94%",
        "daily_signals_target": 75,
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "api": "/api",
            "websocket": "/ws/dashboard",
        },
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check pour Render."""
    from app.core.database import get_db_health
    from app.services.cache_service import CacheService
    
    db_healthy = await get_db_health()
    providers = MarketProviderFactory.get_status()
    cache_size = CacheService.size()
    
    all_healthy = db_healthy and all(p == "healthy" for p in providers.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": "healthy" if db_healthy else "unhealthy",
            "providers": providers,
            "cache": {"size": cache_size},
            "scheduler": "running" if scheduler.running else "stopped",
        },
    }


@app.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """Statistiques détaillées de l'application."""
    return {
        "signals": {
            "active": len(scheduler.get_active()),
            "pending": len(scheduler.get_pending()),
            "total": len(scheduler.signals),
        },
        "connections": {
            "websocket": scheduler.get_connection_count() if hasattr(scheduler, 'get_connection_count') else 0,
        },
        "uptime": "N/A",
        "version": settings.APP_VERSION,
    }