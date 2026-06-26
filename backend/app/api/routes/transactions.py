"""
Transaction HTTP routes.

Routes are intentionally thin:
- Validate input (Pydantic does this automatically)
- Extract Idempotency-Key header
- Delegate to TransactionService
- Map domain exceptions to HTTP responses
- Return typed responses

No business logic lives here.
"""
import uuid
from __future__ import annotations
from app.core.dependencies import DbSession, RedisDep
from app.core.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from fastapi import APIRouter, Header, HTTPException, Query, status
from app.core.exceptions import AppException, NotFoundError, TaskEnqueueError
from app.schemas.transaction import (
    AsyncProcessRequest,
    AsyncProcessResponse,
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def _get_service(session: DbSession, redis: RedisDep) -> TransactionService:
    return TransactionService(session=session, redis=redis)


def _handle_app_exception(exc: AppException) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)


# ── POST /transactions/create ─────────────────────────────────────────────────
@router.post(
    "/create",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a transaction (idempotent)",
    responses={
        201: {"description": "Transaction created"},
        200: {"description": "Idempotent replay — transaction already exists"},
        422: {"description": "Validation error"},
    },
)
async def create_transaction(
    payload: TransactionCreate,
    session: DbSession,
    redis: RedisDep,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> TransactionResponse:
    """
    Create a new transaction.
 
    **Idempotency**: Supply an `Idempotency-Key` header (or `idempotency_key`
    in the body) to make this endpoint safe to retry. Duplicate requests with
    the same key return the original response without re-processing.
    """
    # Header takes precedence over body field
    if idempotency_key:
        payload = payload.model_copy(update={"idempotency_key": idempotency_key})
 
    service = _get_service(session, redis)
    try:
        response, created = await service.create(payload)
    except AppException as exc:
        raise _handle_app_exception(exc)
 
    # Signal to the client whether this was a fresh create or a cached replay
    # (No HTTP status change — 201 on both; use the Idempotent-Replayed header)
    return response


# ── POST /transactions/async-process ─────────────────────────────────────────
@router.post(
    "/async-process",
    response_model=AsyncProcessResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue a transaction for async processing",
    responses={
        202: {"description": "Transaction enqueued"},
        404: {"description": "Transaction not found"},
        503: {"description": "Queue unavailable"},
    },
)
async def async_process_transaction(
    payload: AsyncProcessRequest,
    session: DbSession,
    redis: RedisDep,
) -> AsyncProcessResponse:
    """
    Enqueue an existing transaction for background processing.
 
    Returns immediately with a `task_id`. Track progress via
    `GET /transactions/stream` (WebSocket) or `GET /transactions/{id}`.
    """
    service = _get_service(session, redis)
    try:
        return await service.enqueue(payload.transaction_id)
    except (NotFoundError, TaskEnqueueError) as exc:
        raise _handle_app_exception(exc)


# ── GET /transactions ─────────────────────────────────────────────────────────
@router.get(
    "",
    response_model=TransactionListResponse,
    summary="List all transactions (paginated)",
)
async def list_transactions(
    session: DbSession,
    redis: RedisDep,
    limit: int = Query(default=DEFAULT_PAGE_SIZE, le=MAX_PAGE_SIZE, ge=1),
    offset: int = Query(default=0, ge=0),
) -> TransactionListResponse:
    service = _get_service(session, redis)
    items = await service.list_all(limit=limit, offset=offset)
    return TransactionListResponse(items=items, total=len(items), limit=limit, offset=offset)


# ── GET /transactions/{transaction_id} ────────────────────────────────────────
@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Get a single transaction by ID",
    responses={404: {"description": "Not found"}},
)
async def get_transaction(
    transaction_id: uuid.UUID,
    session: DbSession,
    redis: RedisDep,
) -> TransactionResponse:
    service = _get_service(session, redis)
    try:
        return await service.get(transaction_id)
    except NotFoundError as exc:
        raise _handle_app_exception(exc)
