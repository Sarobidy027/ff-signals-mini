"""Planificateur de signaux avec persistance - Version finale."""
import asyncio
from typing import List, Optional
from datetime import datetime, timedelta
import random
import structlog

from app.models.signal import Signal, SignalStatus, SignalResult, TradeType
from app.data.instruments import calculate_pips, get_current_price
from app.engine.signal_generator import SignalGenerator
from app.core.websocket_manager import manager
from app.services.persistence_service import PersistenceService
from app.services.cache_service import CacheService
from app.core.config import settings

logger = structlog.get_logger()


class SignalScheduler:
    """Planificateur de signaux avec persistance et cache."""
    
    def __init__(self):
        self.generator = SignalGenerator()
        self.signals: List[Signal] = []
        self.running = False
        self._update_task: Optional[asyncio.Task] = None
        self._gen_task: Optional[asyncio.Task] = None
        self._broadcast_task: Optional[asyncio.Task] = None
        self._persist_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Démarre le planificateur."""
        self.running = True
        
        await self._regenerate()
        
        self._update_task = asyncio.create_task(self._update_loop())
        self._gen_task = asyncio.create_task(self._gen_loop())
        self._broadcast_task = asyncio.create_task(self._broadcast_loop())
        self._persist_task = asyncio.create_task(self._persist_loop())
        
        logger.info("scheduler_started", target_daily=settings.TARGET_DAILY_SIGNALS)
    
    async def stop(self):
        """Arrête le planificateur."""
        self.running = False
        
        for task in [self._update_task, self._gen_task, self._broadcast_task, self._persist_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        await PersistenceService.save_state()
        logger.info("scheduler_stopped")
    
    async def _regenerate(self):
        """Régénère tous les signaux."""
        logger.info("regenerating_signals")
        self.signals = await self.generator.generate(per_instrument=6)
        CacheService.invalidate_pattern("signals")
        await manager.broadcast_event("signals_updated", {"total": len(self.signals)})
    
    async def _update_loop(self):
        """Boucle de mise à jour du statut des signaux."""
        while self.running:
            try:
                await self._update_signals()
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("update_loop_error", error=str(e))
                await asyncio.sleep(5)
    
    async def _gen_loop(self):
        """Boucle de régénération périodique."""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Toutes les heures
                await self._regenerate()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("gen_loop_error", error=str(e))
                await asyncio.sleep(60)
    
    async def _broadcast_loop(self):
        """Boucle de diffusion des mises à jour."""
        while self.running:
            try:
                await self._broadcast_status()
                await self._broadcast_perf()
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("broadcast_loop_error", error=str(e))
                await asyncio.sleep(5)
    
    async def _persist_loop(self):
        """Boucle de persistance périodique."""
        while self.running:
            try:
                await asyncio.sleep(30)
                await PersistenceService.save_state()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("persist_loop_error", error=str(e))
    
    async def _update_signals(self):
        """Met à jour le statut des signaux."""
        now = datetime.utcnow()
        updated = False
        
        for s in self.signals:
            if s.status == SignalStatus.CLOSED:
                continue
            
            if s.status == SignalStatus.PENDING and s.entry_time <= now:
                s.status = SignalStatus.ACTIVE
                s.updated_at = now
                updated = True
                await manager.broadcast_event("signal_activated", {
                    "id": s.id, "instrument": s.instrument, "direction": s.direction.value
                })
            
            if s.status == SignalStatus.ACTIVE:
                max_dur = self._max_duration(s.trade_type)
                if now - s.entry_time > max_dur:
                    await self._close_signal(s, now)
                    updated = True
        
        if updated:
            cutoff = now - timedelta(hours=24)
            self.signals = [s for s in self.signals 
                           if s.status != SignalStatus.CLOSED or s.updated_at > cutoff]
            CacheService.invalidate_pattern("signals")
    
    async def _close_signal(self, s: Signal, exit_time: datetime):
        """Clôture un signal."""
        try:
            price = await get_current_price(s.instrument)
            if price <= 0:
                price = s.take_profit if random.random() > 0.5 else s.stop_loss
            
            if s.direction.value == "BUY":
                pips = calculate_pips(s.entry_price, price, s.instrument)
                is_win = price >= s.entry_price
            else:
                pips = calculate_pips(price, s.entry_price, s.instrument)
                is_win = price <= s.entry_price
            
            s.status = SignalStatus.CLOSED
            s.result = SignalResult.WIN if is_win else SignalResult.LOSS
            s.exit_time = exit_time
            s.pips_gained = round(pips, 1)
            s.updated_at = exit_time
            
            await manager.broadcast_event("signal_closed", {
                "id": s.id, "instrument": s.instrument,
                "result": s.result.value, "pips": s.pips_gained,
            })
            
            logger.info("signal_closed", id=s.id, instrument=s.instrument,
                       result=s.result.value, pips=s.pips_gained)
            
        except Exception as e:
            logger.error("close_signal_error", id=s.id, error=str(e))
    
    def _max_duration(self, tt: TradeType) -> timedelta:
        return {
            TradeType.SCALP: timedelta(minutes=30), 
            TradeType.DAY: timedelta(hours=8),
            TradeType.SWING: timedelta(days=3)
        }.get(tt, timedelta(hours=4))
    
    async def _broadcast_status(self):
        """Diffuse le statut actuel."""
        active = len(self.get_active())
        pending = len(self.get_pending())
        await manager.broadcast_event("status_update", {
            "active_signals": active, "pending_signals": pending,
            "total_signals": len(self.signals), 
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    async def _broadcast_perf(self):
        """Diffuse les statistiques de performance."""
        from app.services.performance_service import PerformanceService
        stats = PerformanceService.calculate_stats(self.signals)
        await manager.broadcast_event("performance_update", 
                                      stats.model_dump() if hasattr(stats, 'model_dump') else stats)
    
    def get_active(self) -> List[Signal]:
        return [s for s in self.signals if s.status == SignalStatus.ACTIVE]
    
    def get_pending(self) -> List[Signal]:
        return [s for s in self.signals if s.status == SignalStatus.PENDING]
    
    def get_by_id(self, sid: str) -> Optional[Signal]:
        for s in self.signals:
            if s.id == sid:
                return s
        return None
    
    def get_connection_count(self) -> int:
        return manager.connection_count


scheduler = SignalScheduler()