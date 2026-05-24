"""Schemas Pydantic — Usuários."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole
from app.schemas.base import HateoasLink


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.VISUALIZADOR


class UserUpdate(BaseModel):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    links: List[HateoasLink] = Field(default_factory=list)

    model_config = {"from_attributes": True}

    @staticmethod
    def build_links(user_id: uuid.UUID) -> List[HateoasLink]:
        base = f"/api/v1/users/{user_id}"
        return [
            HateoasLink(rel="self", href=base),
            HateoasLink(rel="update", href=base, method="PATCH"),
        ]
