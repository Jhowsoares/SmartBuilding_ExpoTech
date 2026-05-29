from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_admin
from app.models.sensor_data import SensorData

router = APIRouter(prefix="/predictions", tags=["Predictions"])
logger = logging.getLogger(__name__)

# Semáforo: apenas 1 treino simultâneo (operação cara, ~30s)
# Critério de performance/resiliência — throttling por concorrência
_train_semaphore = asyncio.Semaphore(1)

BRASILIA_OFFSET = timedelta(hours=-3)
BRASILIA_TZ = timezone(BRASILIA_OFFSET, name="BRT")

# Cache em memória para não “sumir” a série quando o modelo falhar ou estiver treinando
_LAST_GOOD_SERIES: list[dict] = []


def _now_brazil() -> datetime:
    return datetime.now(timezone.utc).astimezone(BRASILIA_TZ)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        number = float(value)
        if number != number:  # NaN
            return default
        return number
    except (TypeError, ValueError):
        return default


def _safe_hour(value: Any) -> int | None:
    try:
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            if ":" in value:
                value = value.split(":")[0]
        hour = int(value)
        return hour if 0 <= hour <= 23 else None
    except (TypeError, ValueError):
        return None


async def _get_base_temp(db: AsyncSession) -> float:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=2)
    result = await db.execute(
        select(func.avg(SensorData.valor)).where(
            SensorData.tipo == "temperature",
            SensorData.timestamp >= cutoff,
        )
    )
    val = result.scalar_one_or_none()
    return _safe_float(val, 24.0) or 24.0


def _extract_kwh(item: dict, default: float = 0.0) -> float:
    for key in ("kwh_previsto", "predicted", "value", "kwh", "consumption"):
        if item.get(key) is not None:
            return _safe_float(item.get(key), default)
    return default


def _extract_confidence(item: dict, default: float = 0.5) -> float:
    if item.get("confidence") is not None:
        return _safe_float(item.get("confidence"), default)
    if item.get("confidence_score") is not None:
        return _safe_float(item.get("confidence_score"), default)
    return default


def _generate_template_curve(start: datetime, base_temp: float) -> list[dict]:
    """
    Fallback de segurança quando o modelo não retorna nada aproveitável.
    Gera uma curva suave e não-zero.
    """
    base = max(0.25, 0.55 + (base_temp - 24.0) * 0.05)
    points: list[dict] = []

    for i in range(24):
        dt = start + timedelta(hours=i)
        hour = dt.hour

        if 7 <= hour <= 21:
            if 10 <= hour <= 12 or 14 <= hour <= 17:
                kwh = base * 2.2
            else:
                kwh = base * 1.4
        else:
            kwh = base * 0.7

        points.append(
            {
                "hour_of_day": hour,
                "kwh_previsto": round(max(kwh, 0.01), 3),
                "confidence": 0.5,
                "is_operating_hour": 7 <= hour <= 21,
                "label": f"{hour:02d}:00",
                "timestamp": dt.isoformat(),
            }
        )

    return points


def _reanchor_cached_series(cached: list[dict], start: datetime) -> list[dict]:
    points: list[dict] = []
    for i, item in enumerate(cached[:24]):
        dt = start + timedelta(hours=i)
        hour = dt.hour
        points.append(
            {
                "hour_of_day": hour,
                "kwh_previsto": round(_safe_float(item.get("kwh_previsto"), 0.01), 3),
                "confidence": round(_safe_float(item.get("confidence"), 0.5), 2),
                "is_operating_hour": bool(item.get("is_operating_hour", 7 <= hour <= 21)),
                "label": f"{hour:02d}:00",
                "timestamp": dt.isoformat(),
            }
        )
    return points


