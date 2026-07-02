"""
TransactionService — application layer orchestrator.

Responsibilities:
- Business rules (idempotency check, validation)
- Coordination between repository, cache, worker, and event publisher
- Never does I/O directly (delegates to infrastructure)
- Never knows about HTTP (no Request/Response imports)
"""
from __future__ import annotations
import uuid
from decimal import Decimal
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.constants import TransactionStatus, TransactionType
from app.core.exceptions import NotFoundError, TaskEnqueueError
from app.core.logger import get_logger
from app.infrastructure.cache.idempotency import (
    cache_response,
    get_cached_response,
)
from app.infrastructure.database.models.transaction import Transaction
from app.infrastructure.events.publisher import (
    publish_transaction_created,
    publish_transaction_status_changed,
)
from app.infrastructure.repositories.transaction_repository import TransactionRepository
from app.schemas.transaction import (
    AsyncProcessResponse,
    TransactionCreate,
    TransactionResponse,
)

logger = get_logger(__name__)


class TransactionService:
    def __init__(self, session: AsyncSession, redis: Redis) -> None:
        self._repo = TransactionRepository(session)
        self._redis = redis


    # ── /transactions/create ──────────────────────────────────────────────────
    async def create(self, payload: TransactionCreate) -> tuple[TransactionResponse, bool]:
        """
        Create a transaction, respecting idempotency.
 
        Returns:
            (TransactionResponse, created: bool)
            created=False means the response came from the idempotency cache.
        """
        idem_key = payload.idempotency_key
 
        # 1. Check idempotency cache FIRST (before any DB touch)
        if idem_key:
            cached = await get_cached_response(self._redis, idem_key)
            if cached:
                logger.info("transaction.idempotent_hit", key=idem_key)
                return TransactionResponse(**cached), False
 
        # 2. Persist new transaction
        transaction = Transaction(
            id=uuid.uuid4(),
            user_id=payload.user_id,
            amount=payload.amount,
            type=payload.type,
            status=TransactionStatus.PENDING,
            idempotency_key=idem_key,
        )
        saved = await self._repo.add(transaction)
        response = TransactionResponse.model_validate(saved)
 
        # 3. Cache the response for future duplicate requests
        if idem_key:
            await cache_response(self._redis, idem_key, response.model_dump())
 
        # 4. Publish WS event so connected clients see the new transaction
        await publish_transaction_created(
            transaction_id=saved.id,
            user_id=saved.user_id,
            amount=str(saved.amount),
            status=saved.status,
        )
 
        logger.info(
            "transaction.created",
            id=str(saved.id),
            user=saved.user_id,
            amount=str(saved.amount),
        )
        return response, True


    # ── /transactions/async-process ───────────────────────────────────────────
    async def enqueue(self, transaction_id: uuid.UUID) -> AsyncProcessResponse:
        """
        Enqueue an existing transaction for async processing via Celery.
        Returns 202 with task_id immediately.
        """
        # Verify transaction exists before enqueuing
        transaction = await self._repo.get(transaction_id)
        if not transaction:
            raise NotFoundError(f"Transaction {transaction_id} not found.")
 
        try:
            # Import here to avoid circular imports at module level
            from app.workers.tasks.transaction_tasks import process_transaction
 
            task = process_transaction.delay(str(transaction_id))
        except Exception as exc:
            logger.error("transaction.enqueue_failed", id=str(transaction_id), error=str(exc))
            raise TaskEnqueueError(str(exc)) from exc
 
        # Update task_id on the transaction record
        await self._repo.update_status(
            transaction_id=transaction_id,
            status=TransactionStatus.PENDING,
            task_id=task.id,
        )
 
        logger.info(
            "transaction.enqueued",
            id=str(transaction_id),
            task_id=task.id,
        )
        return AsyncProcessResponse(
            transaction_id=transaction_id,
            task_id=task.id,
        )


    # ── Queries ───────────────────────────────────────────────────────────────
    async def get(self, transaction_id: uuid.UUID) -> TransactionResponse:
        transaction = await self._repo.get(transaction_id)
        if not transaction:
            raise NotFoundError(f"Transaction {transaction_id} not found.")
        return TransactionResponse.model_validate(transaction)


    async def list_all(
        self, limit: int = 20, offset: int = 0
    ) -> list[TransactionResponse]:
        transactions = await self._repo.list(limit=limit, offset=offset)
        return [TransactionResponse.model_validate(t) for t in transactions]


    async def list_by_user(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> list[TransactionResponse]:
        transactions = await self._repo.list_by_user(user_id, limit, offset)
        return [TransactionResponse.model_validate(t) for t in transactions]


    # ── Internal: called by Celery worker ────────────────────────────────────
    async def update_status(
        self,
        transaction_id: uuid.UUID,
        new_status: TransactionStatus,
        old_status: str,
        error_message: str | None = None,
    ) -> None:
        """Called by the Celery task after processing completes."""
        updated = await self._repo.update_status(
            transaction_id=transaction_id,
            status=new_status,
            error_message=error_message,
        )
        if updated:
            await publish_transaction_status_changed(
                transaction_id=transaction_id,
                user_id=updated.user_id,
                old_status=old_status,
                new_status=new_status,
                error_message=error_message,
            )
