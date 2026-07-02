"""Unit tests — ConnectionManager broadcast logic, isolated with mocked WebSockets."""
from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock
from starlette.websockets import WebSocketState
from app.infrastructure.ws.connection_manager import ConnectionManager


def _make_mock_ws(connected: bool = True) -> MagicMock:
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.client_state = WebSocketState.CONNECTED if connected else WebSocketState.DISCONNECTED
    return ws


@pytest.mark.asyncio
async def test_connect_adds_to_active_connections() -> None:
    manager = ConnectionManager()
    ws = _make_mock_ws()
 
    await manager.connect(ws)
 
    assert manager.active_connections == 1
    ws.accept.assert_awaited_once()


@pytest.mark.asyncio
async def test_disconnect_removes_connection() -> None:
    manager = ConnectionManager()
    ws = _make_mock_ws()
 
    await manager.connect(ws)
    await manager.disconnect(ws)
 
    assert manager.active_connections == 0


@pytest.mark.asyncio
async def test_broadcast_sends_to_all_connected_clients() -> None:
    manager = ConnectionManager()
    ws1, ws2, ws3 = _make_mock_ws(), _make_mock_ws(), _make_mock_ws()
 
    for ws in (ws1, ws2, ws3):
        await manager.connect(ws)
 
    payload = {"event": "test.event", "payload": {"id": "123"}}
    await manager.broadcast(payload)
 
    ws1.send_json.assert_awaited_once_with(payload)
    ws2.send_json.assert_awaited_once_with(payload)
    ws3.send_json.assert_awaited_once_with(payload)


@pytest.mark.asyncio
async def test_broadcast_removes_dead_connections() -> None:
    """If send_json raises (client gone), the connection should be pruned silently."""
    manager = ConnectionManager()
    good_ws = _make_mock_ws()
    dead_ws = _make_mock_ws()
    dead_ws.send_json = AsyncMock(side_effect=RuntimeError("connection closed"))
 
    await manager.connect(good_ws)
    await manager.connect(dead_ws)
    assert manager.active_connections == 2
 
    await manager.broadcast({"event": "test"})
 
    # Dead connection pruned, good one remains
    assert manager.active_connections == 1
    good_ws.send_json.assert_awaited_once()


@pytest.mark.asyncio
async def test_broadcast_with_no_connections_does_not_error() -> None:
    manager = ConnectionManager()
    # Should not raise even with zero active connections
    await manager.broadcast({"event": "no.one.listening"})
    assert manager.active_connections == 0


@pytest.mark.asyncio
async def test_broadcast_skips_disconnected_state_clients() -> None:
    """Clients whose state is DISCONNECTED should be skipped, not sent to."""
    manager = ConnectionManager()
    stale_ws = _make_mock_ws(connected=False)
 
    await manager.connect(stale_ws)
    await manager.broadcast({"event": "test"})
 
    stale_ws.send_json.assert_not_awaited()
