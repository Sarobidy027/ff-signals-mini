"""
Rate Limiter - Limitation du nombre de requêtes par IP.
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Tuple
import structlog

from app.core.database import get_db

logger = structlog.get_logger()


class RateLimiter:
    """
    Limiteur de taux par IP.
    100 requêtes par minute par défaut.
    """
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._memory_cache: Dict[str, Tuple[int, datetime]] = {}
        self._lock = asyncio.Lock()
    
    def is_allowed(self, ip: str) -> bool:
        """
        Vérifie si une IP est autorisée à faire une requête.
        Utilise un cache mémoire pour la performance.
        """
        now = datetime.utcnow()
        
        if ip in self._memory_cache:
            count, reset_at = self._memory_cache[ip]
            if now < reset_at:
                if count >= self.max_requests:
                    logger.warning("rate_limit_exceeded_memory", ip=ip, count=count)
                    return False
                self._memory_cache[ip] = (count + 1, reset_at)
                return True
            else:
                self._memory_cache[ip] = (1, now + timedelta(seconds=self.window_seconds))
                return True
        else:
            self._memory_cache[ip] = (1, now + timedelta(seconds=self.window_seconds))
            
            if len(self._memory_cache) > 10000:
                self._cleanup_memory_cache(now)
            
            return True
    
    async def is_allowed_db(self, ip: str) -> bool:
        """
        Vérifie avec persistance dans la base de données.
        """
        now = datetime.utcnow()
        reset_at = now + timedelta(seconds=self.window_seconds)
        
        try:
            db = await get_db()
            
            async with db.execute(
                "SELECT count, reset_at FROM rate_limits WHERE ip = ?",
                (ip,)
            ) as cursor:
                row = await cursor.fetchone()
            
            if row:
                count, reset_at_str = row
                reset_at_db = datetime.fromisoformat(reset_at_str)
                
                if now < reset_at_db:
                    if count >= self.max_requests:
                        logger.warning("rate_limit_exceeded_db", ip=ip, count=count)
                        return False
                    
                    await db.execute(
                        "UPDATE rate_limits SET count = count + 1 WHERE ip = ?",
                        (ip,)
                    )
                else:
                    await db.execute(
                        "UPDATE rate_limits SET count = 1, reset_at = ? WHERE ip = ?",
                        (reset_at.isoformat(), ip)
                    )
            else:
                await db.execute(
                    "INSERT INTO rate_limits (ip, count, reset_at) VALUES (?, 1, ?)",
                    (ip, reset_at.isoformat())
                )
            
            await db.commit()
            return True
            
        except Exception as e:
            logger.error("rate_limit_db_error", error=str(e))
            return self.is_allowed(ip)
    
    def _cleanup_memory_cache(self, now: datetime) -> None:
        """Nettoie les entrées expirées du cache mémoire."""
        expired = [
            ip for ip, (_, reset_at) in self._memory_cache.items()
            if now >= reset_at
        ]
        for ip in expired:
            del self._memory_cache[ip]
    
    def remaining(self, ip: str) -> int:
        """Retourne le nombre de requêtes restantes pour une IP."""
        if ip in self._memory_cache:
            count, reset_at = self._memory_cache[ip]
            if datetime.utcnow() < reset_at:
                return max(0, self.max_requests - count)
        return self.max_requests
    
    def reset(self, ip: str) -> None:
        """Réinitialise le compteur pour une IP."""
        if ip in self._memory_cache:
            del self._memory_cache[ip]