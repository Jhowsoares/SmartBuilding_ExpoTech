#!/usr/bin/env python3
"""
Exporta o openapi.yaml estático a partir do app FastAPI e enriquece metadados
de DX exigidos pela avaliação (exemplos de login, contato, depreciação).
"""
from __future__ import annotations

import argparse
import copy
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).parent.parent
BACKEND = ROOT / "backend"
DOCS = ROOT / "docs"
OUTPUT = DOCS / "openapi.yaml"

HTTP_METHODS = ("get", "post", "put", "patch", "delete")
PROBLEM_SCHEMA_REF = {"$ref": "#/components/schemas/ProblemDetail"}
BASE_ERROR_TYPE = "https://smartbuilding.local/errors"


def get_openapi_schema() -> dict:
    import os

    # Força URL PostgreSQL — export não deve depender de .env/shell de testes.
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://export:export@localhost:5432/export"
    os.environ.pop("TESTING", None)

    sys.path.insert(0, str(BACKEND))
    from app.main import app  # noqa: PLC0415

    return app.openapi()


def _problem_detail_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "title": "ProblemDetail",
        "description": "RFC 7807 — Problem Details for HTTP APIs.",
        "required": ["type", "title", "status", "detail"],
        "properties": {
            "type": {
                "type": "string",
                "format": "uri",
                "description": "URI que identifica o tipo do problema.",
                "example": f"{BASE_ERROR_TYPE}/unauthorized",
            },
            "title": {
                "type": "string",
                "description": "Resumo legível do erro.",
                "example": "Não autenticado",
            },
            "status": {
                "type": "integer",
                "description": "Código HTTP da resposta.",
                "example": 401,
            },
            "detail": {
                "type": "string",
                "description": "Explicação específica desta ocorrência.",
                "example": "Token ausente ou inválido.",
            },
            "instance": {
                "type": "string",
                "description": "URI da requisição que gerou o erro.",
                "example": "/api/v1/rooms",
            },
            "errors": {
                "type": "array",
                "description": "Detalhes adicionais (ex.: campos inválidos em 422).",
                "items": {"type": "object"},
            },
            "rule": {
                "type": "string",
                "description": "Identificador da regra de negócio (409).",
            },
            "subsystems": {
                "type": "object",
                "description": "Estado dos subsistemas (503 no health check).",
            },
        },
    }


def _problem_response(
    status: int,
    *,
    description: str,
    title: str,
    detail: str,
    slug: str,
) -> dict[str, Any]:
    example = {
        "type": f"{BASE_ERROR_TYPE}/{slug}",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": "/api/v1/exemplo",
    }
    body = {
        "description": description,
        "content": {
            "application/problem+json": {
                "schema": PROBLEM_SCHEMA_REF,
                "example": example,
            },
            "application/json": {
                "schema": PROBLEM_SCHEMA_REF,
                "example": example,
            },
        },
    }
    return body


def _standard_error_responses() -> dict[int, dict[str, Any]]:
    return {
        401: _problem_response(
            401,
            description="Não autenticado — token JWT ausente, expirado ou inválido.",
            title="Não autenticado",
            detail="Forneça um Bearer token válido no header Authorization.",
            slug="unauthorized",
        ),
        403: _problem_response(
            403,
            description="Acesso negado — autenticado, mas sem permissão (RBAC/BOPLA).",
            title="Acesso negado",
            detail="Seu perfil não possui permissão para esta operação.",
            slug="forbidden",
        ),
        404: _problem_response(
            404,
            description="Recurso não encontrado.",
            title="Recurso não encontrado",
            detail="O identificador informado não corresponde a um recurso existente.",
            slug="not-found",
        ),
        409: _problem_response(
            409,
            description="Conflito de regra de negócio ou estado do recurso.",
            title="Conflito de estado",
            detail="A operação conflita com o estado atual do servidor.",
            slug="business-rule-violation",
        ),
        422: _problem_response(
            422,
            description="Erro de validação — parâmetros ou corpo semanticamente inválidos.",
            title="Erro de validação",
            detail="page: ensure this value is greater than or equal to 1",
            slug="validation-error",
        ),
        429: _problem_response(
            429,
            description="Limite de requisições excedido (rate limiting via Redis/IP).",
            title="Limite de requisições atingido",
            detail="Aguarde antes de tentar novamente.",
            slug="rate-limit-exceeded",
        ),
        500: _problem_response(
            500,
            description="Erro interno inesperado.",
            title="Erro interno do servidor",
            detail="Um erro inesperado ocorreu. Tente novamente mais tarde.",
            slug="internal-error",
        ),
        503: _problem_response(
            503,
            description="Serviço indisponível ou operação bloqueada por degradação controlada.",
            title="Serviço indisponível",
            detail="Subsistema dependente indisponível ou operação já em andamento.",
            slug="service-unavailable",
        ),
    }


def _merge_response(responses: dict, code: int, payload: dict[str, Any]) -> None:
    key = str(code)
    if key not in responses:
        responses[key] = copy.deepcopy(payload)


def _path_has_params(path: str) -> bool:
    return bool(re.search(r"\{[^}]+\}", path))


