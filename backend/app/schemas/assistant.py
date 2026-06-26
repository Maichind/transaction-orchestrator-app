"""Assistant endpoint schemas."""
from uuid import UUID
from datetime import datetime
from __future__ import annotations
from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=10,
        max_length=8_000,
        description="Text to summarize.",
        examples=["Python is a high-level programming language..."],
    )


class SummarizeResponse(BaseModel):
    id: UUID
    summary: str
    model: str
    tokens_used: int
    source: str          # "openai" | "mock"
    is_mock: bool
    created_at: datetime
 
    model_config = {"from_attributes": True}
