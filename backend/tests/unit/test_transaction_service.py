"""Unit tests — TransactionService business logic."""
import uuid
import pytest
from decimal import Decimal
from __future__ import annotations
from app.core.exceptions import NotFoundError
from unittest.mock import AsyncMock, MagicMock, patch
from app.schemas.transaction import TransactionCreate
from app.core.constants import TransactionStatus, TransactionType


@pytest.mark.asyncio
async def test_create_transaction_returns_response(test_session, fake_redis) -> None:
    from app.services.transaction_service import TransactionService

    with patch("app.infrastructure.events.publisher.ws_manager") as mock_ws:
        mock_ws.broadcast = AsyncMock()
        service = TransactionService(session=test_session, redis=fake_redis)
        payload = TransactionCreate(
            user_id="user_test",
            amount=Decimal("250.00"),
            type=TransactionType.CREDIT,
        )
        response, created = await service.create(payload)

    assert created is True
    assert response.user_id == "user_test"
    assert response.amount == Decimal("250.00")
    assert response.status == TransactionStatus.PENDING


@pytest.mark.asyncio
async def test_create_idempotent_returns_cached(test_session, fake_redis) -> None:
    from app.services.transaction_service import TransactionService

    with patch("app.infrastructure.events.publisher.ws_manager") as mock_ws:
        mock_ws.broadcast = AsyncMock()
        service = TransactionService(session=test_session, redis=fake_redis)
        payload = TransactionCreate(
            user_id="user_idem",
            amount=Decimal("50.00"),
            type=TransactionType.DEBIT,
            idempotency_key="idem-key-001",
        )
        first_response, first_created = await service.create(payload)
        second_response, second_created = await service.create(payload)

    assert first_created is True
    assert second_created is False
    assert first_response.id == second_response.id


@pytest.mark.asyncio
async def test_get_nonexistent_raises_not_found(test_session, fake_redis) -> None:
    from app.services.transaction_service import TransactionService
 
    service = TransactionService(session=test_session, redis=fake_redis)
    with pytest.raises(NotFoundError):
        await service.get(uuid.uuid4())


@pytest.mark.asyncio
async def test_list_all_returns_paginated(test_session, fake_redis) -> None:
    from app.services.transaction_service import TransactionService

    with patch("app.infrastructure.events.publisher.ws_manager") as mock_ws:
        mock_ws.broadcast = AsyncMock()
        service = TransactionService(session=test_session, redis=fake_redis)

        for i in range(5):
            await service.create(TransactionCreate(
                user_id="user_list",
                amount=Decimal(f"{(i+1)*10}.00"),
                type=TransactionType.CREDIT,
            ))
        await test_session.commit()

        results = await service.list_all(limit=3, offset=0)

    assert len(results) == 3
