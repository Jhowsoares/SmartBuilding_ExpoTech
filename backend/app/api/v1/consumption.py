"""Consumo energético — /api/v1/consumption."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.models.sensor_data import SensorData

router = APIRouter(prefix="/consumption", tags=["Consumption"])

# Constantes de consumo estimado (RN10 — eficiência energética)
_KW_POR_GRAU_ACIMA_IDEAL = 0.15   # kW extra por grau acima de 25°C
_KW_BASE_AC = 1.2                  # consumo base de 1 AC em kW
_IDEAL_TEMP = 24.0                 # setpoint padrão

_PERIOD_DELTA = {
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


def _estimate_kwh(avg_temp: float, hours: float) -> float:
    """Estima kWh com base na temperatura média."""
    extra = max(0.0, avg_temp - _IDEAL_TEMP) * _KW_POR_GRAU_ACIMA_IDEAL
    return round((_KW_BASE_AC + extra) * hours, 2)


@router.get("", status_code=200, summary="Histórico de consumo energético")
async def get_consumption(
    period: str = Query("24h", pattern="^(24h|7d|30d)$"),
    device_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    delta = _PERIOD_DELTA[period]
    cutoff = datetime.now(timezone.utc) - delta
    hours = delta.total_seconds() / 3600

    # Busca leituras de temperatura no período
    q = (
        select(
            func.date_trunc("hour", SensorData.timestamp).label("hora"),
            func.avg(SensorData.valor).label("avg_temp"),
            func.count(SensorData.id).label("leituras"),
        )
        .where(
            SensorData.tipo == "temperature",
            SensorData.timestamp >= cutoff,
        )
        .group_by("hora")
        .order_by("hora")
    )
    rows = (await db.execute(q)).all()

    breakdown_by_hour = []
    total_kwh = 0.0
    for row in rows:
        kwh = _estimate_kwh(float(row.avg_temp or _IDEAL_TEMP), 1.0)
        total_kwh += kwh
        breakdown_by_hour.append({
            "hora": row.hora.isoformat() if row.hora else None,
            "avg_temp_celsius": round(float(row.avg_temp or 0), 1),
            "leituras": row.leituras,
            "kwh_estimado": kwh,
        })

    if not breakdown_by_hour:
        # Estimativa sem dados reais: assume operação constante
        total_kwh = _estimate_kwh(_IDEAL_TEMP, hours)

    custo_brl = round(total_kwh * settings.ENERGIA_TARIFA_KWH_BRL, 2)

    return {
        "data": {
            "period": period,
            "cutoff": cutoff.isoformat(),
            "total_kwh": round(total_kwh, 2),
            "custo_brl": custo_brl,
            "tarifa_kwh_brl": settings.ENERGIA_TARIFA_KWH_BRL,
            "breakdown_by_hour": breakdown_by_hour,
        }
    }


@router.get("/summary", status_code=200, summary="Resumo de consumo por sala")
async def get_consumption_summary(
    period: str = Query("7d", pattern="^(24h|7d|30d)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    delta = _PERIOD_DELTA[period]
    cutoff = datetime.now(timezone.utc) - delta

    q = (
        select(
            SensorData.sensor_id,
            func.avg(SensorData.valor).label("avg_temp"),
            func.min(SensorData.valor).label("min_temp"),
            func.max(SensorData.valor).label("max_temp"),
            func.count(SensorData.id).label("total_leituras"),
        )
        .where(SensorData.tipo == "temperature", SensorData.timestamp >= cutoff)
        .group_by(SensorData.sensor_id)
        .order_by(func.avg(SensorData.valor).desc())
    )
    rows = (await db.execute(q)).all()
    hours = delta.total_seconds() / 3600

    sensors = []
    for row in rows:
        kwh = _estimate_kwh(float(row.avg_temp or _IDEAL_TEMP), hours)
        sensors.append({
            "sensor_id": row.sensor_id,
            "avg_temp": round(float(row.avg_temp or 0), 1),
            "min_temp": round(float(row.min_temp or 0), 1),
            "max_temp": round(float(row.max_temp or 0), 1),
            "total_leituras": row.total_leituras,
            "kwh_estimado": kwh,
            "custo_brl": round(kwh * settings.ENERGIA_TARIFA_KWH_BRL, 2),
        })

    return {"data": sensors, "period": period}
