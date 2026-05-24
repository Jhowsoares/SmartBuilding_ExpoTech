"""Serviço de Users."""
from __future__ import annotations
import logging
import uuid
from typing import List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.core.exceptions import ResourceNotFoundError, ConflictError

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = UserRepository(db)
        self._audit = AuditRepository(db)

    async def create_user(self, payload: UserCreate, acting_user_id: str = "system") -> UserResponse:
        existing = await self._repo.get_by_email(payload.email)
        if existing:
            raise ConflictError(f"E-mail '{payload.email}' já está em uso.")
        user = await self._repo.create(payload)
        await self._audit.log(action="user_create", user_id=acting_user_id,
                               resource=str(user.id), metadata={"email": user.email, "role": user.role.value})
        logger.info("Usuário criado | id=%s email=%s role=%s", user.id, user.email, user.role)
        return self._to_response(user)

    async def list_users(self, page: int = 1, size: int = 20) -> Tuple[List[UserResponse], int]:
        users, total = await self._repo.list_users(page=page, size=size)
        return [self._to_response(u) for u in users], total

    async def get_user(self, user_id: uuid.UUID) -> UserResponse:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        return self._to_response(user)

    async def update_user(self, user_id: uuid.UUID, payload: UserUpdate,
                          acting_user_id: str = "system") -> UserResponse:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        user = await self._repo.update(user, payload)
        await self._audit.log(action="user_update", user_id=acting_user_id,
                               resource=str(user_id), metadata=payload.model_dump(exclude_unset=True))
        return self._to_response(user)

    async def delete_user(self, user_id: uuid.UUID, acting_user_id: str = "system") -> None:
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        await self._repo.delete(user)
        await self._audit.log(action="user_delete", user_id=acting_user_id,
                               resource=str(user_id), metadata={})

    @staticmethod
    def _to_response(user: User) -> UserResponse:
        return UserResponse(
            id=user.id, email=user.email, role=user.role,
            is_active=user.is_active, created_at=user.created_at, updated_at=user.updated_at,
            links=UserResponse.build_links(user.id),
        )
