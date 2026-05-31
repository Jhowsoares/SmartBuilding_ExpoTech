"""
RFC 7807 — Problem Details for HTTP APIs
https://datatracker.ietf.org/doc/html/rfc7807

Substitui as respostas de erro genéricas do FastAPI por um formato padronizado.
Adicione ao main.py:

    from app.errors.handlers import register_error_handlers
    register_error_handlers(app)
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


# ---------------------------------------------------------------------------
# Schema base — Problem Details (RFC 7807)
# ---------------------------------------------------------------------------

def problem_detail(
    *,
    type_: str,
    title: str,
    status: int,
    detail: str,
    instance: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """
    Monta um body no formato RFC 7807.

    Exemplo de resposta 422:
    {
        "type": "https://smartbuilding.local/errors/validation-error",
        "title": "Erro de validação",
        "status": 422,
        "detail": "O campo 'page_size' deve ser entre 1 e 100.",
        "instance": "/api/v1/sensors/room-101/data"
    }
    """
    body: dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
    }
    if instance:
        body["instance"] = instance
    body.update(extra)
    return body


BASE_URL = "https://smartbuilding.local/errors"


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------

def _problem_response(body: dict, status_code: int) -> JSONResponse:
    return JSONResponse(
        content=body,
        status_code=status_code,
        media_type="application/problem+json",
    )


def register_error_handlers(app: FastAPI) -> None:
    """Registra todos os handlers de erro RFC 7807 no app FastAPI."""

    # -----------------------------------------------------------------------
    # 400 / 404 / 405 / etc — HTTPException genérico
    # -----------------------------------------------------------------------
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        status_map = {
            400: ("bad-request",          "Requisição inválida"),
            401: ("unauthorized",         "Não autenticado"),
            403: ("forbidden",            "Acesso negado"),
            404: ("not-found",            "Recurso não encontrado"),
            405: ("method-not-allowed",   "Método não permitido"),
            409: ("conflict",             "Conflito de estado"),
            429: ("rate-limit-exceeded",  "Limite de requisições atingido"),
            500: ("internal-error",       "Erro interno do servidor"),
            503: ("service-unavailable",  "Serviço indisponível"),
        }
        slug, title = status_map.get(exc.status_code, ("error", "Erro"))
        body = problem_detail(
            type_=f"{BASE_URL}/{slug}",
            title=title,
            status=exc.status_code,
            detail=str(exc.detail),
            instance=str(request.url.path),
        )
        return _problem_response(body, exc.status_code)

    # -----------------------------------------------------------------------
    # 422 — Validação do Pydantic / query params inválidos
    # Diferença importante:
    #   400 = erro do cliente (recurso não existe, lógica errada)
    #   422 = corpo ou parâmetros sintaticamente corretos mas semanticamente inválidos
    # -----------------------------------------------------------------------
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        # Detalha o primeiro erro; lista todos em "errors"
        first = errors[0] if errors else {}
        field = " → ".join(str(loc) for loc in first.get("loc", []))
        detail = f"{field}: {first.get('msg', 'valor inválido')}" if field else "Dados inválidos."

        body = problem_detail(
            type_=f"{BASE_URL}/validation-error",
            title="Erro de validação",
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            instance=str(request.url.path),
            errors=[
                {
                    "field": " → ".join(str(l) for l in e.get("loc", [])),
                    "message": e.get("msg"),
                    "type": e.get("type"),
                }
                for e in errors
            ],
        )
        return _problem_response(body, status.HTTP_422_UNPROCESSABLE_ENTITY)

    # -----------------------------------------------------------------------
    # 409 — Conflito de regra de negócio (ex: sala já com override ativo)
    # Diferença:
    #   400 = erro do cliente puro (input malformado)
    #   409 = input correto, mas conflito com o estado atual do servidor
    # -----------------------------------------------------------------------
    # Use BusinessRuleException nos seus serviços para disparar 409:
    @app.exception_handler(BusinessRuleException)
    async def business_rule_handler(request: Request, exc: "BusinessRuleException"):
        body = problem_detail(
            type_=f"{BASE_URL}/business-rule-violation",
            title="Violação de regra de negócio",
            status=status.HTTP_409_CONFLICT,
            detail=str(exc),
            instance=str(request.url.path),
            rule=getattr(exc, "rule_id", None),
        )
        return _problem_response(body, status.HTTP_409_CONFLICT)

    # -----------------------------------------------------------------------
    # 500 — Erros não tratados (fallback)
    # -----------------------------------------------------------------------
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        body = problem_detail(
            type_=f"{BASE_URL}/internal-error",
            title="Erro interno do servidor",
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Um erro inesperado ocorreu. Tente novamente mais tarde.",
            instance=str(request.url.path),
        )
        return _problem_response(body, status.HTTP_500_INTERNAL_SERVER_ERROR)


# ---------------------------------------------------------------------------
# Exceção customizada para regras de negócio (409)
# ---------------------------------------------------------------------------

class BusinessRuleException(Exception):
    """
    Lançada quando uma operação viola uma regra de negócio (RN01–RN10).

    Exemplo:
        raise BusinessRuleException(
            "RN04: Override manual ativo. Aguarde 30 minutos.",
            rule_id="RN04"
        )
    """
    def __init__(self, message: str, rule_id: str | None = None):
        super().__init__(message)
        self.rule_id = rule_id
