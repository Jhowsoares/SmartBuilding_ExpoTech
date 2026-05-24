"""Exceções customizadas + handlers RFC 7807."""

from __future__ import annotations
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class SmartBuildingError(Exception):
    status_code: int = 500
    title: str = "Erro interno"
    def __init__(self, detail: str = "") -> None:
        self.detail = detail
        super().__init__(detail)


class ResourceNotFoundError(SmartBuildingError):
    status_code = 404
    title = "Recurso não encontrado"
    def __init__(self, resource: str, id: str = "") -> None:
        super().__init__(f"{resource} '{id}' não encontrado." if id else f"{resource} não encontrado.")


class UnauthorizedError(SmartBuildingError):
    status_code = 401
    title = "Não autorizado"


class ForbiddenError(SmartBuildingError):
    status_code = 403
    title = "Acesso negado"
    def __init__(self, role: str = "") -> None:
        super().__init__(f"Papel '{role}' não tem permissão para este recurso.")


class ConflictError(SmartBuildingError):
    status_code = 409
    title = "Conflito"


class BusinessRuleError(SmartBuildingError):
    status_code = 422
    title = "Regra de negócio violada"


def _problem(status_code: int, title: str, detail: str, instance: str = "") -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"type": f"https://smartbuilding.local/errors/{status_code}",
                 "title": title, "status": status_code,
                 "detail": detail, "instance": instance},
        headers={"Content-Type": "application/problem+json"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(SmartBuildingError)
    async def handle_domain(request: Request, exc: SmartBuildingError) -> JSONResponse:
        return _problem(exc.status_code, exc.title, exc.detail, str(request.url))

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        fields = [{"field": ".".join(str(l) for l in e["loc"]), "message": e["msg"]} for e in exc.errors()]
        return JSONResponse(
            status_code=422,
            content={"type": "https://smartbuilding.local/errors/422",
                     "title": "Erro de validação", "status": 422,
                     "detail": "Payload inválido — verifique os campos abaixo.",
                     "errors": fields},
            headers={"Content-Type": "application/problem+json"},
        )

    @app.exception_handler(Exception)
    async def handle_generic(request: Request, exc: Exception) -> JSONResponse:
        return _problem(500, "Erro interno do servidor", str(exc), str(request.url))
