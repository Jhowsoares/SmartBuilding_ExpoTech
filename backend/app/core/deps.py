"""Dependências FastAPI — JWT, RBAC, DB session."""

from __future__ import annotations
from typing import List

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token, is_token_blacklisted
from app.db.database import get_db  # re-exporta

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> dict:
    if credentials is None:
        raise UnauthorizedError("Token JWT ausente. Use POST /api/v1/auth/login.")
    token = credentials.credentials
    if await is_token_blacklisted(token):
        raise UnauthorizedError("Token revogado. Faça login novamente.")
    try:
        payload = decode_token(token)
    except Exception:
        raise UnauthorizedError("Token JWT inválido ou expirado.")
    if payload.get("type") != "access":
        raise UnauthorizedError("Use o access_token, não o refresh_token.")
    return payload


class RoleChecker:
    def __init__(self, allowed_roles: List[str]) -> None:
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role", "") not in self.allowed_roles:
            raise ForbiddenError(current_user.get("role", ""))
        return current_user


require_admin = RoleChecker(["admin"])
require_operador = RoleChecker(["admin", "operador"])
require_visualizador = RoleChecker(["admin", "operador", "visualizador"])

__all__ = ["get_current_user", "get_db", "RoleChecker",
           "require_admin", "require_operador", "require_visualizador"]
