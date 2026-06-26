"""
System-wide constants and enumerations.
 
Keeping enums here prevents circular imports: models, schemas, and services
all import from core — never from each other.
"""
from enum import StrEnum


class TransactionType(StrEnum):
    CREDIT = "credit"
    DEBIT = "debit"
    TRANSFER = "transfer"


class TransactionStatus(StrEnum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


# ── Cache TTLs (seconds) ───────────────────────────────────────────────────────
IDEMPOTENCY_TTL: int = 86_400        # 24 h — matches typical payment window
TASK_RESULT_TTL: int = 3_600         # 1 h

# ── Celery task settings ───────────────────────────────────────────────────────
TASK_MAX_RETRIES: int = 3
TASK_RETRY_BACKOFF: int = 2          # seconds; doubles each retry (exponential)
TASK_PROCESSING_SLEEP: float = 2.0   # simulated work duration

# ── Pagination defaults ────────────────────────────────────────────────────────
DEFAULT_PAGE_SIZE: int = 20
MAX_PAGE_SIZE: int = 100

# ── OpenAI ────────────────────────────────────────────────────────────────────
OPENAI_MODEL: str = "gpt-4o-mini"
OPENAI_MAX_TOKENS: int = 512
OPENAI_TEMPERATURE: float = 0.3
