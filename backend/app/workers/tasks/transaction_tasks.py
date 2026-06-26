"""
Celery task: process_transaction
 
Flow:
  1. Update status → PENDING (already set on enqueue, idempotent)
  2. Simulate processing (sleep)
  3. Randomly fail 20% of the time to exercise retry/failed path
  4. Update status → PROCESSED or FAILED
  5. Publish WS event via event publisher
 
Important: Celery tasks are sync by nature. We use asyncio.run() to bridge
into the async service/repo layer. In high-throughput systems, consider
gevent/eventlet workers or a separate async task runner (e.g. arq).
"""
import uuid
import time
import random
import asyncio
from celery import Task
from __future__ import annotations
from celery.utils.log import get_task_logger
from app.core.constants import (
    TASK_MAX_RETRIES,
    TASK_PROCESSING_SLEEP,
    TASK_RETRY_BACKOFF,
    TransactionStatus,
)
from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


async def _update_transaction_status(
    transaction_id: uuid.UUID,
    new_status: TransactionStatus,
    old_status: str,
    error_message: str | None = None,
) -> None:
    """
    Bridge into the async service layer from a synchronous Celery task.
    Creates its own DB session since we're outside the request lifecycle.
    """
    from app.infrastructure.database.session import async_session_factory
    from app.infrastructure.cache.redis_client import get_redis_connection
    from app.services.transaction_service import TransactionService
 
    async with async_session_factory() as session:
        redis = await get_redis_connection()
        service = TransactionService(session=session, redis=redis)
        await service.update_status(
            transaction_id=transaction_id,
            new_status=new_status,
            old_status=old_status,
            error_message=error_message,
        )
        await session.commit()


@celery_app.task(
    bind=True,
    name="transaction_tasks.process_transaction",
    max_retries=TASK_MAX_RETRIES,
    default_retry_delay=TASK_RETRY_BACKOFF,
    autoretry_for=(Exception,),
    retry_backoff=True,         # exponential: 2s, 4s, 8s
    retry_backoff_max=60,       # cap at 60s
    retry_jitter=True,          # add randomness to avoid thundering herd
    acks_late=True,
)
def process_transaction(self: Task, transaction_id_str: str) -> dict:
    """
    Main Celery task: simulates processing a financial transaction.
 
    Returns a dict with final status (stored in Celery result backend).
    """
    transaction_id = uuid.UUID(transaction_id_str)
    task_id = self.request.id
    attempt = self.request.retries + 1
 
    logger.info(
        f"[Task {task_id}] Processing transaction {transaction_id_str} "
        f"(attempt {attempt}/{TASK_MAX_RETRIES + 1})"
    )
 
    try:
        # ── Step 1: Mark as pending ────────────────────────────────────────────
        asyncio.run(
            _update_transaction_status(
                transaction_id=transaction_id,
                new_status=TransactionStatus.PENDING,
                old_status=TransactionStatus.PENDING,
            )
        )
 
        # ── Step 2: Simulate processing work ──────────────────────────────────
        logger.info(f"[Task {task_id}] Simulating work ({TASK_PROCESSING_SLEEP}s)...")
        time.sleep(TASK_PROCESSING_SLEEP)
 
        # ── Step 3: Simulate 20% failure rate (exercises retry path) ──────────
        if random.random() < 0.2:
            raise RuntimeError("Simulated processing failure (20% error rate)")
 
        # ── Step 4: Mark as processed ─────────────────────────────────────────
        asyncio.run(
            _update_transaction_status(
                transaction_id=transaction_id,
                new_status=TransactionStatus.PROCESSED,
                old_status=TransactionStatus.PENDING,
            )
        )
 
        logger.info(f"[Task {task_id}] Transaction {transaction_id_str} PROCESSED ✓")
        return {"status": "processed", "transaction_id": transaction_id_str}
 
    except Exception as exc:
        is_final_attempt = self.request.retries >= TASK_MAX_RETRIES
 
        if is_final_attempt:
            # Exhausted all retries → mark as failed permanently
            logger.error(
                f"[Task {task_id}] Transaction {transaction_id_str} FAILED after "
                f"{TASK_MAX_RETRIES + 1} attempts: {exc}"
            )
            asyncio.run(
                _update_transaction_status(
                    transaction_id=transaction_id,
                    new_status=TransactionStatus.FAILED,
                    old_status=TransactionStatus.PENDING,
                    error_message=str(exc),
                )
            )
            return {"status": "failed", "transaction_id": transaction_id_str, "error": str(exc)}
 
        # Retry with exponential backoff (handled by autoretry_for + retry_backoff)
        logger.warning(
            f"[Task {task_id}] Attempt {attempt} failed, retrying... Error: {exc}"
        )
        raise
