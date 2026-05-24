"""Serviço de Alerts."""
from __future__ import annotations
import logging
import uuid
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertSeverity
from app.repositories.alert_repository import AlertRepository
from app.repositories.audit_repository import AuditRepository
from app.schemas.alert import AlertCreate, AlertResponse
from app.core.exceptions import ResourceNotFoundError

logger = logging.getLogger(__name__)


class AlertService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = AlertRepository(db)
        self._audit = AuditRepository(db)

    async def create_alert(self, payload: AlertCreate, user_id: str = "system") -> AlertResponse:
        alert = await self._repo.create(payload)
        logger.warning("Alerta criado | id=%s type=%s severity=%s device=%s",
                       alert.id, alert.alert_type, alert.severity, alert.device_id)
        await self._audit.log(action="alert_create", user_id=user_id, resource=str(alert.id),
                               metadata={"alert_type": alert.alert_type.value,
                                         "severity": alert.severity.value,
                                         "device_id": str(alert.device_id)})
        return self._to_response(alert)

    async def list_alerts(self, active_only: bool = False,
                          device_id: Optional[uuid.UUID] = None,
                          severity: Optional[AlertSeverity] = None,
                          page: int = 1, size: int = 20) -> Tuple[List[AlertResponse], int]:
        alerts, total = await self._repo.list_alerts(
            active_only=active_only, device_id=device_id, severity=severity, page=page, size=size
        )
        return [self._to_response(a) for a in alerts], total

    async def get_alert(self, alert_id: uuid.UUID) -> AlertResponse:
        alert = await self._repo.get_by_id(alert_id)
        if not alert:
            raise ResourceNotFoundError("Alert", str(alert_id))
        return self._to_response(alert)

    async def acknowledge_alert(self, alert_id: uuid.UUID,
                                user_id: str = "system") -> AlertResponse:
        alert = await self._repo.get_by_id(alert_id)
        if not alert:
            raise ResourceNotFoundError("Alert", str(alert_id))
        if alert.acknowledged_at:
            return self._to_response(alert)
        alert = await self._repo.acknowledge(alert)
        await self._audit.log(action="alert_acknowledge", user_id=user_id,
                               resource=str(alert_id), metadata={})
        logger.info("Alerta reconhecido | id=%s user=%s", alert_id, user_id)
        return self._to_response(alert)

    async def resolve_alert(self, alert_id: uuid.UUID,
                            user_id: str = "system") -> AlertResponse:
        alert = await self._repo.get_by_id(alert_id)
        if not alert:
            raise ResourceNotFoundError("Alert", str(alert_id))
        alert = await self._repo.resolve(alert)
        await self._audit.log(action="alert_resolve", user_id=user_id,
                               resource=str(alert_id), metadata={})
        return self._to_response(alert)

    async def get_history(self, days: int = 30, page: int = 1,
                          size: int = 50) -> Tuple[List[AlertResponse], int]:
        alerts, total = await self._repo.get_history(days=days, page=page, size=size)
        return [self._to_response(a) for a in alerts], total

    @staticmethod
    def _to_response(alert: Alert) -> AlertResponse:
        return AlertResponse(
            id=alert.id, device_id=alert.device_id,
            alert_type=alert.alert_type, severity=alert.severity,
            message=alert.message, created_at=alert.created_at,
            acknowledged_at=alert.acknowledged_at, resolved_at=alert.resolved_at,
            is_active=alert.resolved_at is None,
            links=AlertResponse.build_links(alert.id),
        )
