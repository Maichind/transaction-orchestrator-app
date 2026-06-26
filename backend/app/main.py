"""
FastAPI application factory.
 
Uses the lifespan context manager (FastAPI 0.93+) instead of deprecated
@app.on_event handlers. This gives us clean startup/shutdown semantics
that also work correctly in tests.
"""
from __future__ import annotations
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.exceptions import AppException
from app.core.logger import configure_logging, get_logger
from app.infrastructure.cache.redis_client import close_redis, init_redis

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage startup and shutdown of shared resources."""
    settings = get_settings()
    configure_logging(log_level=settings.log_level, json_logs=settings.json_logs)
    logger.info("app.starting", version=settings.app_version)
 
    # ── Startup ───────────────────────────────────────────────────────────────
    await init_redis()
 
    logger.info("app.ready")
    yield
 
    # ── Shutdown ──────────────────────────────────────────────────────────────
    await close_redis()
    logger.info("app.stopped")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Global exception handler ───────────────────────────────────────────────
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "app.exception",
            status=exc.status_code,
            message=exc.message,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "type": type(exc).__name__},
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    from app.api.routes.assistant import router as assistant_router
    from app.api.routes.transactions import router as transactions_router
    from app.api.websocket.transactions_stream import router as ws_router

    app.include_router(assistant_router)
    app.include_router(transactions_router)
    app.include_router(ws_router)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health() -> dict:
        return {"status": "ok", "version": settings.app_version}

    return app


app = create_app()
