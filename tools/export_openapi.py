#!/usr/bin/env python3
"""
Exporta o openapi.yaml estático a partir do app FastAPI.

Por quê isso existe:
  O FastAPI gera o schema OpenAPI dinamicamente em /openapi.json.
  A avaliação exige o arquivo openapi.yaml versionado no repositório
  como evidência de Design-first e para o Spectral lint no CI/CD.

Uso:
  python tools/export_openapi.py            # salva em docs/openapi.yaml
  python tools/export_openapi.py --check    # só verifica se está atualizado (usado no CI)

No CI (.github/workflows/ci.yml), este script roda após os testes
para garantir que o contrato está sincronizado com o código.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).parent.parent  # pasta backend/
DOCS = ROOT.parent / "docs"
OUTPUT = DOCS / "openapi.yaml"


def get_openapi_schema() -> dict:
    """Importa o app FastAPI e retorna o schema OpenAPI como dict."""
    sys.path.insert(0, str(ROOT))
    # Importa sem iniciar o servidor
    from app.main import app  # noqa: PLC0415

    return app.openapi()


def dict_to_yaml(schema: dict) -> str:
    """Converte o schema dict para YAML com formatação limpa."""
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
    schema = get_openapi_schema()
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
        print(f"openapi.yaml exportado para {OUTPUT}")
        # Conta endpoints como evidência
        paths = schema.get("paths", {})
        total = sum(
            len([m for m in methods if m in {"get","post","put","patch","delete"}])
            for methods in paths.values()
        )
        print(f"  {len(paths)} paths · {total} operações · versão {schema.get('info',{}).get('version','?')}")


if __name__ == "__main__":
    main()
