"""
FastAPI dependency injection providers.
 
All `Depends(...)` callables live here. This prevents the same session/redis
factory from being duplicated across route files, and makes swapping
implementations in tests trivial (just override the dependency).
"""
from fastapi import Depends
from typing import Annotated
from __future__ import annotations
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings, Settings
from app.infrastructure.database.session import async_session_factory
from app.infrastructure.cache.redis_client import get_redis_connection


# ── Settings ───────────────────────────────────────────────────────────────────
def get_app_settings() -> Settings:
    return get_settings()

SettingsDep = Annotated[Settings, Depends(get_app_settings)]


# ── Database session ───────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a SQLAlchemy AsyncSession, auto-committed on success,
    rolled back on exception, always closed.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


DbSession = Annotated[AsyncSession, Depends(get_db)]


# ── Redis ──────────────────────────────────────────────────────────────────────
async def get_redis():
    """Yield an aioredis client from the shared connection pool."""
    return await get_redis_connection()


RedisDep = Annotated[object, Depends(get_redis)]
