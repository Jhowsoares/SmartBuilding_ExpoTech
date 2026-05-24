"""Predições de consumo — /api/v1/predictions."""
from __future__ import annotations
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_admin
from app.models.sensor_data import SensorData

router = APIRouter(prefix="/predictions", tags=["Predictions"])
logger = logging.getLogger(__name__)


async def _get_base_temp(db: AsyncSession) -> float:
    """Retorna a temperatura média das últimas 2h para usar como base."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=2)
    from sqlalchemy import func
    result = await db.execute(
        select(func.avg(SensorData.valor))
        .where(SensorData.tipo == "temperature", SensorData.timestamp >= cutoff)
    )
    val = result.scalar_one_or_none()
    return float(val) if val else 24.0


@router.get("/24h", status_code=200, summary="Predição de consumo para as próximas 24 horas")
async def get_predictions_24h(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    from app.ml.predictor import predictor

    base_temp = await _get_base_temp(db)
    predictions = predictor.predict_24h(base_temp=base_temp)

    total_kwh = sum(p["kwh_previsto"] for p in predictions)
    from app.core.config import settings
    custo_total = round(total_kwh * settings.ENERGIA_TARIFA_KWH_BRL, 2)

    # Recomendações baseadas em regras simples (A07)
    recommendations = []
    high_hours = [p for p in predictions if p["kwh_previsto"] > 1.5 and p["is_operating_hour"]]
    if high_hours:
        hours_str = ", ".join(str(p["hour_of_day"]) + "h" for p in high_hours[:3])
        recommendations.append(
            f"Pico de consumo previsto às {hours_str}. "
            "Considere reduzir o setpoint para 25°C nesses horários."
        )
    if total_kwh > 20:
        recommendations.append(
            "Consumo total elevado. Verifique se dispositivos estão ligados fora do horário comercial."
        )
    recommendations.append(
        f"Temperatura base atual: {base_temp:.1f}°C. "
        "Manter setpoint entre 23-25°C pode reduzir o consumo em até 15%."
    )

    return {
        "data": {
            "hourly_predictions": predictions,
            "total_kwh_24h": round(total_kwh, 2),
            "custo_estimado_brl": custo_total,
            "base_temp_celsius": round(base_temp, 1),
            "model_version": predictor.model_version,
            "confidence_avg": round(
                sum(p["confidence"] for p in predictions) / len(predictions), 2
            ),
            "recommendations": recommendations,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    }


@router.post("/train", status_code=202, summary="Retreinar modelo com dados históricos")
async def trigger_retrain(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> dict:
    """Agenda retreinamento do modelo ML com últimos 30 dias de dados."""
    from datetime import timedelta
    from app.ml.predictor import predictor

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    rows = (await db.execute(
        select(SensorData)
        .where(SensorData.tipo == "temperature", SensorData.timestamp >= cutoff)
        .order_by(SensorData.timestamp)
    )).scalars().all()

    records = [
        {"timestamp": r.timestamp, "valor": r.valor, "sensor_id": r.sensor_id}
        for r in rows
    ]

    def _train_task() -> None:
        metrics = predictor.train(records)
        logger.info("Retreinamento concluído | metrics=%s", metrics)

    background_tasks.add_task(_train_task)
    return {
        "message": "Retreinamento agendado em background.",
        "n_samples": len(records),
    }
