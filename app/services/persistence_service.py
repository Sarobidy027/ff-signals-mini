"""
Service de persistance pour la reprise après crash.
"""
import asyncio
from typing import List, Dict, Any
from datetime import datetime
import json
import structlog

from app.core.database import save_signals, load_signals, save_app_state, load_app_state
from app.models.signal import Signal
from app.engine import scheduler

logger = structlog.get_logger()


class PersistenceService:
    """Service de sauvegarde et restauration de l'état."""
    
    _save_task: asyncio.Task = None
    _running = False
    
    @classmethod
    async def start_auto_save(cls, interval_seconds: int = 30):
        """Démarre la sauvegarde automatique périodique."""
        if cls._running:
            return
        
        cls._running = True
        
        async def _save_loop():
            while cls._running:
                try:
                    await asyncio.sleep(interval_seconds)
                    await cls.save_state()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("auto_save_failed", error=str(e))
        
        cls._save_task = asyncio.create_task(_save_loop())
        logger.info("auto_save_started", interval=interval_seconds)
    
    @classmethod
    async def stop_auto_save(cls):
        """Arrête la sauvegarde automatique."""
        cls._running = False
        if cls._save_task:
            cls._save_task.cancel()
            try:
                await cls._save_task
            except asyncio.CancelledError:
                pass
        logger.info("auto_save_stopped")
    
    @classmethod
    async def save_state(cls) -> bool:
        """Sauvegarde l'état complet de l'application."""
        try:
            signals_data = []
            for signal in scheduler.signals:
                signal_dict = signal.model_dump() if hasattr(signal, 'model_dump') else signal
                signals_data.append(signal_dict)
            
            await save_signals(signals_data)
            
            state = {
                "last_save": datetime.utcnow().isoformat(),
                "signal_count": len(signals_data),
                "active_count": len(scheduler.get_active()),
                "pending_count": len(scheduler.get_pending()),
            }
            await save_app_state("last_state", json.dumps(state))
            
            logger.debug("state_saved", signal_count=len(signals_data))
            return True
            
        except Exception as e:
            logger.error("save_state_failed", error=str(e))
            return False
    
    @classmethod
    async def restore_state(cls) -> bool:
        """Restaure l'état depuis la base de données."""
        try:
            signals_data = await load_signals()
            
            restored_signals = []
            for data in signals_data:
                try:
                    signal = Signal(**data)
                    restored_signals.append(signal)
                except Exception as e:
                    logger.warning("signal_restore_failed", error=str(e))
            
            scheduler.signals = restored_signals
            
            state_str = await load_app_state("last_state")
            if state_str:
                state = json.loads(state_str)
                logger.info(
                    "state_restored",
                    last_save=state.get("last_save"),
                    signal_count=len(restored_signals),
                )
            
            return True
            
        except Exception as e:
            logger.error("restore_state_failed", error=str(e))
            return False
    
    @classmethod
    async def create_backup(cls) -> str:
        """Crée une sauvegarde complète."""
        import shutil
        from pathlib import Path
        
        backup_path = Path("data") / f"ff_signals_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.db"
        source_path = Path("data") / "ff_signals.db"
        
        if source_path.exists():
            shutil.copy(source_path, backup_path)
            logger.info("backup_created", path=str(backup_path))
            return str(backup_path)
        
        return ""