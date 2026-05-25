"""GET /api/v1/health — health check sem autenticação."""

from __future__ import annotations
import logging
from fastapi import APIRouter
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


@router.get("", summary="Health check", status_code=200)
async def health_check() -> dict:
    db_ok = await ping_db()
    redis_ok = await _ping_redis()
    mqtt_ok = _ping_mqtt()
    sim_ok = _ping_simulator()
    overall = "healthy" if (db_ok and redis_ok) else "degraded"
    return {
        "status": overall,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "subsystems": {
            "database":  "ok" if db_ok    else "unavailable",
            "redis":     "ok" if redis_ok  else "unavailable",
            "mqtt":      "ok" if mqtt_ok   else "unavailable",
            "simulator": "ok" if sim_ok    else "unavailable",
        },
    }
