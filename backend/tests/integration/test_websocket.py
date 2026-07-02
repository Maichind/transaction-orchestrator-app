"""
Integration tests — WebSocket transaction stream.

Uses FastAPI's TestClient (sync, built on Starlette's WebSocketTestSession)
for the connection handshake tests, since it handles the WS protocol
upgrade more reliably in tests than raw httpx/AsyncClient.
"""
from __future__ import annotations
 
import pytest
from app.main import create_app
from fastapi.testclient import TestClient
from app.core.dependencies import get_db, get_redis
from app.infrastructure.ws.connection_manager import ws_manager
 
 
@pytest.fixture
def sync_client(test_session, fake_redis):
    """Sync TestClient for WebSocket tests (WS protocol needs sync test client)."""
    app = create_app()
    app.dependency_overrides[get_db] = lambda: test_session
    app.dependency_overrides[get_redis] = lambda: fake_redis
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
 
 
def test_websocket_connects_and_receives_handshake(sync_client: TestClient) -> None:
    """On connect, the server should immediately send a 'connected' event."""
    with sync_client.websocket_connect("/transactions/stream") as ws:
        data = ws.receive_json()
        assert data["event"] == "connected"
        assert "active_connections" in data
        assert data["active_connections"] >= 1
 
 
def test_websocket_disconnect_cleans_up_connection(sync_client: TestClient) -> None:
    """After disconnecting, the connection manager should no longer track the client."""
    initial_count = ws_manager.active_connections
 
    with sync_client.websocket_connect("/transactions/stream") as ws:
        ws.receive_json()  # consume handshake
        assert ws_manager.active_connections == initial_count + 1
 
    # Connection manager cleanup happens async; this confirms no leak after close
    assert ws_manager.active_connections == initial_count
 
 
def test_websocket_multiple_clients_all_receive_handshake(sync_client: TestClient) -> None:
    """Multiple simultaneous clients should each get their own handshake."""
    with sync_client.websocket_connect("/transactions/stream") as ws1:
        data1 = ws1.receive_json()
        assert data1["event"] == "connected"
 
        with sync_client.websocket_connect("/transactions/stream") as ws2:
            data2 = ws2.receive_json()
            assert data2["event"] == "connected"
            # Second client should see at least 2 active connections
            assert data2["active_connections"] >= 2
 
 
@pytest.mark.asyncio
async def test_create_transaction_broadcasts_via_websocket(
    sync_client: TestClient, test_session, fake_redis
) -> None:
    """
    End-to-end: creating a transaction over HTTP should broadcast a
    'transaction.created' event to all connected WebSocket clients.
    """
    with sync_client.websocket_connect("/transactions/stream") as ws:
        ws.receive_json()  # consume handshake
 
        # Create a transaction via the async service directly
        # (sync_client's HTTP calls run in a separate event loop context,
        #  so we drive the service layer directly to keep the test deterministic)
        from app.services.transaction_service import TransactionService
        from app.schemas.transaction import TransactionCreate
        from decimal import Decimal
 
        service = TransactionService(session=test_session, redis=fake_redis)
        await service.create(
            TransactionCreate(
                user_id="ws_test_user",
                amount=Decimal("75.00"),
                type="credit",
            )
        )
        await test_session.commit()
 
        event = ws.receive_json(mode="text")
        assert event["event"] == "transaction.created"
        assert event["payload"]["user_id"] == "ws_test_user"
        assert event["payload"]["amount"] == "75.00"
        assert event["payload"]["status"] == "pending"
 
 
def test_websocket_accepts_client_messages_without_error(sync_client: TestClient) -> None:
    """
    The server should tolerate arbitrary client messages without crashing
    the connection (future-proofs for subscription filtering).
    """
    with sync_client.websocket_connect("/transactions/stream") as ws:
        ws.receive_json()  # handshake
        ws.send_text("ping from client")
        # Connection should remain open — verified by being able to close cleanly
        ws.close()
