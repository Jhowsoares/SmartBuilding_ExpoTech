"""Usuários — /api/v1/users — CRUD (admin only)."""
from __future__ import annotations
import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_admin
from app.schemas.base import PaginationMeta
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", status_code=200, summary="Listar usuários (admin)")
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> dict:
    service = UserService(db)
    users, total = await service.list_users(page=page, size=size)
    total_pages = max(1, -(-total // size)) if total else 0
    return {
        "data": [u.model_dump() for u in users],
        "meta": PaginationMeta(total=total, page=page, size=size, total_pages=total_pages).model_dump(),
    }


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED,
             summary="Criar usuário (admin)")
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> UserResponse:
    service = UserService(db)
    return await service.create_user(payload, acting_user_id=current_user.get("sub", "system"))


@router.get("/me", response_model=UserResponse, status_code=200,
            summary="Perfil do usuário autenticado")
async def get_me(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> UserResponse:
    from app.repositories.user_repository import UserRepository
    repo = UserRepository(db)
    user = await repo.get_by_id(uuid.UUID(current_user["sub"]))
    if not user:
        from app.core.exceptions import ResourceNotFoundError
        raise ResourceNotFoundError("User", current_user["sub"])
    from app.schemas.user import UserResponse as UR
    return UR(
        id=user.id, email=user.email, role=user.role,
        is_active=user.is_active, created_at=user.created_at, updated_at=user.updated_at,
        links=UR.build_links(user.id),
    )


@router.get("/{user_id}", response_model=UserResponse, status_code=200,
            summary="Detalhes de um usuário (admin)")
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> UserResponse:
    service = UserService(db)
    return await service.get_user(user_id)


@router.patch("/{user_id}", response_model=UserResponse, status_code=200,
              summary="Atualizar usuário (admin)")
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> UserResponse:
    service = UserService(db)
    return await service.update_user(user_id, payload, acting_user_id=current_user.get("sub", "system"))


@router.delete("/{user_id}", status_code=204, response_class=Response, summary="Desativar usuário (admin)")
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_admin),
) -> Response:
    service = UserService(db)
    await service.delete_user(user_id, acting_user_id=current_user.get("sub", "system"))
    return Response(status_code=204)
