"""Testes: health check, falha parcial e 503 quando DB indisponível."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200_when_db_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in ("healthy", "degraded")
    assert "subsystems" in body
    assert "database" in body["subsystems"]


@pytest.mark.asyncio
async def test_health_reports_subsystems(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    subs = response.json()["subsystems"]
    assert set(subs.keys()) >= {"database", "redis", "mqtt", "simulator"}


@pytest.mark.asyncio
async def test_health_returns_503_rfc7807_when_db_down(client: AsyncClient) -> None:
    with patch("app.api.v1.health.ping_db", new=AsyncMock(return_value=False)):
        response = await client.get("/api/v1/health")
    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["status"] == 503
    assert body["title"] == "Serviço indisponível"
    assert "subsystems" in body


@pytest.mark.asyncio
async def test_api_responses_have_cache_control_header(client: AsyncClient) -> None:
    response = await client.get("/api/v1/rooms")
    assert "cache-control" in response.headers
    assert "no-store" in response.headers["cache-control"]
