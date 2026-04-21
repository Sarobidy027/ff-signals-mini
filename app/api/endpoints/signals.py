"""
Endpoints des signaux.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
import structlog

from app.api.dependencies import get_current_user
from app.services.signal_service import SignalService
from app.models.signal import Signal, SignalsResponse

logger = structlog.get_logger()
router = APIRouter(prefix="/signals", tags=["Signals"])


@router.get("/active", response_model=Optional[Signal])
async def get_active_signal(user=Depends(get_current_user)):
    """
    Retourne le signal actif actuel.
    """
    signal = SignalService.get_active_signal()
    logger.debug("active_signal_requested", found=signal is not None)
    return signal


@router.get("/list", response_model=SignalsResponse)
async def get_signals_list(
    trade_type: Optional[str] = Query(None, description="SCALP, DAY, SWING, ou ALL"),
    instrument: Optional[str] = Query(None, description="Filtrer par instrument"),
    status: Optional[str] = Query(None, description="PENDING, ACTIVE"),
    limit: int = Query(100, ge=1, le=500),
    user=Depends(get_current_user),
):
    """
    Retourne la liste des signaux avec filtres.
    
    - **trade_type**: SCALP, DAY, SWING, ou ALL
    - **instrument**: Nom de l'instrument (ex: EUR/USD)
    - **status**: PENDING ou ACTIVE
    - **limit**: Nombre maximum de résultats
    """
    response = SignalService.get_signals_list(
        trade_type=trade_type,
        instrument=instrument,
        status=status,
        limit=limit,
    )
    
    logger.debug(
        "signals_list_requested",
        trade_type=trade_type,
        instrument=instrument,
        total=response.total,
    )
    
    return response


@router.get("/{signal_id}", response_model=Signal)
async def get_signal_by_id(
    signal_id: str,
    user=Depends(get_current_user),
):
    """
    Retourne les détails d'un signal spécifique.
    """
    signal = SignalService.get_signal_by_id(signal_id)
    
    if not signal:
        logger.warning("signal_not_found", signal_id=signal_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Signal non trouvé",
        )
    
    return signal


@router.get("/instrument/{instrument}")
async def get_signals_by_instrument(
    instrument: str,
    days: int = Query(7, ge=1, le=30),
    user=Depends(get_current_user),
):
    """
    Retourne l'historique des signaux pour un instrument.
    """
    signals = SignalService.get_signals_by_instrument(instrument, days)
    return {
        "instrument": instrument,
        "count": len(signals),
        "signals": signals,
    }