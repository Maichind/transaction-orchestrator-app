"""
Domain exception hierarchy.
 
Design rationale:
- All exceptions inherit from AppException so callers can catch broadly.
- HTTP status codes live here as metadata; the API layer maps them to responses.
- No FastAPI imports — this module has zero external dependencies.
"""
from __future__ import annotations


class AppException(Exception):
    """Base for all application-level exceptions."""
 
    status_code: int = 500
    default_message: str = "An unexpected error occurred."
 
    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)
 
 
# ── 4xx Client errors ──────────────────────────────────────────────────────────
class ValidationError(AppException):
    status_code = 422
    default_message = "Validation failed."


class NotFoundError(AppException):
    status_code = 404
    default_message = "Resource not found."


class ConflictError(AppException):
    """Raised when a resource already exists (e.g. duplicate idempotency key with
    a different payload — signals caller sent inconsistent duplicate request)."""
    status_code = 409
    default_message = "Resource conflict."


class IdempotencyConflictError(ConflictError):
    """Same idempotency key, different payload — suspicious duplicate."""
    default_message = "Idempotency key reuse with different payload."


# ── 5xx Server errors ──────────────────────────────────────────────────────────
class ExternalServiceError(AppException):
    """Raised when a third-party integration fails (OpenAI, etc.)."""
    status_code = 502
    default_message = "External service is unavailable."


class TaskEnqueueError(AppException):
    """Raised when Celery fails to enqueue a task."""
    status_code = 503
    default_message = "Could not enqueue background task."
