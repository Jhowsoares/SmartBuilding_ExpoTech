"""Serviço de Rooms."""
from __future__ import annotations
import logging
import uuid
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room
from app.repositories.audit_repository import AuditRepository
from app.repositories.room_repository import RoomRepository
from app.schemas.room import RoomCreate, RoomResponse, RoomUpdate
from app.core.exceptions import ResourceNotFoundError

logger = logging.getLogger(__name__)


class RoomService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = RoomRepository(db)
        self._audit = AuditRepository(db)

    async def create_room(self, payload: RoomCreate, user_id: str = "system") -> RoomResponse:
        room = await self._repo.create(payload)
        await self._audit.log(action="room_create", user_id=user_id, resource=str(room.id),
                               metadata={"name": room.name, "building": room.building})
        logger.info("Sala criada | id=%s name=%s", room.id, room.name)
        return self._to_response(room)

    async def list_rooms(self, building: Optional[str] = None,
                         page: int = 1, size: int = 20) -> Tuple[List[RoomResponse], int]:
        rooms, total = await self._repo.list_rooms(building=building, page=page, size=size)
        return [self._to_response(r) for r in rooms], total

    async def get_room(self, room_id: uuid.UUID) -> RoomResponse:
        room = await self._repo.get_by_id(room_id)
        if not room:
            raise ResourceNotFoundError("Room", str(room_id))
        return self._to_response(room)

    async def update_room(self, room_id: uuid.UUID, payload: RoomUpdate,
                          user_id: str = "system") -> RoomResponse:
        room = await self._repo.get_by_id(room_id)
        if not room:
            raise ResourceNotFoundError("Room", str(room_id))
        room = await self._repo.update(room, payload)
        await self._audit.log(action="room_update", user_id=user_id, resource=str(room_id),
                               metadata=payload.model_dump(exclude_unset=True))
        return self._to_response(room)

    async def delete_room(self, room_id: uuid.UUID, user_id: str = "system") -> None:
        deleted = await self._repo.delete(room_id)
        if not deleted:
            raise ResourceNotFoundError("Room", str(room_id))
        await self._audit.log(action="room_delete", user_id=user_id, resource=str(room_id), metadata={})

    @staticmethod
    def _to_response(room: Room) -> RoomResponse:
        return RoomResponse(
            id=room.id, name=room.name, building=room.building,
            floor=room.floor, area_m2=room.area_m2,
            created_at=room.created_at, updated_at=room.updated_at,
            links=RoomResponse.build_links(room.id),
        )
