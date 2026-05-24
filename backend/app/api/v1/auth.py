"""Autenticação JWT — POST /api/v1/auth/login|refresh|logout."""

from __future__ import annotations
import logging
from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_db
from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token, create_refresh_token, decode_token, verify_password,
)
from app.repositories.user_repository import UserRepository
from app.schemas.token import LoginRequest, TokenResponse, RefreshRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])
_bearer = HTTPBearer(auto_error=False)


@router.post("/login", response_model=TokenResponse, summary="Autenticar e obter tokens JWT")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    repo = UserRepository(db)
    user = await repo.get_by_email(body.email)
    if not user or not user.is_active:
        raise UnauthorizedError("Credenciais inválidas.")
    if not verify_password(body.password, user.password_hash):
        raise UnauthorizedError("Credenciais inválidas.")
    payload = {"sub": str(user.id), "email": user.email, "role": user.role.value}
    logger.info("Login realizado | email=%s role=%s", user.email, user.role)
    return TokenResponse(
        access_token=create_access_token(payload),
        refresh_token=create_refresh_token(payload),
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse, summary="Renovar access token")
async def refresh(body: RefreshRequest) -> TokenResponse:
    try:
        payload = decode_token(body.refresh_token)
    except Exception:
        raise UnauthorizedError("Refresh token inválido ou expirado.")
    if payload.get("type") != "refresh":
        raise UnauthorizedError("Token não é do tipo refresh.")
    new_payload = {"sub": payload["sub"], "email": payload.get("email"), "role": payload.get("role")}
    return TokenResponse(
        access_token=create_access_token(new_payload),
        refresh_token=create_refresh_token(new_payload),
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", status_code=200, summary="Revogar token (logout)")
async def logout(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    if credentials:
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
            token = credentials.credentials
            payload = decode_token(token)
            exp = payload.get("exp", 0)
            import time
            ttl = max(1, int(exp - time.time()))
            await r.setex(f"blacklist:{token[:32]}", ttl, "1")
            await r.aclose()
        except Exception:
            pass
    return {"message": "Logout realizado com sucesso."}
