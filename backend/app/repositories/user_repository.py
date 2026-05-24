"""Repositório de Users."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import hash_password
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(self, payload: UserCreate) -> User:
        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            role=payload.role,
        )
        self._db.add(user)
        await self._db.flush()
        await self._db.refresh(user)
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        result = await self._db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def list_users(self, page: int = 1, size: int = 20) -> Tuple[List[User], int]:
        q = select(User)
        total = (await self._db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
        rows = (await self._db.execute(q.order_by(User.created_at.desc())
                                        .offset((page - 1) * size).limit(size))).scalars().all()
        return list(rows), total

    async def update(self, user: User, payload: UserUpdate) -> User:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        user.updated_at = datetime.now(timezone.utc)
        await self._db.flush()
        await self._db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        await self._db.flush()
