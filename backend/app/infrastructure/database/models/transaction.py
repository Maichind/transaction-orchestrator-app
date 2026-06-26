"""
Transaction persistence model.
 
Note: This is an ORM model (infrastructure concern), not a domain entity.
The separation allows us to evolve the DB schema independently of business
logic and makes the persistence layer swappable.
"""
import uuid
from decimal import Decimal
from __future__ import annotations
from sqlalchemy import Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.constants import TransactionStatus, TransactionType
from app.infrastructure.database.models.base import Base, TimestampMixin


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"
 
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(
        Numeric(precision=18, scale=2), nullable=False
    )
    type: Mapped[TransactionType] = mapped_column(
        String(16), nullable=False
    )
    status: Mapped[TransactionStatus] = mapped_column(
        String(16),
        nullable=False,
        default=TransactionStatus.PENDING,
        index=True,
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        String(128), nullable=True, unique=True, index=True
    )
    task_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
 

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.id} user={self.user_id} "
            f"amount={self.amount} status={self.status}>"
        )
