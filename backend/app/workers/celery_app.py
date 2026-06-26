"""
Celery application factory.
 
Configuration rationale:
- task_acks_late=True: task acknowledged AFTER completion, not on receipt
  → if worker crashes mid-task, broker re-delivers it (at-least-once)
- task_reject_on_worker_lost=True: re-queue on hard worker crash
- worker_prefetch_multiplier=1: fair dispatch (long tasks don't starve queue)
- result_expires: auto-cleanup of result backend keys
"""
from celery import Celery
from __future__ import annotations
from app.config import get_settings


def create_celery_app() -> Celery:
    settings = get_settings()
 
    app = Celery(
        "transaction_worker",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=["app.workers.tasks.transaction_tasks"],
    )
 
    app.conf.update(
        # Serialization
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        # Reliability
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        # Results
        result_expires=3600,
        # Timezone
        timezone="UTC",
        enable_utc=True,
        # Retry defaults (overridden per-task when needed)
        task_max_retries=3,
    )
 
    return app


celery_app = create_celery_app()
