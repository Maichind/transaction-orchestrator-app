"""
Generic base repository.
 
Why a generic base?
- Eliminates copy-paste CRUD in every concrete repository
- Type-safe via Generic[T] — IDEs autocomplete correctly
- Easy to extend: concrete repos override only what differs
"""
from __future__ import annotations
from uuid import UUID
from sqlalchemy import select
from typing import Generic, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.models.base import Base
 
T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Generic async CRUD repository."""

    model: type[T]


    def __init__(self, session: AsyncSession) -> None:
        self.session = session


    async def get(self, record_id: UUID) -> T | None:
        return await self.session.get(self.model, record_id)


    async def list(self, limit: int = 20, offset: int = 0) -> list[T]:
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())


    async def add(self, instance: T) -> T:
        self.session.add(instance)
        await self.session.flush()   # assign DB-generated values (id, timestamps)
        await self.session.refresh(instance)
        return instance


    async def delete(self, instance: T) -> None:
        await self.session.delete(instance)
        await self.session.flush()
