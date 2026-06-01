"""Testes: depreciação de endpoints legados (Critério 5)."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.api_lifecycle import DEPRECATION_HEADERS


@pytest.mark.asyncio
async def test_sensor_history_marked_deprecated_in_openapi(client: AsyncClient) -> None:
    resp = await client.get("/api/openapi.json")
    path = resp.json()["paths"].get("/api/v1/sensors/{sensor_id}/data", {}).get("get", {})
    assert path.get("deprecated") is True


@pytest.mark.asyncio
async def test_sensor_history_returns_deprecation_headers(client: AsyncClient) -> None:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@smartbuilding.local", "password": "admin123"},
    )
    if login.status_code != 200:
        pytest.skip("Seed de usuários não disponível neste ambiente de teste")

    token = login.json()["access_token"]
    resp = await client.get(
        "/api/v1/sensors/sensor-temperature-room-101/data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        assert resp.headers.get("Deprecation") == DEPRECATION_HEADERS["Deprecation"]
        assert resp.headers.get("Sunset") == DEPRECATION_HEADERS["Sunset"]
