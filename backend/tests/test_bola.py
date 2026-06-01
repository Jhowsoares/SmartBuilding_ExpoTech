"""Testes: BOLA / RBAC (OWASP API1) — Critério 3."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _login(client: AsyncClient, email: str, password: str) -> str | None:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    if resp.status_code != 200:
        return None
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_users_me_uses_token_sub_not_url_id(client: AsyncClient) -> None:
    token = await _login(client, "visualizador@smartbuilding.local", "view123")
    if not token:
        pytest.skip("Usuário visualizador não disponível no banco de teste")

    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "visualizador@smartbuilding.local"
    assert body["role"] == "visualizador"


@pytest.mark.asyncio
async def test_viewer_cannot_list_all_users(client: AsyncClient) -> None:
    token = await _login(client, "visualizador@smartbuilding.local", "view123")
    if not token:
        pytest.skip("Usuário visualizador não disponível no banco de teste")

    resp = await client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_viewer_cannot_train_model(client: AsyncClient) -> None:
    token = await _login(client, "visualizador@smartbuilding.local", "view123")
    if not token:
        pytest.skip("Usuário visualizador não disponível no banco de teste")

    resp = await client.post(
        "/api/v1/predictions/train",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
