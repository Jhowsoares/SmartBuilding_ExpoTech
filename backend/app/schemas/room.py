"""Schemas Pydantic — Salas."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.base import HateoasLink


class RoomCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    building: str = Field(..., min_length=1, max_length=100)
    floor: int = Field(..., ge=0, le=100)
    area_m2: Optional[float] = Field(None, gt=0)


class RoomUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    building: Optional[str] = Field(None, min_length=1, max_length=100)
    floor: Optional[int] = Field(None, ge=0, le=100)
    area_m2: Optional[float] = Field(None, gt=0)


class RoomResponse(BaseModel):
    id: uuid.UUID
    name: str
    building: str
    floor: int
    area_m2: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    links: List[HateoasLink] = Field(default_factory=list)

    model_config = {"from_attributes": True}

    @staticmethod
    def build_links(room_id: uuid.UUID) -> List[HateoasLink]:
        base = f"/api/v1/rooms/{room_id}"
        return [
            HateoasLink(rel="self", href=base),
            HateoasLink(rel="devices", href=f"{base}/devices"),
        ]
