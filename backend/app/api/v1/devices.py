"""Dispositivos — /api/v1/devices — CRUD completo + controle."""
from __future__ import annotations
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_admin, require_operador
from app.models.device import DeviceStatus
from app.schemas.base import PaginationMeta
from app.schemas.device import (
    DeviceCreate, DeviceControlRequest, DeviceControlResponse,
    DeviceResponse, DeviceUpdate,
)
from app.services.device_service import DeviceService

router = APIRouter(prefix="/devices", tags=["Devices"])


@router.get("", status_code=200, summary="Listar dispositivos")
async def list_devices(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    room_id: Optional[uuid.UUID] = Query(None),
    status: Optional[DeviceStatus] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    service = DeviceService(db)
    devices, total = await service.list_devices(room_id=room_id, status=status, page=page, size=size)
    total_pages = max(1, -(-total // size)) if total else 0
    return {
        "data": [d.model_dump() for d in devices],
        "meta": PaginationMeta(total=total, page=page, size=size, total_pages=total_pages).model_dump(),
    }


@router.post("", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED,
             summary="Cadastrar dispositivo")
async def create_device(
    payload: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> DeviceResponse:
    service = DeviceService(db)
    return await service.create_device(payload, user_id=current_user.get("sub", "system"))


@router.get("/{device_id}", response_model=DeviceResponse, status_code=200,
            summary="Detalhes de um dispositivo")
async def get_device(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> DeviceResponse:
    service = DeviceService(db)
    return await service.get_device(device_id)


@router.patch("/{device_id}", response_model=DeviceResponse, status_code=200,
              summary="Atualizar dispositivo")
async def update_device(
    device_id: uuid.UUID,
    payload: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> DeviceResponse:
    service = DeviceService(db)
    return await service.update_device(device_id, payload, user_id=current_user.get("sub", "system"))


@router.delete("/{device_id}", status_code=204, response_class=Response, summary="Desativar dispositivo")
async def delete_device(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> Response:
    service = DeviceService(db)
    await service.delete_device(device_id, user_id=current_user.get("sub", "system"))
    return Response(status_code=204)


@router.post("/{device_id}/control", response_model=DeviceControlResponse, status_code=200,
             summary="Controlar dispositivo (ligar/desligar/setpoint)")
async def control_device(
    device_id: uuid.UUID,
    payload: DeviceControlRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_operador),
) -> DeviceControlResponse:
    service = DeviceService(db)
    return await service.control_device(device_id, payload, user_id=current_user.get("sub", "system"))


@router.get("/{device_id}/status", response_model=DeviceResponse, status_code=200,
            summary="Status atual do dispositivo")
async def get_device_status(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> DeviceResponse:
    service = DeviceService(db)
    return await service.get_device(device_id)
