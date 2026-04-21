"""
Endpoints de performance.
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
import structlog

from app.api.dependencies import get_current_user
from app.services.performance_service import PerformanceService
from app.models.performance import PerformanceStats, RecentSignal, PerformanceHistory

logger = structlog.get_logger()
router = APIRouter(prefix="/performance", tags=["Performance"])


@router.get("", response_model=PerformanceStats)
async def get_performance_stats(user=Depends(get_current_user)):
    """
    Retourne les statistiques de performance globales.
    """
    stats = PerformanceService.get_current_stats()
    logger.debug("performance_stats_requested", win_rate=stats.win_rate)
    return stats


@router.get("/recent", response_model=List[RecentSignal])
async def get_recent_signals(
    limit: int = Query(3, ge=1, le=20),
    user=Depends(get_current_user),
):
    """
    Retourne les derniers signaux clôturés.
    """
    signals = PerformanceService.get_recent(limit)
    logger.debug("recent_signals_requested", count=len(signals))
    return signals


@router.get("/history", response_model=List[PerformanceHistory])
async def get_performance_history(
    days: int = Query(30, ge=1, le=90),
    user=Depends(get_current_user),
):
    """
    Retourne l'historique des performances quotidiennes.
    """
    history = PerformanceService.get_history(days)
    return history


@router.get("/by-instrument")
async def get_performance_by_instrument(
    days: int = Query(30, ge=1, le=90),
    user=Depends(get_current_user),
):
    """
    Retourne les performances détaillées par instrument.
    """
    stats = PerformanceService.get_stats_by_instrument(days)
    return {
        "period_days": days,
        "instruments": stats,
    }


@router.get("/by-trade-type")
async def get_performance_by_trade_type(
    days: int = Query(30, ge=1, le=90),
    user=Depends(get_current_user),
):
    """
    Retourne les performances par type de trade.
    """
    stats = PerformanceService.get_stats_by_trade_type(days)
    return {
        "period_days": days,
        "trade_types": stats,
    }


@router.get("/summary")
async def get_performance_summary(user=Depends(get_current_user)):
    """
    Retourne un résumé complet des performances.
    """
    return PerformanceService.get_summary()