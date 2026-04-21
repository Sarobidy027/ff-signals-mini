"""
Service de cache avec TTL.
"""
from typing import Any, Optional, Dict, Tuple
from datetime import datetime, timedelta
import asyncio
import structlog

logger = structlog.get_logger()


class CacheService:
    """Cache mémoire avec TTL."""
    
    _cache: Dict[str, Tuple[Any, datetime]] = {}
    _lock = asyncio.Lock()
    _cleanup_task: asyncio.Task = None
    
    @classmethod
    async def start_cleanup(cls, interval_seconds: int = 60):
        """Démarre le nettoyage périodique du cache."""
        async def _cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(interval_seconds)
                    await cls.cleanup()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error("cache_cleanup_failed", error=str(e))
        
        cls._cleanup_task = asyncio.create_task(_cleanup_loop())
    
    @classmethod
    async def stop_cleanup(cls):
        """Arrête le nettoyage périodique."""
        if cls._cleanup_task:
            cls._cleanup_task.cancel()
            try:
                await cls._cleanup_task
            except asyncio.CancelledError:
                pass
    
    @classmethod
    async def cleanup(cls):
        """Nettoie les entrées expirées du cache."""
        now = datetime.utcnow()
        async with cls._lock:
            expired = [k for k, (_, exp) in cls._cache.items() if now >= exp]
            for key in expired:
                del cls._cache[key]
        
        if expired:
            logger.debug("cache_cleanup", removed=len(expired), remaining=len(cls._cache))
    
    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """Récupère une valeur du cache si elle n'a pas expiré."""
        if key in cls._cache:
            value, expires_at = cls._cache[key]
            if datetime.utcnow() < expires_at:
                return value
            else:
                del cls._cache[key]
        return None
    
    @classmethod
    def set(cls, key: str, value: Any, ttl: int = 60) -> None:
        """Ajoute une valeur au cache avec TTL en secondes."""
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        cls._cache[key] = (value, expires_at)
    
    @classmethod
    def delete(cls, key: str) -> bool:
        """Supprime une entrée du cache."""
        if key in cls._cache:
            del cls._cache[key]
            return True
        return False
    
    @classmethod
    def invalidate_pattern(cls, pattern: str) -> int:
        """Invalide toutes les clés contenant le pattern."""
        keys_to_delete = [k for k in cls._cache if pattern in k]
        for key in keys_to_delete:
            del cls._cache[key]
        return len(keys_to_delete)
    
    @classmethod
    def clear(cls) -> None:
        """Vide complètement le cache."""
        cls._cache.clear()
        logger.info("cache_cleared")
    
    @classmethod
    def size(cls) -> int:
        """Retourne la taille du cache."""
        return len(cls._cache)
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Retourne les statistiques du cache."""
        now = datetime.utcnow()
        active = sum(1 for _, (_, exp) in cls._cache.items() if now < exp)
        expired = len(cls._cache) - active
        
        return {
            "total_entries": len(cls._cache),
            "active_entries": active,
            "expired_entries": expired,
        }