"""GET /api/v1/health — health check sem autenticação."""

from __future__ import annotations

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.database import ping_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])


async def _ping_redis() -> bool:
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        return True
    except Exception:
        return False


def _ping_mqtt() -> bool:
    """Verifica se o client MQTT está conectado ao broker."""
    try:
        from app.mqtt.client import mqtt_client

        return mqtt_client.is_connected
    except Exception:
        return False


def _ping_simulator() -> bool:
    """Estima se o simulador está ativo contando mensagens recentes no _device_state."""
    try:
        from app.mqtt.handlers import _device_state

        return len(_device_state) > 0
    except Exception:
        return False


def _build_payload(db_ok: bool, redis_ok: bool, mqtt_ok: bool, sim_ok: bool) -> dict:
    overall = "healthy" if (db_ok and redis_ok) else "degraded"
    return {
        "status": overall,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "subsystems": {
            "database": "ok" if db_ok else "unavailable",
            "redis": "ok" if redis_ok else "unavailable",
            "mqtt": "ok" if mqtt_ok else "unavailable",
            "simulator": "ok" if sim_ok else "unavailable",
        },
    }


@router.get("", summary="Health check")
async def health_check():
    """
    Monitoramento de subsistemas.

    Se o PostgreSQL estiver indisponível, retorna **503** em RFC 7807.
    MQTT/simulador offline degradam o status, mas não derrubam a API (falha parcial).
    """
    db_ok = await ping_db()
    redis_ok = await _ping_redis()
    mqtt_ok = _ping_mqtt()
    sim_ok = _ping_simulator()
    payload = _build_payload(db_ok, redis_ok, mqtt_ok, sim_ok)

    if not db_ok:
        return JSONResponse(
            status_code=503,
            content={
                "type": "https://smartbuilding.local/errors/service-unavailable",
                "title": "Serviço indisponível",
                "status": 503,
                "detail": "O subsistema de banco de dados está indisponível.",
                "instance": "/api/v1/health",
                "version": payload["version"],
                "environment": payload["environment"],
                "subsystems": payload["subsystems"],
            },
            headers={"Content-Type": "application/problem+json"},
        )

    return payload
