"""Alertas — /api/v1/alerts."""
from __future__ import annotations
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_operador
from app.models.alert import AlertSeverity
from app.schemas.alert import AlertCreate, AlertResponse
from app.schemas.base import PaginationMeta
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", status_code=200, summary="Listar alertas")
async def list_alerts(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    active_only: bool = Query(False, description="Somente alertas não resolvidos"),
    device_id: Optional[uuid.UUID] = Query(None),
    severity: Optional[AlertSeverity] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    service = AlertService(db)
    alerts, total = await service.list_alerts(
        active_only=active_only, device_id=device_id, severity=severity, page=page, size=size
    )
    total_pages = max(1, -(-total // size)) if total else 0
    return {
        "data": [a.model_dump() for a in alerts],
        "meta": PaginationMeta(total=total, page=page, size=size, total_pages=total_pages).model_dump(),
    }


@router.get("/history", status_code=200, summary="Histórico de alertas")
async def get_alert_history(
    days: int = Query(30, ge=1, le=365),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    service = AlertService(db)
    alerts, total = await service.get_history(days=days, page=page, size=size)
    total_pages = max(1, -(-total // size)) if total else 0
    return {
        "data": [a.model_dump() for a in alerts],
        "meta": PaginationMeta(total=total, page=page, size=size, total_pages=total_pages).model_dump(),
    }


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED,
             summary="Criar alerta manualmente")
async def create_alert(
    payload: AlertCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_operador),
) -> AlertResponse:
    service = AlertService(db)
    return await service.create_alert(payload, user_id=current_user.get("sub", "system"))


@router.get("/{alert_id}", response_model=AlertResponse, status_code=200,
            summary="Detalhes de um alerta")
async def get_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> AlertResponse:
    service = AlertService(db)
    return await service.get_alert(alert_id)


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse, status_code=200,
             summary="Reconhecer alerta")
async def acknowledge_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_operador),
) -> AlertResponse:
    service = AlertService(db)
    return await service.acknowledge_alert(alert_id, user_id=current_user.get("sub", "system"))


@router.post("/{alert_id}/resolve", response_model=AlertResponse, status_code=200,
             summary="Resolver alerta")
async def resolve_alert(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_operador),
) -> AlertResponse:
    service = AlertService(db)
    return await service.resolve_alert(alert_id, user_id=current_user.get("sub", "system"))
