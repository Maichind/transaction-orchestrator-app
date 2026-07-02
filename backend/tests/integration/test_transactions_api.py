"""Integration tests — Transaction HTTP endpoints."""
from __future__ import annotations
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_transaction_201(client: AsyncClient) -> None:
    response = await client.post("/transactions/create", json={
        "user_id": "user_integration",
        "amount": "150.00",
        "type": "credit",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == "user_integration"
    assert data["status"] == "pending"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_transaction_idempotent(client: AsyncClient) -> None:
    payload = {"user_id": "user_idem", "amount": "99.99", "type": "debit"}
    headers = {"Idempotency-Key": "integ-test-key-001"}

    r1 = await client.post("/transactions/create", json=payload, headers=headers)
    r2 = await client.post("/transactions/create", json=payload, headers=headers)

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["id"] == r2.json()["id"]


@pytest.mark.asyncio
async def test_create_transaction_invalid_amount(client: AsyncClient) -> None:
    response = await client.post("/transactions/create", json={
        "user_id": "user_x",
        "amount": "-50.00",
        "type": "credit",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_transaction_404(client: AsyncClient) -> None:
    response = await client.get("/transactions/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_transactions(client: AsyncClient) -> None:
    # Create 3 transactions
    for i in range(3):
        await client.post("/transactions/create", json={
            "user_id": "user_list",
            "amount": f"{(i+1)*10}.00",
            "type": "credit",
        })

    response = await client.get("/transactions?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 3
    assert len(data["items"]) >= 3


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
