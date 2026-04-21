"""
Gestion de la base de données SQLite.
"""
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

import aiosqlite
import structlog

from app.core.config import settings

logger = structlog.get_logger()

_db: Optional[aiosqlite.Connection] = None
_db_lock = asyncio.Lock()


async def init_database() -> None:
    """Initialise la base de données."""
    global _db
    
    async with _db_lock:
        if _db is not None:
            return
        
        _db = await aiosqlite.connect(settings.DATABASE_URL)
        _db.row_factory = aiosqlite.Row
        
        await _db.executescript("""
            CREATE TABLE IF NOT EXISTS signals (
                id TEXT PRIMARY KEY,
                instrument TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                stop_loss REAL NOT NULL,
                take_profit REAL NOT NULL,
                confidence REAL NOT NULL,
                trade_type TEXT NOT NULL,
                estimated_duration TEXT,
                entry_time TEXT NOT NULL,
                exit_time TEXT,
                status TEXT NOT NULL,
                result TEXT,
                pips_gained REAL,
                risk_reward_ratio REAL NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                raw_data TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status);
            CREATE INDEX IF NOT EXISTS idx_signals_instrument ON signals(instrument);
            CREATE INDEX IF NOT EXISTS idx_signals_created_at ON signals(created_at);
            
            CREATE TABLE IF NOT EXISTS performance_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                win_rate REAL NOT NULL,
                total_signals INTEGER NOT NULL,
                wins INTEGER NOT NULL,
                losses INTEGER NOT NULL,
                profit_factor REAL NOT NULL,
                raw_stats TEXT
            );
            
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS rate_limits (
                ip TEXT PRIMARY KEY,
                count INTEGER NOT NULL,
                reset_at TEXT NOT NULL
            );
        """)
        
        await _db.commit()
        logger.info("database_initialized", path=settings.DATABASE_URL)


async def close_database() -> None:
    """Ferme la connexion à la base de données."""
    global _db
    
    async with _db_lock:
        if _db is not None:
            await _db.close()
            _db = None
            logger.info("database_closed")


async def get_db() -> aiosqlite.Connection:
    """Retourne la connexion à la base de données."""
    global _db
    
    if _db is None:
        await init_database()
    
    return _db


async def get_db_health() -> bool:
    """Vérifie la santé de la base de données."""
    try:
        db = await get_db()
        await db.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return False


async def save_signals(signals: List[Dict[str, Any]]) -> None:
    """Sauvegarde les signaux dans la base de données."""
    db = await get_db()
    
    async with _db_lock:
        await db.execute("DELETE FROM signals WHERE status != 'CLOSED'")
        
        for signal in signals:
            await db.execute("""
                INSERT OR REPLACE INTO signals 
                (id, instrument, direction, entry_price, stop_loss, take_profit,
                 confidence, trade_type, estimated_duration, entry_time, exit_time,
                 status, result, pips_gained, risk_reward_ratio, created_at, updated_at, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal.get("id"),
                signal.get("instrument"),
                signal.get("direction"),
                signal.get("entry_price"),
                signal.get("stop_loss"),
                signal.get("take_profit"),
                signal.get("confidence"),
                signal.get("trade_type"),
                signal.get("estimated_duration"),
                signal.get("entry_time"),
                signal.get("exit_time"),
                signal.get("status"),
                signal.get("result"),
                signal.get("pips_gained"),
                signal.get("risk_reward_ratio"),
                signal.get("created_at"),
                signal.get("updated_at"),
                json.dumps(signal),
            ))
        
        await db.commit()


async def load_signals() -> List[Dict[str, Any]]:
    """Charge les signaux depuis la base de données."""
    db = await get_db()
    
    async with db.execute("""
        SELECT * FROM signals 
        WHERE status != 'CLOSED' OR updated_at > datetime('now', '-1 day')
        ORDER BY created_at DESC
    """) as cursor:
        rows = await cursor.fetchall()
    
    signals = []
    for row in rows:
        signal = dict(row)
        if signal.get("raw_data"):
            try:
                signals.append(json.loads(signal["raw_data"]))
            except json.JSONDecodeError:
                signals.append(signal)
        else:
            signals.append(signal)
    
    return signals


async def save_app_state(key: str, value: str) -> None:
    """Sauvegarde un état de l'application."""
    db = await get_db()
    
    await db.execute("""
        INSERT OR REPLACE INTO app_state (key, value, updated_at)
        VALUES (?, ?, ?)
    """, (key, value, datetime.utcnow().isoformat()))
    
    await db.commit()


async def load_app_state(key: str) -> Optional[str]:
    """Charge un état de l'application."""
    db = await get_db()
    
    async with db.execute(
        "SELECT value FROM app_state WHERE key = ?", (key,)
    ) as cursor:
        row = await cursor.fetchone()
    
    return row[0] if row else None