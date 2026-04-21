"""
Service de calcul des performances.
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
import numpy as np
import structlog

from app.models.signal import Signal, SignalStatus, SignalResult, TradeType
from app.models.performance import (
    PerformanceStats, RecentSignal, PerformanceHistory,
    InstrumentPerformance, TradeTypePerformance, PerformanceSummary,
)
from app.engine import scheduler
from app.services.cache_service import CacheService
from app.core.config import settings

logger = structlog.get_logger()


class PerformanceService:
    """Service pour les statistiques de performance."""
    
    @staticmethod
    def calculate_stats(signals: List[Signal]) -> PerformanceStats:
        """Calcule les statistiques à partir d'une liste de signaux."""
        closed = [s for s in signals if s.status == SignalStatus.CLOSED and s.result is not None]
        
        if not closed:
            return PerformanceStats(
                win_rate=0.0,
                total_signals=0,
                wins=0,
                losses=0,
                average_pips_gained=0.0,
                largest_win=0.0,
                largest_loss=0.0,
                profit_factor=0.0,
                last_updated=datetime.utcnow(),
                win_rate_target=settings.TARGET_WIN_RATE * 100,
            )
        
        wins = [s for s in closed if s.result == SignalResult.WIN]
        losses = [s for s in closed if s.result == SignalResult.LOSS]
        
        win_rate = (len(wins) / len(closed)) * 100 if closed else 0.0
        
        win_pips = [s.pips_gained for s in wins if s.pips_gained is not None]
        loss_pips = [abs(s.pips_gained) for s in losses if s.pips_gained is not None]
        all_pips = [s.pips_gained for s in closed if s.pips_gained is not None]
        
        avg_pips = float(np.mean(all_pips)) if all_pips else 0.0
        largest_win = max(win_pips) if win_pips else 0.0
        largest_loss = max(loss_pips) if loss_pips else 0.0
        
        gross_profit = sum(win_pips) if win_pips else 0.0
        gross_loss = sum(loss_pips) if loss_pips else 1.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0
        
        return PerformanceStats(
            win_rate=round(win_rate, 1),
            total_signals=len(closed),
            wins=len(wins),
            losses=len(losses),
            average_pips_gained=round(avg_pips, 1),
            largest_win=round(largest_win, 1),
            largest_loss=round(largest_loss, 1),
            profit_factor=round(profit_factor, 2),
            last_updated=datetime.utcnow(),
            win_rate_target=settings.TARGET_WIN_RATE * 100,
        )
    
    @staticmethod
    def get_recent_signals(signals: List[Signal], limit: int = 3) -> List[RecentSignal]:
        """Retourne les signaux récemment clôturés."""
        closed = [s for s in signals if s.status == SignalStatus.CLOSED and s.result is not None]
        closed.sort(key=lambda s: s.updated_at, reverse=True)
        
        recent = []
        for signal in closed[:limit]:
            recent.append(RecentSignal(
                id=signal.id,
                instrument=signal.instrument,
                direction=signal.direction.value,
                result=signal.result.value,
                pips_gained=signal.pips_gained or 0.0,
                closed_at=signal.updated_at,
            ))
        return recent
    
    @staticmethod
    def get_current_stats() -> PerformanceStats:
        """Retourne les statistiques actuelles."""
        cache_key = "performance_stats"
        cached = CacheService.get(cache_key)
        if cached:
            return cached
        
        try:
            stats = PerformanceService.calculate_stats(scheduler.signals)
            CacheService.set(cache_key, stats, ttl=30)
            return stats
        except Exception as e:
            logger.error("get_current_stats_failed", error=str(e))
            return PerformanceStats(
                win_rate=0.0, total_signals=0, wins=0, losses=0,
                average_pips_gained=0.0, largest_win=0.0, largest_loss=0.0,
                profit_factor=0.0, last_updated=datetime.utcnow(),
                win_rate_target=settings.TARGET_WIN_RATE * 100,
            )
    
    @staticmethod
    def get_recent(limit: int = 3) -> List[RecentSignal]:
        """Retourne les signaux récents."""
        try:
            return PerformanceService.get_recent_signals(scheduler.signals, limit)
        except Exception as e:
            logger.error("get_recent_failed", error=str(e))
            return []
    
    @staticmethod
    def get_history(days: int = 30) -> List[PerformanceHistory]:
        """Retourne l'historique quotidien des performances."""
        history = []
        closed = [s for s in scheduler.signals if s.status == SignalStatus.CLOSED and s.result]
        
        for day_offset in range(days):
            date = datetime.utcnow().date() - timedelta(days=day_offset)
            day_signals = [s for s in closed if s.updated_at.date() == date]
            
            if day_signals:
                wins = len([s for s in day_signals if s.result == SignalResult.WIN])
                losses = len([s for s in day_signals if s.result == SignalResult.LOSS])
                win_rate = (wins / len(day_signals)) * 100 if day_signals else 0
                
                win_pips = sum(s.pips_gained for s in day_signals if s.result == SignalResult.WIN and s.pips_gained)
                loss_pips = sum(abs(s.pips_gained) for s in day_signals if s.result == SignalResult.LOSS and s.pips_gained)
                profit_factor = win_pips / loss_pips if loss_pips > 0 else 0
                
                history.append(PerformanceHistory(
                    date=date.isoformat(),
                    win_rate=round(win_rate, 1),
                    total_signals=len(day_signals),
                    wins=wins,
                    losses=losses,
                    profit_factor=round(profit_factor, 2),
                ))
        
        return sorted(history, key=lambda h: h.date)
    
    @staticmethod
    def get_stats_by_instrument(days: int = 30) -> Dict[str, InstrumentPerformance]:
        """Retourne les performances par instrument."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        closed = [
            s for s in scheduler.signals
            if s.status == SignalStatus.CLOSED and s.result and s.updated_at >= cutoff
        ]
        
        stats = {}
        instruments = set(s.instrument for s in closed)
        
        for inst in instruments:
            inst_signals = [s for s in closed if s.instrument == inst]
            wins = len([s for s in inst_signals if s.result == SignalResult.WIN])
            losses = len([s for s in inst_signals if s.result == SignalResult.LOSS])
            win_rate = (wins / len(inst_signals)) * 100 if inst_signals else 0
            pips = [s.pips_gained for s in inst_signals if s.pips_gained is not None]
            avg_pips = sum(pips) / len(pips) if pips else 0
            
            stats[inst] = InstrumentPerformance(
                instrument=inst,
                win_rate=round(win_rate, 1),
                total_signals=len(inst_signals),
                wins=wins,
                losses=losses,
                average_pips=round(avg_pips, 1),
            )
        
        return stats
    
    @staticmethod
    def get_stats_by_trade_type(days: int = 30) -> Dict[str, TradeTypePerformance]:
        """Retourne les performances par type de trade."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        closed = [
            s for s in scheduler.signals
            if s.status == SignalStatus.CLOSED and s.result and s.updated_at >= cutoff
        ]
        
        stats = {}
        for trade_type in TradeType:
            type_signals = [s for s in closed if s.trade_type == trade_type]
            if type_signals:
                wins = len([s for s in type_signals if s.result == SignalResult.WIN])
                losses = len([s for s in type_signals if s.result == SignalResult.LOSS])
                win_rate = (wins / len(type_signals)) * 100 if type_signals else 0
                
                stats[trade_type.value] = TradeTypePerformance(
                    trade_type=trade_type.value,
                    win_rate=round(win_rate, 1),
                    total_signals=len(type_signals),
                    wins=wins,
                    losses=losses,
                )
        
        return stats
    
    @staticmethod
    def get_summary() -> PerformanceSummary:
        """Retourne un résumé complet des performances."""
        return PerformanceSummary(
            overall=PerformanceService.get_current_stats(),
            by_instrument=PerformanceService.get_stats_by_instrument(30),
            by_trade_type=PerformanceService.get_stats_by_trade_type(30),
            recent_signals=PerformanceService.get_recent(10),
            history=PerformanceService.get_history(30),
        )