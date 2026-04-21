"""Endpoints module."""
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.signals import router as signals_router
from app.api.endpoints.performance import router as performance_router
from app.api.endpoints.ws import router as ws_router

__all__ = ["auth_router", "signals_router", "performance_router", "ws_router"]