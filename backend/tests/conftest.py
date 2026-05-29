"""Configuração compartilhada para todos os testes pytest.

Usa httpx.AsyncClient com transport ASGI para rodar os testes
sem necessidade de um servidor real em execução — critério de
automação de testes do guia de avaliação.
"""
from __future__ import annotations

import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Variáveis mínimas de ambiente para os testes não falharem na importação
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-automated-tests")
os.environ.setdefault("MQTT_BROKER", "localhost")

from app.main import app  # noqa: E402 — importa depois das envvars


@pytest_asyncio.fixture
async def client():
    """AsyncClient com transport ASGI (sem servidor HTTP real)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
