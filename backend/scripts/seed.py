"""
Seed script: populates the DB with demo transactions.
 
Usage:
    cd backend && python -m scripts.seed
    # or via Makefile:
    make seed
"""
import uuid
import random
import asyncio
from decimal import Decimal
from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.engine import engine
from app.infrastructure.database.models.base import Base
from app.core.constants import TransactionStatus, TransactionType
from app.infrastructure.database.models.transaction import Transaction
from app.infrastructure.database.session import async_session_factory


USERS = ["user_alice", "user_bob", "user_carol", "user_dave"]
TYPES = list(TransactionType)
STATUSES = [TransactionStatus.PENDING, TransactionStatus.PROCESSED, TransactionStatus.FAILED]
STATUS_WEIGHTS = [0.3, 0.6, 0.1]


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Tables ensured")


async def seed_transactions(session: AsyncSession, count: int = 30) -> None:
    transactions = [
        Transaction(
            id=uuid.uuid4(),
            user_id=random.choice(USERS),
            amount=Decimal(str(round(random.uniform(10, 9999), 2))),
            type=random.choice(TYPES),
            status=random.choices(STATUSES, weights=STATUS_WEIGHTS)[0],
            idempotency_key=f"seed-{uuid.uuid4().hex[:12]}",
        )
        for _ in range(count)
    ]
    session.add_all(transactions)
    await session.commit()
    print(f"✓ Seeded {count} transactions")


async def main() -> None:
    await create_tables()
    async with async_session_factory() as session:
        await seed_transactions(session)
    print("✓ Seed complete")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
