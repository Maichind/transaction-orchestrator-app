"""
Application configuration via pydantic-settings.
 
Why pydantic-settings over python-decouple or os.environ?
- Type validation + coercion at startup (fail fast, not at runtime)
- IDE autocomplete on Settings attributes
- .env file support out of the box
- Cached with @lru_cache so the file is parsed once per process
"""
from functools import lru_cache
from __future__ import annotations
from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

 
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
 
    # ── App ────────────────────────────────────────────────────────────────────
    app_name: str = "TransactionAPI"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    json_logs: bool = False         # True in production containers
 
    # ── Database ───────────────────────────────────────────────────────────────
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/transactions_db"
    )
 
    # ── Redis ──────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
 
    # ── Celery ────────────────────────────────────────────────────────────────
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
 
    # ── OpenAI ────────────────────────────────────────────────────────────────
    openai_api_key: str | None = None   # None → mock fallback activates
    openai_org_id: str | None = None
 
    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
 
    @computed_field
    @property
    def has_openai(self) -> bool:
        """True when a real OpenAI key is configured."""
        return bool(self.openai_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance (parsed once, cached forever)."""
    return Settings()
