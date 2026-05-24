"""Repositório de Alerts."""
from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertSeverity
from app.schemas.alert import AlertCreate


class AlertRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, payload: AlertCreate) -> Alert:
        alert = Alert(
            device_id=payload.device_id,
            alert_type=payload.alert_type,
            severity=payload.severity,
            message=payload.message,
        )
        self._db.add(alert)
        await self._db.flush()
        await self._db.refresh(alert)
        return alert

    async def get_by_id(self, alert_id: uuid.UUID) -> Optional[Alert]:
        result = await self._db.execute(select(Alert).where(Alert.id == alert_id))
        return result.scalar_one_or_none()

    async def list_alerts(self, active_only: bool = False,
                          device_id: Optional[uuid.UUID] = None,
                          severity: Optional[AlertSeverity] = None,
                          page: int = 1, size: int = 20) -> Tuple[List[Alert], int]:
        q = select(Alert)
        if active_only:
            q = q.where(Alert.resolved_at.is_(None))
        if device_id:
            q = q.where(Alert.device_id == device_id)
        if severity:
            q = q.where(Alert.severity == severity)
        total = (await self._db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        rows = (await self._db.execute(q.order_by(Alert.created_at.desc())
                                        .offset((page - 1) * size).limit(size))).scalars().all()
        return list(rows), total

    async def acknowledge(self, alert: Alert) -> Alert:
        alert.acknowledged_at = datetime.now(timezone.utc)
        await self._db.flush()
        await self._db.refresh(alert)
        return alert

    async def resolve(self, alert: Alert) -> Alert:
        now = datetime.now(timezone.utc)
        alert.resolved_at = now
        if not alert.acknowledged_at:
            alert.acknowledged_at = now
        await self._db.flush()
        await self._db.refresh(alert)
        return alert

    async def get_history(self, days: int = 30, page: int = 1,
                          size: int = 50) -> Tuple[List[Alert], int]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        q = select(Alert).where(Alert.created_at >= cutoff)
        total = (await self._db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        rows = (await self._db.execute(q.order_by(Alert.created_at.desc())
                                        .offset((page - 1) * size).limit(size))).scalars().all()
        return list(rows), total
