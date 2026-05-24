"""Repositório de SensorData — acesso ao banco."""
from __future__ import annotations
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sensor_data import SensorData
from app.schemas.sensor import SensorDataIngest

logger = logging.getLogger(__name__)

_PERIOD_DELTA = {"1h": timedelta(hours=1), "24h": timedelta(hours=24),
                 "7d": timedelta(days=7), "30d": timedelta(days=30)}


class SensorRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, payload: SensorDataIngest, is_anomaly: bool = False) -> SensorData:
        record = SensorData(
            sensor_id=payload.sensor_id, tipo=payload.tipo.value,
            valor=payload.valor, tick=payload.tick, timestamp=payload.timestamp,
            is_anomaly=is_anomaly, received_at=datetime.now(timezone.utc),
        )
        self._db.add(record)
        await self._db.flush()
        await self._db.refresh(record)
        return record

    async def get_latest(self, sensor_id: str) -> Optional[SensorData]:
        result = await self._db.execute(
            select(SensorData).where(SensorData.sensor_id == sensor_id)
            .order_by(SensorData.timestamp.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_history(self, sensor_id: str, period: str = "24h", page: int = 1,
                          size: int = 20, anomalies_only: bool = False) -> Tuple[List[SensorData], int]:
        cutoff = datetime.now(timezone.utc) - _PERIOD_DELTA.get(period, timedelta(hours=24))
        q = select(SensorData).where(SensorData.sensor_id == sensor_id, SensorData.timestamp >= cutoff)
        if anomalies_only:
            q = q.where(SensorData.is_anomaly.is_(True))
        total = (await self._db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        rows = (await self._db.execute(q.order_by(SensorData.timestamp.desc()).offset((page-1)*size).limit(size))).scalars().all()
        return list(rows), total

    async def get_distinct_sensors(self, tipo: Optional[str] = None, page: int = 1,
                                   size: int = 20) -> Tuple[List[str], int]:
        q = select(SensorData.sensor_id, SensorData.tipo).distinct()
        if tipo:
            q = q.where(SensorData.tipo == tipo)
        total = (await self._db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        rows = (await self._db.execute(q.offset((page-1)*size).limit(size))).all()
        return [r[0] for r in rows], total
