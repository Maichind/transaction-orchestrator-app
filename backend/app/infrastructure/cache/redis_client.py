"""
Async Redis client.
 
A single pool is shared across the process lifetime. We initialize it
lazily on first use and expose it via get_redis_connection() so the
dependency layer can inject it without knowing the pool internals.
"""
from __future__ import annotations
import redis.asyncio as redis
from redis.asyncio import Redis
from app.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
_redis_pool: Redis | None = None


async def init_redis() -> None:
    """Create the connection pool. Called once during app lifespan startup."""
    global _redis_pool
    settings = get_settings()
    _redis_pool = redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        max_connections=20,
    )
    await _redis_pool.ping()
    logger.info("redis.connected", url=settings.redis_url)


async def close_redis() -> None:
    """Close the pool gracefully. Called during app lifespan shutdown."""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.aclose()
        _redis_pool = None
        logger.info("redis.disconnected")


async def get_redis_connection() -> Redis:
    """Return the shared Redis pool (lazy init if needed)."""
    global _redis_pool
    if _redis_pool is None:
        await init_redis()
    return _redis_pool
