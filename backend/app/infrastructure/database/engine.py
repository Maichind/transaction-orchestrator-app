"""
SQLAlchemy async engine factory.
 
Keeping engine creation separate from session creation follows SRP:
engine.py = connection pool config
session.py = unit-of-work factory
"""
from __future__ import annotations
from app.config import get_settings
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def build_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        str(settings.database_url),
        echo=settings.debug,          # SQL logging in debug mode only
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,           # detect stale connections before use
        pool_recycle=3600,            # recycle connections every hour
    )
 

# Module-level singleton — imported by session.py and Alembic env.py
engine: AsyncEngine = build_engine()
