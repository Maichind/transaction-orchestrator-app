"""Assistant (AI summarization) HTTP routes."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from app.core.dependencies import DbSession
from app.core.exceptions import AppException
from app.services.ai_service import AIService
from app.schemas.assistant import SummarizeRequest, SummarizeResponse

router = APIRouter(prefix="/assistant", tags=["Assistant"])


@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    summary="Summarize text via OpenAI (falls back to mock if no API key)",
    responses={
        200: {"description": "Summary generated"},
        502: {"description": "OpenAI API unavailable (and mock disabled)"},
    },
)
async def summarize(
    payload: SummarizeRequest,
    session: DbSession,
) -> SummarizeResponse:
    """
    Summarize the provided text.
 
    - With `OPENAI_API_KEY` set → uses `gpt-4o-mini`
    - Without it → returns a clearly labeled mock response
    - Every request is persisted to `ai_logs` for cost tracking and audit
    """
    service = AIService(session=session)
    try:
        return await service.summarize(payload.text)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
