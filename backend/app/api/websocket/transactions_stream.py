"""
WebSocket endpoint: GET /transactions/stream

Lifecycle:
  1. Client connects → registered in ConnectionManager
  2. Server sends confirmation handshake JSON
  3. Server sends periodic pings to detect dead connections
  4. On any transaction state change → EventPublisher broadcasts to all clients
  5. Client disconnects → removed from registry (no leak)

Kept in api/websocket/ (separate from HTTP routes) because WS has a
fundamentally different lifecycle and error model than HTTP.
"""
import asyncio
from __future__ import annotations
from app.core.logger import get_logger
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.infrastructure.ws.connection_manager import ws_manager

router = APIRouter(tags=["WebSocket"])

logger = get_logger(__name__)

PING_INTERVAL_SECONDS = 30


@router.websocket("/transactions/stream")
async def transactions_stream(ws: WebSocket) -> None:
    """
    Real-time transaction event stream.
 
    Connect with: `ws://localhost:8000/transactions/stream`
 
    Events emitted:
    - `transaction.created`      → new transaction saved
    - `transaction.status_changed` → async processing updated status
    - `ping`                     → keepalive (every 30s)
    """
    await ws_manager.connect(ws)
    logger.info("ws.stream_connected", client=str(ws.client))
 
    # Send handshake so client knows it's live
    await ws.send_json({
        "event": "connected",
        "message": "Subscribed to transaction events.",
        "active_connections": ws_manager.active_connections,
    })
 
    try:
        # Main loop: listen for client messages AND keep connection alive
        ping_task = asyncio.create_task(_ping_loop(ws))
 
        try:
            while True:
                # We accept client messages but don't require them
                # (allows future subscription filtering without breaking existing clients)
                data = await ws.receive_text()
                logger.debug("ws.client_message", data=data)
        finally:
            ping_task.cancel()
 
    except WebSocketDisconnect as exc:
        logger.info("ws.stream_disconnected", code=exc.code, client=str(ws.client))
    except Exception as exc:
        logger.error("ws.stream_error", error=str(exc), client=str(ws.client))
    finally:
        await ws_manager.disconnect(ws)


async def _ping_loop(ws: WebSocket) -> None:
    """Send periodic pings to keep the connection alive through proxies/load balancers."""
    while True:
        await asyncio.sleep(PING_INTERVAL_SECONDS)
        try:
            await ws.send_json({"event": "ping"})
        except Exception:
            break  # Connection is dead; outer loop will handle cleanup
