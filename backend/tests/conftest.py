"""
Pytest fixtures for unit and integration tests.

Strategy:
- SQLite in-memory for fast DB tests (no Docker needed for unit tests)
- fakeredis for Redis mocking (no network required)
- Override FastAPI dependencies so tests use isolated infrastructure
"""
import pytest
import pytest_asyncio
from typing import Any
from app.main import create_app
from __future__ import annotations
from unittest.mock import AsyncMock
from collections.abc import AsyncGenerator
from httpx import ASGITransport, AsyncClient
from app.core.dependencies import get_db, get_redis
from app.infrastructure.database.models.base import Base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


# ── Test DB (SQLite in-memory, async) ─────────────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


# ── Fake Redis ─────────────────────────────────────────────────────────────────
@pytest.fixture
def fake_redis() -> AsyncMock:
    """In-memory redis mock backed by a dict."""
    store: dict[str, Any] = {}

    redis = AsyncMock()
    redis.get = AsyncMock(side_effect=lambda k: store.get(k))
    redis.set = AsyncMock(side_effect=lambda k, v, ex=None: store.update({k: v}))
    redis.delete = AsyncMock(side_effect=lambda k: store.pop(k, None))
    redis.ping = AsyncMock(return_value=True)
    return redis


# ── FastAPI test client ────────────────────────────────────────────────────────
@pytest_asyncio.fixture(scope="function")
async def client(test_session: AsyncSession, fake_redis: AsyncMock) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    # Override dependencies with test doubles
    app.dependency_overrides[get_db] = lambda: test_session
    app.dependency_overrides[get_redis] = lambda: fake_redis
 
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
