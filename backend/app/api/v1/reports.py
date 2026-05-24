"""Relatórios consolidados — /api/v1/reports."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from io import StringIO

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.models.alert import Alert
from app.models.sensor_data import SensorData

router = APIRouter(prefix="/reports", tags=["Reports"])

_PERIOD_DELTA = {
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}
_KW_BASE = 1.2
_IDEAL_TEMP = 24.0
_KW_PER_DEGREE = 0.15


@router.get("/consumption", status_code=200, summary="Relatório de consumo")
async def get_consumption_report(
    period: str = Query("7d", pattern="^(24h|7d|30d)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    delta = _PERIOD_DELTA[period]
    cutoff = datetime.now(timezone.utc) - delta

    # Consumo por dia
    daily_q = (
        select(
            func.date_trunc("day", SensorData.timestamp).label("dia"),
            func.avg(SensorData.valor).label("avg_temp"),
            func.count(SensorData.id).label("leituras"),
        )
        .where(SensorData.tipo == "temperature", SensorData.timestamp >= cutoff)
        .group_by("dia")
        .order_by("dia")
    )
    daily_rows = (await db.execute(daily_q)).all()

    daily_data = []
    total_kwh = 0.0
    for row in daily_rows:
        extra = max(0.0, float(row.avg_temp or _IDEAL_TEMP) - _IDEAL_TEMP) * _KW_PER_DEGREE
        kwh = round((_KW_BASE + extra) * 24, 2)
        total_kwh += kwh
        daily_data.append({
            "dia": row.dia.date().isoformat() if row.dia else None,
            "avg_temp_celsius": round(float(row.avg_temp or 0), 1),
            "leituras": row.leituras,
            "kwh_estimado": kwh,
            "custo_brl": round(kwh * settings.ENERGIA_TARIFA_KWH_BRL, 2),
        })

    # Alertas no período
    alerts_count = (await db.execute(
        select(func.count(Alert.id)).where(Alert.created_at >= cutoff)
    )).scalar_one()

    # Temperatura média geral
    avg_temp_result = (await db.execute(
        select(func.avg(SensorData.valor))
        .where(SensorData.tipo == "temperature", SensorData.timestamp >= cutoff)
    )).scalar_one()
    avg_temp = round(float(avg_temp_result or 0), 1)

    return {
        "data": {
            "period": period,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_kwh": round(total_kwh, 2),
                "custo_total_brl": round(total_kwh * settings.ENERGIA_TARIFA_KWH_BRL, 2),
                "avg_temp_celsius": avg_temp,
                "total_alerts": alerts_count,
                "total_days": len(daily_data),
            },
            "daily_breakdown": daily_data,
        }
    }


@router.get("/consumption/export", summary="Exportar relatório de consumo em CSV")
async def export_consumption_csv(
    period: str = Query("7d", pattern="^(24h|7d|30d)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> StreamingResponse:
    """Exporta o relatório de consumo como arquivo CSV."""
    delta = _PERIOD_DELTA[period]
    cutoff = datetime.now(timezone.utc) - delta

    daily_q = (
        select(
            func.date_trunc("day", SensorData.timestamp).label("dia"),
            func.avg(SensorData.valor).label("avg_temp"),
            func.min(SensorData.valor).label("min_temp"),
            func.max(SensorData.valor).label("max_temp"),
            func.count(SensorData.id).label("leituras"),
        )
        .where(SensorData.tipo == "temperature", SensorData.timestamp >= cutoff)
        .group_by("dia")
        .order_by("dia")
    )
    rows = (await db.execute(daily_q)).all()

    output = StringIO()
    output.write("dia,avg_temp_c,min_temp_c,max_temp_c,leituras,kwh_estimado,custo_brl\n")
    for row in rows:
        extra = max(0.0, float(row.avg_temp or _IDEAL_TEMP) - _IDEAL_TEMP) * _KW_PER_DEGREE
        kwh = round((_KW_BASE + extra) * 24, 2)
        custo = round(kwh * settings.ENERGIA_TARIFA_KWH_BRL, 2)
        dia = row.dia.date().isoformat() if row.dia else ""
        output.write(
            f"{dia},{round(float(row.avg_temp or 0),1)},"
            f"{round(float(row.min_temp or 0),1)},{round(float(row.max_temp or 0),1)},"
            f"{row.leituras},{kwh},{custo}\n"
        )

    output.seek(0)
    filename = f"smartbuilding_consumo_{period}_{datetime.now().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/alerts", status_code=200, summary="Relatório de alertas")
async def get_alerts_report(
    period: str = Query("7d", pattern="^(24h|7d|30d)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    delta = _PERIOD_DELTA[period]
    cutoff = datetime.now(timezone.utc) - delta

    by_type = (await db.execute(
        select(Alert.alert_type, Alert.severity, func.count(Alert.id).label("total"))
        .where(Alert.created_at >= cutoff)
        .group_by(Alert.alert_type, Alert.severity)
        .order_by(func.count(Alert.id).desc())
    )).all()

    resolved_count = (await db.execute(
        select(func.count(Alert.id))
        .where(Alert.created_at >= cutoff, Alert.resolved_at.isnot(None))
    )).scalar_one()

    total = (await db.execute(
        select(func.count(Alert.id)).where(Alert.created_at >= cutoff)
    )).scalar_one()

    return {
        "data": {
            "period": period,
            "total_alerts": total,
            "resolved_alerts": resolved_count,
            "open_alerts": total - resolved_count,
            "resolution_rate": round(resolved_count / total * 100, 1) if total else 0,
            "by_type": [
                {"type": row.alert_type.value, "severity": row.severity.value, "total": row.total}
                for row in by_type
            ],
        }
    }
