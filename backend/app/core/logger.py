"""
Centralized logging configuration using structlog.
 
Why structlog over plain logging?
- Structured key=value context travels with the log record (user_id, task_id…)
- JSON output in production feeds directly into log aggregators (Datadog, Loki)
- Dev mode renders pretty colored output with no config change from callers
"""
import sys
import logging
import structlog
from __future__ import annotations


def configure_logging(log_level: str = "INFO", json_logs: bool = False) -> None:
    """Call once at application startup (main.py lifespan)."""

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
 
    if json_logs:
        # Production: machine-readable JSON
        renderer = structlog.processors.JSONRenderer()
    else:
        # Development: human-readable with colors
        renderer = structlog.dev.ConsoleRenderer()
 
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
 
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )
 
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
 
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())
 
    # Silence noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "celery.app.trace"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a bound logger with the given module name."""
    return structlog.get_logger(name)
