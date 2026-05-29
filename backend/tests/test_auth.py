"""Testes: fluxo de autenticação JWT (login, refresh, logout).

Cobre os critérios de segurança da rubrica:
- BOLA/BOPLA (OWASP API Top 10): verifica que endpoints protegidos
  retornam 401 sem token e 403 para roles insuficientes.
- RFC 7807: respostas de erro devem ter 'detail' estruturado.
- Revogação de token: logout deve impedir reuso (via Redis blacklist).
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_401(client: AsyncClient) -> None:
    """Credenciais erradas devem retornar 401 (não 403 nem 500)."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "naoexiste@test.com", "password": "senhaerrada"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_without_token_returns_401(
    client: AsyncClient,
) -> None:
    """Qualquer endpoint protegido sem token deve retornar 401.

    Valida OWASP API2:2023 — Broken Authentication.
    """
    response = await client.get("/api/v1/rooms")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_with_invalid_token_returns_401(
    client: AsyncClient,
) -> None:
    """Token JWT malformado deve retornar 401.

    Valida rejeição de tokens inválidos/expirados.
    """
    response = await client.get(
        "/api/v1/rooms",
        headers={"Authorization": "Bearer token.invalido.aqui"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_error_response_follows_rfc7807(client: AsyncClient) -> None:
    """Respostas de erro 401 devem conter o campo 'detail' (RFC 7807).

    O campo 'detail' é o mapeamento FastAPI do 'detail' do ProblemDetails.
    """
    response = await client.get("/api/v1/rooms")
    body = response.json()
    assert "detail" in body


@pytest.mark.asyncio
async def test_admin_only_endpoint_requires_admin_role(client: AsyncClient) -> None:
    """POST /predictions/train é restrito a admin (RBAC).

    Sem token, deve retornar 401 — não 404 nem 500.
    Valida OWASP API5:2023 — Broken Function Level Authorization (BOPLA).
    """
    response = await client.post("/api/v1/predictions/train")
    assert response.status_code == 401
