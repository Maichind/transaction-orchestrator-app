"""
Transaction repository — data access for the Transaction model.
 
Concrete repos add domain-specific queries on top of BaseRepository.
Services call repos; repos never call services.
"""
from uuid import UUID
from __future__ import annotations
from sqlalchemy import select, update
from app.core.constants import TransactionStatus
from app.infrastructure.repositories.base import BaseRepository
from app.infrastructure.database.models.transaction import Transaction


class TransactionRepository(BaseRepository[Transaction]):
    model = Transaction
 

    async def get_by_idempotency_key(self, key: str) -> Transaction | None:
        result = await self.session.execute(
            select(Transaction).where(Transaction.idempotency_key == key)
        )
        return result.scalar_one_or_none()
 

    async def list_by_user(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> list[Transaction]:
        result = await self.session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
 

    async def update_status(
        self,
        transaction_id: UUID,
        status: TransactionStatus,
        error_message: str | None = None,
        task_id: str | None = None,
    ) -> Transaction | None:
        await self.session.execute(
            update(Transaction)
            .where(Transaction.id == transaction_id)
            .values(
                status=status,
                error_message=error_message,
                task_id=task_id,
            )
        )
        await self.session.flush()
        return await self.get(transaction_id)
