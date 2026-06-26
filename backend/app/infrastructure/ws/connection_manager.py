"""
WebSocket connection manager.
 
Responsibilities:
- Track all active WS connections in memory
- Broadcast JSON events to all connected clients
- Silently drop stale connections without crashing the broadcast loop
 
Design note: This is an in-process registry. In a multi-replica deployment,
replace with Redis Pub/Sub as the broadcast bus (each process subscribes and
forwards to its local connections). The interface stays identical.
"""
import asyncio
from typing import Any
from fastapi import WebSocket
from __future__ import annotations
from app.core.logger import get_logger
from starlette.websockets import WebSocketState
 
logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()


    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._connections.add(ws)
        logger.info("ws.connected", total=len(self._connections))


    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(ws)
        logger.info("ws.disconnected", total=len(self._connections))


    async def broadcast(self, data: dict[str, Any]) -> None:
        """
        Send a JSON message to every connected client.
        Connections that fail to receive are removed gracefully.
        """
        if not self._connections:
            return
 
        dead: list[WebSocket] = []
 
        async with self._lock:
            targets = list(self._connections)
 
        for ws in targets:
            try:
                if ws.client_state == WebSocketState.CONNECTED:
                    await ws.send_json(data)
            except Exception as exc:
                logger.warning("ws.send_failed", error=str(exc))
                dead.append(ws)
 
        if dead:
            async with self._lock:
                for ws in dead:
                    self._connections.discard(ws)
            logger.info("ws.stale_removed", count=len(dead))


    @property
    def active_connections(self) -> int:
        return len(self._connections)


# Module-level singleton — imported by routes and event publisher
ws_manager = ConnectionManager()
