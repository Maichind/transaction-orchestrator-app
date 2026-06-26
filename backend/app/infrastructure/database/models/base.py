"""
Shared ORM base class.
 
All models inherit from Base to share the same metadata registry,
which is required for Alembic autogenerate to work correctly.
 
TimestampMixin provides created_at/updated_at without repeating them.
"""
from __future__ import annotations
from sqlalchemy import DateTime, func
from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedColumn, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """Auto-managed created_at and updated_at columns."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
