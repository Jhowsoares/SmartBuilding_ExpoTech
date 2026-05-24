"""Salas — /api/v1/rooms — CRUD completo."""
from __future__ import annotations
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_admin
from app.schemas.base import PaginationMeta
from app.schemas.room import RoomCreate, RoomResponse, RoomUpdate
from app.services.room_service import RoomService

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.get("", status_code=200, summary="Listar salas")
async def list_rooms(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    building: Optional[str] = Query(None, max_length=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> dict:
    service = RoomService(db)
    rooms, total = await service.list_rooms(building=building, page=page, size=size)
    total_pages = max(1, -(-total // size)) if total else 0
    return {
        "data": [r.model_dump() for r in rooms],
        "meta": PaginationMeta(total=total, page=page, size=size, total_pages=total_pages).model_dump(),
    }


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED,
             summary="Cadastrar sala")
async def create_room(
    payload: RoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> RoomResponse:
    service = RoomService(db)
    return await service.create_room(payload, user_id=current_user.get("sub", "system"))


@router.get("/{room_id}", response_model=RoomResponse, status_code=200,
            summary="Detalhes de uma sala")
async def get_room(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
) -> RoomResponse:
    service = RoomService(db)
    return await service.get_room(room_id)


@router.patch("/{room_id}", response_model=RoomResponse, status_code=200,
              summary="Atualizar sala")
async def update_room(
    room_id: uuid.UUID,
    payload: RoomUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> RoomResponse:
    service = RoomService(db)
    return await service.update_room(room_id, payload, user_id=current_user.get("sub", "system"))


@router.delete("/{room_id}", status_code=204, response_class=Response, summary="Excluir sala")
async def delete_room(
    room_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> Response:
    service = RoomService(db)
    await service.delete_room(room_id, user_id=current_user.get("sub", "system"))
    return Response(status_code=204)
