"""
AsyncSession factory.
 
Using async_sessionmaker (SQLAlchemy 2.x) over the older sessionmaker
for native async support and better type inference.
"""
from __future__ import annotations
from app.infrastructure.database.engine import engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,   # avoids lazy-load errors after commit
    autoflush=False,          # explicit flush control inside services
)
