"""Unit tests — AIService with mocked OpenAI integration."""
import pytest
from __future__ import annotations
from unittest.mock import AsyncMock, patch
from app.infrastructure.integrations.openai_client import AIResponse


@pytest.mark.asyncio
async def test_summarize_uses_mock_when_no_key(test_session) -> None:
    from app.services.ai_service import AIService

    mock_response = AIResponse(
        text="[MOCK SUMMARY] This is a test summary.",
        model="mock",
        tokens_used=0,
        is_mock=True,
        source="mock",
    )

    with patch(
        "app.infrastructure.integrations.openai_client.call_openai_summarize",
        new=AsyncMock(return_value=mock_response),
    ):
        service = AIService(session=test_session)
        result = await service.summarize("Python is a high-level programming language.")

    assert result.is_mock is True
    assert result.source == "mock"
    assert result.tokens_used == 0
    assert result.id is not None


@pytest.mark.asyncio
async def test_summarize_persists_log(test_session) -> None:
    from app.services.ai_service import AIService
    from app.infrastructure.repositories.ai_log_repository import AILogRepository

    mock_response = AIResponse(
        text="Summary text here.",
        model="gpt-4o-mini",
        tokens_used=42,
        is_mock=False,
        source="openai",
    )

    with patch(
        "app.infrastructure.integrations.openai_client.call_openai_summarize",
        new=AsyncMock(return_value=mock_response),
    ):
        service = AIService(session=test_session)
        await service.summarize("Some text to summarize.")
        await test_session.commit()

    repo = AILogRepository(test_session)
    logs = await repo.list(limit=10)
    assert len(logs) == 1
    assert logs[0].tokens_used == 42
    assert logs[0].source == "openai"
