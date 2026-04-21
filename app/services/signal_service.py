"""
Service de gestion des signaux.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import structlog

from app.models.signal import Signal, SignalsResponse, SignalStatus, TradeType
from app.engine import scheduler
from app.services.cache_service import CacheService

logger = structlog.get_logger()


class SignalService:
    """Service pour les opérations sur les signaux."""
    
    @staticmethod
    def get_active_signal() -> Optional[Signal]:
        """Retourne le signal actif le plus récent."""
        cache_key = "active_signal"
        cached = CacheService.get(cache_key)
        if cached:
            return cached
        
        try:
            active = scheduler.get_active()
            if active:
                signal = sorted(active, key=lambda s: s.entry_time, reverse=True)[0]
                CacheService.set(cache_key, signal, ttl=30)
                return signal
        except Exception as e:
            logger.error("get_active_signal_failed", error=str(e))
        return None
    
    @staticmethod
    def get_signals_list(
        trade_type: Optional[str] = None,
        instrument: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> SignalsResponse:
        """Retourne la liste filtrée des signaux."""
        cache_key = f"signals_list_{trade_type}_{instrument}_{status}_{limit}"
        cached = CacheService.get(cache_key)
        if cached:
            return cached
        
        try:
            active = scheduler.get_active()
            pending = scheduler.get_pending()
            
            if trade_type and trade_type != "ALL":
                active = [s for s in active if s.trade_type.value == trade_type]
                pending = [s for s in pending if s.trade_type.value == trade_type]
            
            if instrument and instrument != "ALL":
                active = [s for s in active if s.instrument == instrument]
                pending = [s for s in pending if s.instrument == instrument]
            
            if status:
                if status == "ACTIVE":
                    pending = []
                elif status == "PENDING":
                    active = []
            
            active.sort(key=lambda s: s.entry_time)
            pending.sort(key=lambda s: s.entry_time)
            
            response = SignalsResponse(
                active=active[:limit],
                pending=pending[:limit],
                total=len(active) + len(pending),
            )
            
            CacheService.set(cache_key, response, ttl=30)
            return response
            
        except Exception as e:
            logger.error("get_signals_list_failed", error=str(e))
            return SignalsResponse(active=[], pending=[], total=0)
    
    @staticmethod
    def get_signal_by_id(signal_id: str) -> Optional[Signal]:
        """Retourne un signal par son ID."""
        cache_key = f"signal_{signal_id}"
        cached = CacheService.get(cache_key)
        if cached:
            return cached
        
        try:
            signal = scheduler.get_by_id(signal_id)
            if signal:
                CacheService.set(cache_key, signal, ttl=60)
            return signal
        except Exception as e:
            logger.error("get_signal_by_id_failed", error=str(e), signal_id=signal_id)
            return None
    
    @staticmethod
    def get_signals_by_instrument(instrument: str, days: int = 7) -> List[Signal]:
        """Retourne l'historique des signaux pour un instrument."""
        try:
            all_signals = scheduler.signals
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            filtered = [
                s for s in all_signals
                if s.instrument == instrument and s.created_at >= cutoff
            ]
            filtered.sort(key=lambda s: s.created_at, reverse=True)
            
            return filtered
        except Exception as e:
            logger.error("get_signals_by_instrument_failed", error=str(e), instrument=instrument)
            return []
    
    @staticmethod
    def get_scalp_signals_count() -> int:
        """Retourne le nombre de signaux SCALP générés aujourd'hui."""
        today = datetime.utcnow().date()
        scalp_signals = [
            s for s in scheduler.signals
            if s.trade_type == TradeType.SCALP and s.created_at.date() == today
        ]
        return len(scalp_signals)
    
    @staticmethod
    def get_signals_anticipation_stats() -> Dict[str, Any]:
        """Retourne les statistiques d'anticipation des signaux."""
        closed = [s for s in scheduler.signals if s.status == SignalStatus.CLOSED and s.result]
        
        if not closed:
            return {"scalp": 5, "day": 15, "swing": 180}
        
        anticipation_stats = {"scalp": [], "day": [], "swing": []}
        
        for s in closed:
            if s.exit_time:
                actual_duration = (s.exit_time - s.entry_time).total_seconds() / 60
                trade_type = s.trade_type.value
                anticipation_stats[trade_type].append(actual_duration)
        
        return {
            "scalp": int(sum(anticipation_stats["scalp"]) / max(len(anticipation_stats["scalp"]), 1)),
            "day": int(sum(anticipation_stats["day"]) / max(len(anticipation_stats["day"]), 1)),
            "swing": int(sum(anticipation_stats["swing"]) / max(len(anticipation_stats["swing"]), 1)),
        }