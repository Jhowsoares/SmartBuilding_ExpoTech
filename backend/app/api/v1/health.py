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


@router.get("", summary="Health check", status_code=200)
async def health_check() -> dict:
    db_ok = await ping_db()
    redis_ok = await _ping_redis()
    overall = "healthy" if (db_ok and redis_ok) else "degraded"
    return {
        "status": overall,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "subsystems": {
            "database": "ok" if db_ok else "unavailable",
            "redis": "ok" if redis_ok else "unavailable",
            "mqtt": "not_checked",
        },
    }
