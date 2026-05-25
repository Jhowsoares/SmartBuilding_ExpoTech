"""Sensores IoT — /api/v1/sensors/*"""

from __future__ import annotations
import logging, re
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.core.exceptions import ResourceNotFoundError
from app.schemas.base import HateoasLink, PaginationMeta
from app.schemas.sensor import (
    SensorDataIngest, SensorDataResponse, SensorLatestResponse,
    SensorListResponse, SensorResponse, SensorStatus, SensorTipo,
)
from app.services.sensor_service import SensorService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sensors", tags=["Sensors"])
_SENSOR_RE = re.compile(r"^sensor-(temperature|humidity|presence)-.+$")


@router.post("/data", response_model=SensorDataResponse, status_code=status.HTTP_201_CREATED,
             summary="Ingerir leitura de sensor IoT")
async def ingest_sensor_data(
    payload: SensorDataIngest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> SensorDataResponse:
    logger.info("POST /sensors/data | sensor=%s tipo=%s valor=%s tick=%d user=%s",
                payload.sensor_id, payload.tipo.value, payload.valor, payload.tick,
                current_user.get("sub", "unknown"))
    service = SensorService(db)
    return await service.ingest(payload=payload, user_id=current_user.get("sub", "system"))


@router.get("", response_model=SensorListResponse, status_code=200,
            summary="Listar sensores registrados", name="list_sensors")
async def list_sensors(
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
    tipo: Optional[SensorTipo] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> SensorListResponse:
    service = SensorService(db)
    sensors, total = await service.list_sensors(tipo=tipo.value if tipo else None, page=page, size=size)
    total_pages = max(1, -(-total // size)) if total else 0
    return SensorListResponse(
        data=sensors,
        meta=PaginationMeta(total=total, page=page, size=size, total_pages=total_pages),
    )


@router.get("/{sensor_id}", response_model=SensorResponse, status_code=200,
            summary="Detalhes de um sensor", name="get_sensor")
async def get_sensor(
    sensor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> SensorResponse:
    if not _SENSOR_RE.match(sensor_id):
        raise ResourceNotFoundError("Sensor", sensor_id)
    service = SensorService(db)
    latest = await service.get_latest(sensor_id)
    tipo = SensorTipo(sensor_id.split("-")[1])
    st = SensorStatus.OFFLINE
    if latest:
        now = datetime.now(timezone.utc)
        ts = latest.timestamp.replace(tzinfo=timezone.utc) if latest.timestamp.tzinfo is None else latest.timestamp
        if (now - ts).total_seconds() < 60:
            st = SensorStatus.ONLINE
    return SensorResponse(id=sensor_id, tipo=tipo, status=st,
                          last_seen=latest.timestamp if latest else None,
                          links=SensorResponse.build_links(sensor_id))


@router.get("/{sensor_id}/data", status_code=200, summary="Histórico de leituras", name="get_sensor_history")
async def get_sensor_history(
    sensor_id: str,
    period: str = Query("24h", pattern="^(1h|24h|7d|30d)$"),
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
    anomalies_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    if not _SENSOR_RE.match(sensor_id):
        raise ResourceNotFoundError("Sensor", sensor_id)
    service = SensorService(db)
    records, total = await service.get_history(sensor_id, period, page, size, anomalies_only)
    total_pages = max(1, -(-total // size)) if total else 0
    return {
        "data": [{"id": r.id, "sensor_id": r.sensor_id, "tipo": r.tipo, "valor": r.valor,
                  "tick": r.tick, "timestamp": r.timestamp.isoformat(), "is_anomaly": r.is_anomaly} for r in records],
        "meta": {"total": total, "page": page, "size": size, "total_pages": total_pages},
    }


@router.get("/{sensor_id}/latest", response_model=SensorLatestResponse, status_code=200,
            summary="Última leitura de um sensor", name="get_sensor_latest")
async def get_sensor_latest(
    sensor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> SensorLatestResponse:
    if not _SENSOR_RE.match(sensor_id):
        raise ResourceNotFoundError("Sensor", sensor_id)
    service = SensorService(db)
    result = await service.get_latest(sensor_id)
    if result is None:
        raise ResourceNotFoundError("Leitura para o sensor", sensor_id)
    return result
