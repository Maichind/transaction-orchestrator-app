"""Unit tests — idempotency cache layer."""
import pytest
from __future__ import annotations
from unittest.mock import AsyncMock
from app.infrastructure.cache.idempotency import (
    cache_response,
    get_cached_response,
    delete_cached_response,
)


@pytest.mark.asyncio
async def test_cache_miss_returns_none(fake_redis: AsyncMock) -> None:
    result = await get_cached_response(fake_redis, "nonexistent-key")
    assert result is None


@pytest.mark.asyncio
async def test_cache_set_and_get(fake_redis: AsyncMock) -> None:
    payload = {"id": "abc", "status": "pending", "amount": "100.00"}

    await cache_response(fake_redis, "key-001", payload)
    result = await get_cached_response(fake_redis, "key-001")

    assert result is not None
    assert result["id"] == "abc"
    assert result["status"] == "pending"


@pytest.mark.asyncio
async def test_cache_delete(fake_redis: AsyncMock) -> None:
    await cache_response(fake_redis, "key-del", {"data": "x"})
    await delete_cached_response(fake_redis, "key-del")
    result = await get_cached_response(fake_redis, "key-del")
    assert result is None
