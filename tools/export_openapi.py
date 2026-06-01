#!/usr/bin/env python3
"""
Exporta o openapi.yaml estático a partir do app FastAPI e enriquece metadados
de DX exigidos pela avaliação (exemplos de login, contato, depreciação).
"""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent
BACKEND = ROOT / "backend"
DOCS = ROOT / "docs"
OUTPUT = DOCS / "openapi.yaml"


def get_openapi_schema() -> dict:
    import os

    # Força URL PostgreSQL — export não deve depender de .env/shell de testes.
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://export:export@localhost:5432/export"
    os.environ.pop("TESTING", None)

    sys.path.insert(0, str(BACKEND))
    from app.main import app  # noqa: PLC0415

    return app.openapi()


def enrich_openapi(schema: dict) -> dict:
    """Camada editorial sobre o schema gerado pelo FastAPI (design-first + DX)."""
    out = copy.deepcopy(schema)
    info = out.setdefault("info", {})
    info.setdefault("contact", {"name": "Smart Building ExpoTech", "email": "suporte@smartbuilding.local"})
    info.setdefault(
        "description",
        "Sistema de controle inteligente de ar-condicionado — contrato sincronizado "
        "com o código via CI (contract-check).",
    )

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
