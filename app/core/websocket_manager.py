"""
Gestionnaire WebSocket.
"""
from typing import Set, Any, Dict, List
from fastapi import WebSocket
import asyncio
from datetime import datetime
import structlog

logger = structlog.get_logger()


class ConnectionManager:
    """Gère les connexions WebSocket actives."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, metadata: Dict[str, Any] = None) -> None:
        """Accepte une nouvelle connexion."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.add(websocket)
            self._connection_metadata[websocket] = metadata or {}
            self._connection_metadata[websocket]["connected_at"] = datetime.utcnow()
        logger.info("websocket_connected", total=self.connection_count)
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """Retire une connexion."""
        async with self._lock:
            self.active_connections.discard(websocket)
            self._connection_metadata.pop(websocket, None)
        logger.info("websocket_disconnected", total=self.connection_count)
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket) -> bool:
        """Envoie un message à une connexion spécifique."""
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.error("websocket_send_failed", error=str(e))
            await self.disconnect(websocket)
            return False
    
    async def broadcast(self, message: Dict[str, Any]) -> int:
        """Diffuse un message à toutes les connexions."""
        async with self._lock:
            connections = list(self.active_connections)
        
        success_count = 0
        for connection in connections:
            if await self.send_personal_message(message, connection):
                success_count += 1
        
        return success_count
    
    async def broadcast_event(self, event_type: str, payload: Any) -> int:
        """Diffuse un événement typé."""
        return await self.broadcast({
            "type": event_type,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    @property
    def connection_count(self) -> int:
        """Nombre de connexions actives."""
        return len(self.active_connections)
    
    def get_metadata(self, websocket: WebSocket) -> Dict[str, Any]:
        """Récupère les métadonnées d'une connexion."""
        return self._connection_metadata.get(websocket, {})
    
    async def broadcast_to_filtered(self, message: Dict[str, Any], filter_func) -> int:
        """Diffuse à une sélection de connexions."""
        async with self._lock:
            connections = [ws for ws in self.active_connections if filter_func(self._connection_metadata.get(ws, {}))]
        
        success_count = 0
        for connection in connections:
            if await self.send_personal_message(message, connection):
                success_count += 1
        
        return success_count


manager = ConnectionManager()