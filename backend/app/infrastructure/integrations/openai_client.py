"""
OpenAI integration adapter.
 
Design decisions:
- Returns a typed dataclass so ai_service never imports the OpenAI SDK directly
- Mock path is deterministic and clearly labeled — no surprises in tests
- Cost guard: logs token usage on every real call
- The service layer depends on the return type, not on this module's internals
"""
from dataclasses import dataclass
from __future__ import annotations
from app.config import get_settings
from app.core.logger import get_logger
from app.core.exceptions import ExternalServiceError
from app.core.constants import OPENAI_MAX_TOKENS, OPENAI_MODEL, OPENAI_TEMPERATURE

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class AIResponse:
    text: str
    model: str
    tokens_used: int
    is_mock: bool
    source: str  # "openai" | "mock"


# ── Mock implementation ────────────────────────────────────────────────────────
def _mock_summarize(text: str) -> AIResponse:
    """
    Deterministic mock — activates when OPENAI_API_KEY is absent.
    Returns a clearly labeled summary so reviewers know it's simulated.
    """
    preview = text[:120].replace("\n", " ")
    summary = (
        f"[MOCK SUMMARY] This text discusses: \"{preview}...\". "
        "No OpenAI API key was configured; this is a simulated response."
    )
    logger.info("openai.mock_used", text_length=len(text))
    return AIResponse(
        text=summary,
        model="mock",
        tokens_used=0,
        is_mock=True,
        source="mock",
    )


# ── Real OpenAI implementation ─────────────────────────────────────────────────
async def call_openai_summarize(text: str) -> AIResponse:
    """
    Call OpenAI chat completions API.
    Falls back to mock if no API key is configured.
    Raises ExternalServiceError on API failures so the service layer
    can handle retries or surface a clean 502.
    """
    settings = get_settings()
 
    if not settings.has_openai:
        return _mock_summarize(text)
 
    try:
        from openai import AsyncOpenAI
 
        client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            organization=settings.openai_org_id,
        )
 
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a concise summarization assistant. "
                        "Summarize the given text in 2-3 sentences. "
                        "Be factual and neutral."
                    ),
                },
                {"role": "user", "content": text},
            ],
        )
 
        tokens = response.usage.total_tokens if response.usage else 0
        summary = response.choices[0].message.content or ""
 
        logger.info(
            "openai.call_success",
            model=OPENAI_MODEL,
            tokens_used=tokens,
            text_length=len(text),
        )
 
        return AIResponse(
            text=summary,
            model=OPENAI_MODEL,
            tokens_used=tokens,
            is_mock=False,
            source="openai",
        )
 
    except Exception as exc:
        logger.error("openai.call_failed", error=str(exc))
        raise ExternalServiceError(f"OpenAI request failed: {exc}") from exc