def _operation_is_protected(path: str, operation: dict[str, Any]) -> bool:
    security = operation.get("security")
    if security is not None:
        return bool(security)
    return path not in {
        "/api/v1/health",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
    }


def _enrich_error_responses(schema: dict) -> None:
    errors = _standard_error_responses()
    paths: dict[str, Any] = schema.get("paths", {})

    for path, path_item in paths.items():
        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not operation:
                continue

            responses: dict[str, Any] = operation.setdefault("responses", {})
            protected = _operation_is_protected(path, operation)

            # Substitui 422 gerado pelo FastAPI pelo ProblemDetail (runtime real).
            responses["422"] = copy.deepcopy(errors[422])

            _merge_response(responses, 429, errors[429])

            if protected:
                _merge_response(responses, 401, errors[401])
                _merge_response(responses, 403, errors[403])

            if _path_has_params(path):
                _merge_response(responses, 404, errors[404])

            if method in {"post", "put", "patch"}:
                _merge_response(responses, 409, errors[409])

            if method in {"post", "put", "patch", "delete"}:
                _merge_response(responses, 500, errors[500])

            if path == "/api/v1/health" and method == "get":
                _merge_response(responses, 503, errors[503])

            if path == "/api/v1/auth/login" and method == "post":
                responses["401"] = _problem_response(
                    401,
                    description="Credenciais inválidas.",
                    title="Não autenticado",
                    detail="E-mail ou senha incorretos.",
                    slug="unauthorized",
                )

            if path == "/api/v1/auth/refresh" and method == "post":
                responses["401"] = _problem_response(
                    401,
                    description="Refresh token inválido, expirado ou revogado.",
                    title="Não autenticado",
                    detail="Renove a sessão com login ou use um refresh token válido.",
                    slug="unauthorized",
                )

            if path == "/api/v1/predictions/train" and method == "post":
                train_503 = copy.deepcopy(errors[503])
                train_503["description"] = (
                    "Retreinamento já em andamento (throttling por semáforo) "
                    "ou subsistema indisponível."
                )
                responses["503"] = train_503


def enrich_openapi(schema: dict) -> dict:
    """Camada editorial sobre o schema gerado pelo FastAPI (design-first + DX)."""
    out = copy.deepcopy(schema)
    info = out.setdefault("info", {})
    info.setdefault("contact", {"name": "Smart Building ExpoTech", "email": "suporte@smartbuilding.local"})
    info.setdefault(
        "description",
        "Sistema de controle inteligente de ar-condicionado — contrato sincronizado "
        "com o código via CI (contract-check). Erros seguem RFC 7807 (Problem Details).",
    )

    components = out.setdefault("components", {})
    schemas = components.setdefault("schemas", {})
    schemas["ProblemDetail"] = _problem_detail_schema()

    paths = out.get("paths", {})
    login_op = paths.get("/api/v1/auth/login", {}).get("post")
    if login_op:
        content = login_op.setdefault("requestBody", {}).setdefault("content", {})
        json_body = content.setdefault("application/json", {})
        json_body.setdefault("examples", {
            "admin": {
                "summary": "Login como administrador",
                "value": {"email": "admin@smartbuilding.local", "password": "admin123"},
            },
            "operador": {
                "summary": "Login como operador",
                "value": {"email": "operador@smartbuilding.local", "password": "op123"},
            },
        })

    history_path = "/api/v1/sensors/{sensor_id}/data"
    history_op = paths.get(history_path, {}).get("get")
    if history_op:
        history_op["deprecated"] = True
        history_op.setdefault(
            "description",
            "Endpoint legado. Depreciado em 2027-01-01; sunset em 2027-06-01.",
        )

    _enrich_error_responses(out)
    return out


def dict_to_yaml(schema: dict) -> str:
    return yaml.dump(
        schema,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        indent=2,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporta openapi.yaml do FastAPI")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Apenas verifica se o arquivo está atualizado (exit 1 se divergir)",
    )
    args = parser.parse_args()

    print("Carregando schema OpenAPI do FastAPI...")
    schema = enrich_openapi(get_openapi_schema())
    yaml_content = dict_to_yaml(schema)

    if args.check:
        if not OUTPUT.exists():
            print(f"ERRO: {OUTPUT} não existe. Rode sem --check para gerar.")
            sys.exit(1)
        current = OUTPUT.read_text(encoding="utf-8")
        if current == yaml_content:
            print("openapi.yaml está atualizado.")
        else:
            print(
                "ERRO: openapi.yaml está desatualizado em relação ao código.\n"
                "Rode 'python tools/export_openapi.py' e commite o resultado."
            )
            sys.exit(1)
    else:
        DOCS.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(yaml_content, encoding="utf-8")
        paths = schema.get("paths", {})
        total = sum(
            len([m for m in methods if m in {"get", "post", "put", "patch", "delete"}])
            for methods in paths.values()
        )
        print(f"openapi.yaml exportado para {OUTPUT}")
        print(f"  {len(paths)} paths · {total} operações · versão {schema.get('info', {}).get('version', '?')}")


if __name__ == "__main__":
    main()
