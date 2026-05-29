"""Testes: endpoint público de health-check.

Verifica que o endpoint /health responde 200 e que o header
Cache-Control injeta corretamente o valor 'private, no-store'
para endpoints da API (middleware implementado em main.py).
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient) -> None:
    """GET /health deve retornar HTTP 200."""
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_has_status_field(client: AsyncClient) -> None:
    """Resposta do /health deve conter o campo 'status'."""
    response = await client.get("/health")
    body = response.json()
    assert "status" in body


@pytest.mark.asyncio
async def test_api_responses_have_cache_control_header(client: AsyncClient) -> None:
    """Respostas da API /api/ devem incluir Cache-Control: private, no-store (LGPD).

    Este teste valida o middleware de Cache-Control adicionado em main.py.
    Mesmo que o endpoint retorne 401, o header deve estar presente.
    """
    response = await client.get("/api/v1/rooms")
    assert "cache-control" in response.headers
    assert "no-store" in response.headers["cache-control"]
