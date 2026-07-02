"""
Idempotency layer backed by Redis.
 
Strategy:
  Key:   idempotency:{client_key}
  Value: JSON-serialized response payload
  TTL:   IDEMPOTENCY_TTL (24h default)
 
On first request  → MISS → process normally → cache result
On repeat request → HIT  → return cached result immediately (no DB write)
 
Why Redis over a DB unique constraint?
  - O(1) lookup before any SQL touches the wire
  - TTL is native (no cron job needed to clean up old keys)
  - Reduces DB load on high-frequency idempotent endpoints
"""
from __future__ import annotations
import json
from redis.asyncio import Redis
from app.core.logger import get_logger
from app.core.constants import IDEMPOTENCY_TTL

logger = get_logger(__name__)
_KEY_PREFIX = "idempotency:"


def _build_key(idempotency_key: str) -> str:
    return f"{_KEY_PREFIX}{idempotency_key}"


async def get_cached_response(
    redis: Redis, idempotency_key: str
) -> dict | None:
    """Return the cached response dict if the key exists, else None."""
    raw = await redis.get(_build_key(idempotency_key))
    if raw is None:
        return None
    logger.info("idempotency.cache_hit", key=idempotency_key)
    return json.loads(raw)


async def cache_response(
    redis: Redis,
    idempotency_key: str,
    response: dict,
    ttl: int = IDEMPOTENCY_TTL,
) -> None:
    """Persist the response under the idempotency key with TTL."""
    await redis.set(
        _build_key(idempotency_key),
        json.dumps(response, default=str),
        ex=ttl,
    )
    logger.info("idempotency.cached", key=idempotency_key, ttl=ttl)


async def delete_cached_response(redis: Redis, idempotency_key: str) -> None:
    """Remove a cached response (useful when a transaction fails and shouldn't be replayed)."""
    await redis.delete(_build_key(idempotency_key))
