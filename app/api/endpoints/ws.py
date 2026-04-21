"""
Endpoint WebSocket.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from fastapi.exceptions import HTTPException
import asyncio
import json
import structlog

from app.core.websocket_manager import manager
from app.core.security import decode_token
from app.services.signal_service import SignalService
from app.services.performance_service import PerformanceService

logger = structlog.get_logger()
router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/dashboard")
async def dashboard_websocket(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket pour les mises à jour temps réel du dashboard.
    
    Événements émis :
    - active_signal : Signal actif mis à jour
    - signal_activated : Nouveau signal activé
    - signal_closed : Signal clôturé
    - performance_update : Statistiques mises à jour
    - signals_updated : Liste des signaux rafraîchie
    - status_update : Statut global
    """
    payload = decode_token(token)
    if not payload:
        logger.warning("websocket_auth_failed")
        await websocket.close(code=1008, reason="Token invalide")
        return
    
    client_ip = websocket.client.host if websocket.client else "unknown"
    await manager.connect(websocket, {"ip": client_ip})
    logger.info("websocket_connected", ip=client_ip)
    
    try:
        active = SignalService.get_active_signal()
        if active:
            await manager.send_personal_message({
                "type": "active_signal",
                "payload": active.model_dump() if hasattr(active, 'model_dump') else active,
            }, websocket)
        
        stats = PerformanceService.get_current_stats()
        await manager.send_personal_message({
            "type": "performance_update",
            "payload": stats.model_dump() if hasattr(stats, 'model_dump') else stats,
        }, websocket)
        
        signals_response = SignalService.get_signals_list(limit=50)
        await manager.send_personal_message({
            "type": "signals_list",
            "payload": {
                "active": [s.model_dump() if hasattr(s, 'model_dump') else s for s in signals_response.active],
                "pending": [s.model_dump() if hasattr(s, 'model_dump') else s for s in signals_response.pending],
                "total": signals_response.total,
            },
        }, websocket)
        
        ping_count = 0
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                
                if data == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()}))
                elif data.startswith("subscribe:"):
                    subscription = data.split(":", 1)[1]
                    metadata = manager.get_metadata(websocket)
                    metadata["subscriptions"] = metadata.get("subscriptions", []) + [subscription]
                    await websocket.send_text(json.dumps({"type": "subscribed", "topic": subscription}))
                    
            except asyncio.TimeoutError:
                ping_count += 1
                if ping_count % 4 == 0:
                    await websocket.send_text(json.dumps({"type": "keepalive"}))
                
    except WebSocketDisconnect:
        logger.info("websocket_disconnected", ip=client_ip)
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error("websocket_error", error=str(e), ip=client_ip)
        await manager.disconnect(websocket)


@router.websocket("/signals")
async def signals_websocket(
    websocket: WebSocket,
    token: str = Query(...),
    instrument: str = Query(None),
):
    """
    WebSocket pour les mises à jour des signaux d'un instrument spécifique.
    """
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Token invalide")
        return
    
    await manager.connect(websocket, {"ip": websocket.client.host, "instrument": instrument})
    
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                pass
    except WebSocketDisconnect:
        await manager.disconnect(websocket)