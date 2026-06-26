"""
AIService — application layer orchestrator for summarization.

Delegates:
- Actual AI call → infrastructure/integrations/openai_client.py
- Persistence     → infrastructure/repositories/ai_log_repo.py
 
This service has no knowledge of HTTP or WebSockets.
"""
from __future__ import annotations
from app.core.logger import get_logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.assistant import SummarizeResponse
from app.infrastructure.database.models.ai_log import AILog
from app.infrastructure.repositories.ai_log_repository import AILogRepository
from app.infrastructure.integrations.openai_client import call_openai_summarize

logger = get_logger(__name__)


class AIService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = AILogRepository(session)


    async def summarize(self, text: str) -> SummarizeResponse:
        """
        Summarize text via OpenAI (or mock), persist the log, return response.
        """
        logger.info("ai_service.summarize_start", text_length=len(text))
 
        # 1. Call the integration adapter (handles mock/real transparently)
        ai_response = await call_openai_summarize(text)
 
        # 2. Persist request + response for audit and cost tracking
        log = AILog(
            input_text=text,
            output_text=ai_response.text,
            model=ai_response.model,
            tokens_used=ai_response.tokens_used,
            is_mock=ai_response.is_mock,
            source=ai_response.source,
        )
        saved = await self._repo.add(log)
 
        logger.info(
            "ai_service.summarize_done",
            log_id=str(saved.id),
            model=ai_response.model,
            tokens=ai_response.tokens_used,
            mock=ai_response.is_mock,
        )
 
        return SummarizeResponse(
            id=saved.id,
            summary=ai_response.text,
            model=ai_response.model,
            tokens_used=ai_response.tokens_used,
            source=ai_response.source,
            is_mock=ai_response.is_mock,
            created_at=saved.created_at,
        )
