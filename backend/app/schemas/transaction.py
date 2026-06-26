"""
Transaction schemas.

Intentional design:
- TransactionCreate: what the client sends
- TransactionResponse: what the system returns (always includes status + timestamps)
- AsyncProcessResponse: 202 Accepted with task_id for polling/WS tracking
- Separated from ORM models → no SQLAlchemy leaking into the API contract
"""
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from app.core.constants import TransactionStatus, TransactionType


class TransactionCreate(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64, examples=["user_abc123"])
    amount: Decimal = Field(..., gt=0, decimal_places=2, examples=[["100.00"]])
    type: TransactionType = Field(..., examples=[TransactionType.CREDIT])
    idempotency_key: str | None = Field(
        default=None,
        max_length=128,
        description="Optional client-supplied key for idempotent creates.",
        examples=["inv-2024-001"],
    )
 
    @field_validator("amount", mode="before")
    @classmethod
    def coerce_amount(cls, v: object) -> Decimal:
        return Decimal(str(v))


class TransactionResponse(BaseModel):
    id: UUID
    user_id: str
    amount: Decimal
    type: TransactionType
    status: TransactionStatus
    idempotency_key: str | None
    task_id: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
 
    model_config = {"from_attributes": True}


class AsyncProcessRequest(BaseModel):
    transaction_id: UUID = Field(..., description="ID of an existing transaction to process.")


class AsyncProcessResponse(BaseModel):
    transaction_id: UUID
    task_id: str
    status: TransactionStatus = TransactionStatus.PENDING
    message: str = "Transaction enqueued for async processing."


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    limit: int
    offset: int
