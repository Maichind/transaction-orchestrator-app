"""
AILog ORM model — audit trail for every AI request/response.
 
Persisting both request and response serves dual purposes:
1. Cost tracking (tokens_used accumulates per day/user)
2. Debugging / replay (exact prompt that produced a given summary)
"""
from __future__ import annotations
import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean, Integer, String, Text
from app.infrastructure.database.models.base import Base, TimestampMixin


class AILog(Base, TimestampMixin):
    __tablename__ = "ai_logs"
 
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    output_text: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_mock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source: Mapped[str] = mapped_column(
        String(16), nullable=False, default="openai"
    )  # "openai" | "mock"
 
 
    def __repr__(self) -> str:
        return (
            f"<AILog id={self.id} model={self.model} "
            f"tokens={self.tokens_used} mock={self.is_mock}>"
        )