def _build_horizon_predictions(raw_predictions: list[dict], now_local: datetime, base_temp: float) -> list[dict]:
    """
    Gera 24 pontos futuros reais, corrigindo:
    - zeros artificiais após a meia-noite
    - previsões incompletas
    - ordem quebrada
    - ausência total de valores úteis
    """
    global _LAST_GOOD_SERIES

    start = now_local.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    target_hours = [(start + timedelta(hours=i)).hour for i in range(24)]

    # Normaliza os pontos recebidos
    normalized: list[dict] = []
    for idx, item in enumerate((raw_predictions or [])[:24]):
        hour = _safe_hour(item.get("hour_of_day"))
        if hour is None:
            hour = target_hours[idx]

        normalized.append(
            {
                "hour_of_day": hour,
                "kwh_previsto": _extract_kwh(item, 0.0),
                "confidence": _extract_confidence(item, 0.5),
                "is_operating_hour": item.get("is_operating_hour"),
            }
        )

    # Se o modelo veio vazio, usa cache ou fallback
    if not normalized:
        if _LAST_GOOD_SERIES:
            return _reanchor_cached_series(_LAST_GOOD_SERIES, start)
        return _generate_template_curve(start, base_temp)

    # Considera 0 como ausente quando existe algum valor válido na série
    has_positive = any(p["kwh_previsto"] > 0.001 for p in normalized)

    known_by_hour: dict[int, dict] = {}
    for item in normalized:
        hour = item["hour_of_day"]
        kwh = item["kwh_previsto"]

        # Zero “artificial” é tratado como falta de dado
        if has_positive and kwh <= 0.001:
            continue

        if hour not in known_by_hour:
            known_by_hour[hour] = item

    # Se tudo virou zero ou inválido, usa cache ou template
    if not known_by_hour:
        if _LAST_GOOD_SERIES:
            return _reanchor_cached_series(_LAST_GOOD_SERIES, start)
        return _generate_template_curve(start, base_temp)

    known_hours = sorted(known_by_hour.keys())

    def interpolate_hour(hour: int) -> dict:
        if hour in known_by_hour:
            return known_by_hour[hour]

        if len(known_hours) == 1:
            only = known_by_hour[known_hours[0]]
            return {
                "hour_of_day": hour,
                "kwh_previsto": only["kwh_previsto"],
                "confidence": only["confidence"],
                "is_operating_hour": only["is_operating_hour"],
            }

        prev_hour = max((h for h in known_hours if h < hour), default=known_hours[-1])
        next_hour = min((h for h in known_hours if h > hour), default=known_hours[0])

        prev_item = known_by_hour[prev_hour]
        next_item = known_by_hour[next_hour]

        span = (next_hour - prev_hour) % 24
        if span == 0:
            span = 24

        pos = (hour - prev_hour) % 24
        t = pos / span

        prev_kwh = _safe_float(prev_item["kwh_previsto"], 0.01)
        next_kwh = _safe_float(next_item["kwh_previsto"], prev_kwh)
        prev_conf = _safe_float(prev_item["confidence"], 0.5)
        next_conf = _safe_float(next_item["confidence"], prev_conf)

        return {
            "hour_of_day": hour,
            "kwh_previsto": round(max(prev_kwh + (next_kwh - prev_kwh) * t, 0.01), 3),
            "confidence": round(prev_conf + (next_conf - prev_conf) * t, 2),
            "is_operating_hour": None,
        }

    rotated: list[dict] = []
    for i, hour in enumerate(target_hours):
        src = interpolate_hour(hour)
        is_operating_hour = src.get("is_operating_hour")
        if is_operating_hour is None:
            is_operating_hour = 7 <= hour <= 21

        dt = start + timedelta(hours=i)
        rotated.append(
            {
                "hour_of_day": hour,
                "kwh_previsto": round(_safe_float(src.get("kwh_previsto"), 0.01), 3),
                "confidence": round(_safe_float(src.get("confidence"), 0.5), 2),
                "is_operating_hour": bool(is_operating_hour),
                "label": f"{hour:02d}:00",
                "timestamp": dt.isoformat(),
            }
        )

    # Atualiza cache apenas com série boa
    if any(p["kwh_previsto"] > 0.001 for p in rotated):
        _LAST_GOOD_SERIES = rotated

    return rotated


