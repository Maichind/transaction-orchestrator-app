"""
Unit tests — Celery task logic.

We test the task function directly (not via .delay()/worker) using Celery's
`task.apply()` which runs synchronously in-process — no broker needed.
"""
from __future__ import annotations
import uuid
import pytest
from unittest.mock import AsyncMock, patch
from app.workers.tasks.transaction_tasks import process_transaction


@pytest.mark.asyncio
async def test_process_transaction_success_path() -> None:
    """Happy path: transaction moves pending → processed."""
    transaction_id = str(uuid.uuid4())
 
    with (
        patch("app.workers.tasks.transaction_tasks._update_transaction_status", new=AsyncMock()) as mock_update,
        patch("app.workers.tasks.transaction_tasks.time.sleep"),  # skip real sleep
        patch("app.workers.tasks.transaction_tasks.random.random", return_value=0.99),  # force success (>0.2)
    ):
        result = process_transaction.apply(args=[transaction_id]).get()
 
    assert result["status"] == "processed"
    assert result["transaction_id"] == transaction_id
    # Called twice: once to set PENDING, once to set PROCESSED
    assert mock_update.call_count == 2


@pytest.mark.asyncio
async def test_process_transaction_marks_failed_after_max_retries() -> None:
    """When the simulated failure always triggers and retries are exhausted, status = failed."""
    transaction_id = str(uuid.uuid4())
 
    with (
        patch("app.workers.tasks.transaction_tasks._update_transaction_status", new=AsyncMock()) as mock_update,
        patch("app.workers.tasks.transaction_tasks.time.sleep"),
        patch("app.workers.tasks.transaction_tasks.random.random", return_value=0.01),  # force failure (<0.2)
    ):
        # .apply() with throw=False to inspect the task's own retry-exhaustion handling
        # We directly call the task function bypassing Celery's retry decorator
        # by checking the final state after max retries simulated via request.retries
        task = process_transaction
        task.push_request(retries=task.max_retries)  # simulate final attempt
        try:
            result = task.run(transaction_id)
        finally:
            task.pop_request()
 
    assert result["status"] == "failed"
    assert "error" in result
    # PENDING set, then FAILED set
    assert mock_update.call_count == 2
    last_call = mock_update.call_args_list[-1]
    assert last_call.kwargs["new_status"] == "failed"


def test_clean_wikipedia_text_helper_not_in_scope() -> None:
    """Sanity placeholder — ensures this module's imports don't break collection."""
    assert process_transaction.name == "transaction_tasks.process_transaction"
