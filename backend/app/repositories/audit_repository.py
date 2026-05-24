"""Repositório de AuditLog — compliance RN09."""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def log(self, action: str, user_id: Optional[str] = None,
                  resource: Optional[str] = None, metadata: Optional[dict] = None) -> None:
        try:
            self._db.add(AuditLog(user_id=user_id, action=action, resource=resource,
                                   metadata_json=metadata, timestamp=datetime.now(timezone.utc)))
            await self._db.flush()
        except Exception as exc:
            logger.warning("Falha ao registrar auditoria [%s]: %s", action, exc)