@router.get("/24h", status_code=200)
async def get_predictions_24h(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    from app.core.config import settings
    from app.ml.predictor import predictor

    now_local = _now_brazil()
    base_temp = await _get_base_temp(db)

    try:
        raw_predictions = predictor.predict_24h(base_temp=base_temp) or []
    except Exception:
        logger.exception("predict_24h falhou")
        raw_predictions = []

    if not raw_predictions:
        predictions = _reanchor_cached_series(_LAST_GOOD_SERIES, now_local.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)) if _LAST_GOOD_SERIES else _generate_template_curve(now_local.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1), base_temp)
    else:
        predictions = _build_horizon_predictions(raw_predictions, now_local, base_temp)

    total_kwh = sum(p["kwh_previsto"] for p in predictions)
    custo_total = round(total_kwh * settings.ENERGIA_TARIFA_KWH_BRL, 2)
    confidence_avg = round(sum(p["confidence"] for p in predictions) / len(predictions), 2) if predictions else 0.0

    recommendations: list[str] = []
    high_hours = [p for p in predictions if p["kwh_previsto"] > 1.5 and p["is_operating_hour"]]
    if high_hours:
        hours_str = ", ".join(f'{p["hour_of_day"]:02d}h' for p in high_hours[:3])
        recommendations.append(f"Pico de consumo previsto às {hours_str}.")
    if total_kwh > 20:
        recommendations.append("Consumo total elevado.")
    recommendations.append(
        f"Temperatura base atual: {base_temp:.1f}°C. "
        "Manter setpoint entre 23-25°C reduz consumo em até 15%."
    )

    return {
        "data": {
            "hourly_predictions": predictions,
            "total_kwh_24h": round(total_kwh, 2),
            "custo_estimado_brl": custo_total,
            "base_temp_celsius": round(base_temp, 1),
            "model_version": predictor.model_version,
            "confidence_avg": confidence_avg,
            "recommendations": recommendations,
            "generated_at": now_local.isoformat(),
        }
    }


@router.post("/train", status_code=202)
async def trigger_retrain(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> dict:
    """
    Retreina o modelo ML com os últimos 30 dias de dados de temperatura.

    Throttling: apenas 1 treino simultâneo via semáforo asyncio.
    Se já houver um treino em andamento, retorna 503 (degradação controlada).
    """
    # Throttling por concorrência — critério de performance/resiliência
    if _train_semaphore.locked():
        raise HTTPException(
            status_code=503,
            detail="Retreinamento já em andamento. Aguarde a conclusão e tente novamente.",
            headers={"Retry-After": "60"},
        )

    async with _train_semaphore:
        from app.ml.predictor import predictor

        cutoff = datetime.now(timezone.utc) - timedelta(days=30)

        try:
            rows = (
                await db.execute(
                    select(SensorData)
                    .where(
                        SensorData.tipo == "temperature",
                        SensorData.timestamp >= cutoff,
                    )
                    .order_by(SensorData.timestamp)
                )
            ).scalars().all()
        except Exception:
            logger.exception("Erro ao buscar dados para treino")
            return {"message": "Erro ao acessar banco de dados.", "n_samples": 0}

        records = [
            {"timestamp": r.timestamp, "valor": r.valor, "sensor_id": r.sensor_id}
            for r in rows
        ]

        try:
            metrics = predictor.train(records)
            logger.info("Treinamento concluído: %s", metrics)
            return {
                "message": "Retreinamento concluído com sucesso.",
                "n_samples": len(records),
                "metrics": metrics,
            }
        except Exception:
            logger.exception("Falha no treinamento")
            return {"message": "Falha no retreinamento.", "n_samples": len(records)}