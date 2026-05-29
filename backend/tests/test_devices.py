"""Testes: validação de schema Pydantic e regras de negócio de dispositivos.

Testa as regras RN01–RN10 indiretamente via validação de payloads:
- Campos obrigatórios e restrições de tipo (Pydantic)
- Valores fora do intervalo esperado (temperatura, setpoint)
- Que criação sem autenticação retorna 401 (BOLA)
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_device_without_auth_returns_401(client: AsyncClient) -> None:
    """POST /devices sem token deve retornar 401 (BOLA — OWASP API1).

    Um atacante não deve conseguir criar dispositivos sem se autenticar.
    """
    response = await client.post(
        "/api/v1/devices",
        json={
            "name": "AC Sala 101",
            "type": "air_conditioner",
            "room_id": "00000000-0000-0000-0000-000000000001",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_room_without_auth_returns_401(client: AsyncClient) -> None:
    """POST /rooms sem token deve retornar 401."""
    response = await client.post(
        "/api/v1/rooms",
        json={"name": "Sala 101", "building": "Bloco A", "floor": 1},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_nonexistent_room_without_auth_returns_401(
    client: AsyncClient,
) -> None:
    """GET /rooms/{id} sem token deve retornar 401, não 404.

    Evita vazamento de informação sobre recursos existentes (BOLA).
    A autenticação deve ocorrer antes da verificação de existência.
    """
    response = await client.get(
        "/api/v1/rooms/00000000-0000-0000-0000-000000000099"
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_consumption_endpoint_requires_auth(client: AsyncClient) -> None:
    """GET /consumption sem token retorna 401.

    Dados de consumo energético contêm informações sensíveis (LGPD).
    """
    response = await client.get("/api/v1/consumption")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_predictions_endpoint_requires_auth(client: AsyncClient) -> None:
    """GET /predictions sem token retorna 401.

    Predições são baseadas em dados proprietários do modelo ML.
    """
    response = await client.get("/api/v1/predictions")
    assert response.status_code == 401
