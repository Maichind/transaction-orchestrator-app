"""
Event publisher — infrastructure concern.
 
Why infrastructure and not services?
Publishing to a WebSocket is a side-effect of infrastructure (network I/O).
The service layer fires domain events via this publisher without knowing
HOW they are delivered (WS today, Kafka tomorrow — same interface).
 
Pattern: thin async functions, no state, injected manager for testability.
"""
from uuid import UUID
from typing import Any
from __future__ import annotations
from app.core.logger import get_logger
from datetime import datetime, timezone
from app.infrastructure.ws.connection_manager import ws_manager

logger = get_logger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def publish_transaction_created(
    transaction_id: UUID,
    user_id: str,
    amount: str,
    status: str,
) -> None:
    event: dict[str, Any] = {
        "event": "transaction.created",
        "timestamp": _now_iso(),
        "payload": {
            "id": str(transaction_id),
            "user_id": user_id,
            "amount": amount,
            "status": status,
        },
    }
    logger.info("event.publish", event_type="transaction.created", id=str(transaction_id))
    await ws_manager.broadcast(event)


async def publish_transaction_status_changed(
    transaction_id: UUID,
    user_id: str,
    old_status: str,
    new_status: str,
    task_id: str | None = None,
    error_message: str | None = None,
) -> None:
    event: dict[str, Any] = {
        "event": "transaction.status_changed",
        "timestamp": _now_iso(),
        "payload": {
            "id": str(transaction_id),
            "user_id": user_id,
            "old_status": old_status,
            "new_status": new_status,
            "task_id": task_id,
            "error_message": error_message,
        },
    }
    logger.info(
        "event.publish",
        event_type="transaction.status_changed",
        id=str(transaction_id),
        old=old_status,
        new=new_status,
    )
    await ws_manager.broadcast(event)
