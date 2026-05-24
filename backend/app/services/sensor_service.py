"""Serviço de Sensores — casos de uso de ingestão e consulta."""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sensor_data import SensorData
from app.repositories.audit_repository import AuditRepository
from app.repositories.sensor_repository import SensorRepository
from app.schemas.base import HateoasLink
from app.schemas.sensor import (
    SensorDataIngest, SensorDataResponse, SensorLatestResponse,
    SensorResponse, SensorStatus, SensorTipo,
)

logger = logging.getLogger(__name__)
_TEMP_ALERT_THRESHOLD = 40.0


class SensorService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = SensorRepository(db)
        self._audit = AuditRepository(db)

    async def ingest(self, payload: SensorDataIngest, user_id: str = "system") -> SensorDataResponse:
        # Detecção de anomalia (stub — Isolation Forest na Fase 6)
        is_anomaly = False

        record = await self._repo.create(payload, is_anomaly=is_anomaly)

        if payload.tipo == SensorTipo.TEMPERATURE and payload.valor > _TEMP_ALERT_THRESHOLD:
            logger.warning("HIGH_TEMPERATURE | sensor=%s valor=%.1f°C", payload.sensor_id, payload.valor)

        await self._audit.log(
            action="sensor_ingest", user_id=user_id, resource=payload.sensor_id,
            metadata={"tipo": payload.tipo.value, "valor": payload.valor,
                      "tick": payload.tick, "is_anomaly": is_anomaly, "record_id": record.id},
        )

        logger.info("Leitura persistida | id=%d sensor=%s tipo=%s valor=%s tick=%d",
                    record.id, record.sensor_id, record.tipo, record.valor, record.tick)

        return SensorDataResponse.build(payload=payload, record_id=record.id,
                                        is_anomaly=is_anomaly, created_at=record.received_at)

    async def get_latest(self, sensor_id: str) -> Optional[SensorLatestResponse]:
        record = await self._repo.get_latest(sensor_id)
        if not record:
            return None
        return SensorLatestResponse(
            sensor_id=record.sensor_id, tipo=SensorTipo(record.tipo),
            valor=record.valor, tick=record.tick, timestamp=record.timestamp,
            is_anomaly=record.is_anomaly,
            links=[
                HateoasLink(rel="self", href=f"/api/v1/sensors/{sensor_id}/latest"),
                HateoasLink(rel="sensor", href=f"/api/v1/sensors/{sensor_id}"),
                HateoasLink(rel="history", href=f"/api/v1/sensors/{sensor_id}/data"),
            ],
        )

    async def get_history(self, sensor_id: str, period: str = "24h", page: int = 1,
                          size: int = 20, anomalies_only: bool = False) -> Tuple[List[SensorData], int]:
        return await self._repo.get_history(sensor_id, period, page, size, anomalies_only)

    async def list_sensors(self, tipo: Optional[str] = None, page: int = 1,
                           size: int = 20) -> Tuple[List[SensorResponse], int]:
        sensor_ids, total = await self._repo.get_distinct_sensors(tipo, page, size)
        sensors = []
        now = datetime.now(timezone.utc)
        for sid in sensor_ids:
            latest = await self._repo.get_latest(sid)
            tipo_enum = SensorTipo(sid.split("-")[1]) if "-" in sid else SensorTipo.TEMPERATURE
            st = SensorStatus.OFFLINE
            if latest and latest.timestamp:
                ts = latest.timestamp.replace(tzinfo=timezone.utc) if latest.timestamp.tzinfo is None else latest.timestamp
                if (now - ts).total_seconds() < 60:
                    st = SensorStatus.ONLINE
            sensors.append(SensorResponse(id=sid, tipo=tipo_enum, status=st,
                                          last_seen=latest.timestamp if latest else None,
                                          links=SensorResponse.build_links(sid)))
        return sensors, total
