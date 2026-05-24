"""Repositório de Rooms."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.room import Room
from app.schemas.room import RoomCreate, RoomUpdate


class RoomRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, payload: RoomCreate) -> Room:
        room = Room(
            name=payload.name,
            building=payload.building,
            floor=payload.floor,
            area_m2=payload.area_m2,
        )
        self._db.add(room)
        await self._db.flush()
        await self._db.refresh(room)
        return room

    async def get_by_id(self, room_id: uuid.UUID) -> Optional[Room]:
        result = await self._db.execute(select(Room).where(Room.id == room_id))
        return result.scalar_one_or_none()

    async def list_rooms(self, building: Optional[str] = None,
                         page: int = 1, size: int = 20) -> Tuple[List[Room], int]:
        q = select(Room)
        if building:
            q = q.where(Room.building == building)
        total = (await self._db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        rows = (await self._db.execute(q.order_by(Room.building, Room.floor, Room.name)
                                        .offset((page - 1) * size).limit(size))).scalars().all()
        return list(rows), total

    async def update(self, room: Room, payload: RoomUpdate) -> Room:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(room, field, value)
        room.updated_at = datetime.now(timezone.utc)
        await self._db.flush()
        await self._db.refresh(room)
        return room

    async def delete(self, room_id: uuid.UUID) -> bool:
        room = await self.get_by_id(room_id)
        if not room:
            return False
        await self._db.delete(room)
        await self._db.flush()
        return True
