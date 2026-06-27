"""Integration tests — Assistant endpoint."""
import pytest
from httpx import AsyncClient
from __future__ import annotations
from unittest.mock import AsyncMock, patch
from app.infrastructure.integrations.openai_client import AIResponse


@pytest.mark.asyncio
async def test_summarize_returns_mock_when_no_key(client: AsyncClient) -> None:
    mock_ai = AIResponse(
        text="[MOCK SUMMARY] A summary.",
        model="mock",
        tokens_used=0,
        is_mock=True,
        source="mock",
    )
    with patch(
        "app.infrastructure.integrations.openai_client.call_openai_summarize",
        new=AsyncMock(return_value=mock_ai),
    ):
        response = await client.post("/assistant/summarize", json={
            "text": "Python is a widely used high-level programming language."
        })

    assert response.status_code == 200
    data = response.json()
    assert data["is_mock"] is True
    assert data["source"] == "mock"
    assert data["tokens_used"] == 0
    assert "id" in data
    assert "summary" in data


@pytest.mark.asyncio
async def test_summarize_validates_min_length(client: AsyncClient) -> None:
    response = await client.post("/assistant/summarize", json={"text": "short"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_summarize_persists_and_returns_created_at(client: AsyncClient) -> None:
    mock_ai = AIResponse(
        text="Summary here.",
        model="mock",
        tokens_used=0,
        is_mock=True,
        source="mock",
    )
    with patch(
        "app.infrastructure.integrations.openai_client.call_openai_summarize",
        new=AsyncMock(return_value=mock_ai),
    ):
        response = await client.post("/assistant/summarize", json={
            "text": "FastAPI is a modern Python web framework for building APIs."
        })

    data = response.json()
    assert "created_at" in data
    assert data["created_at"] is not None
