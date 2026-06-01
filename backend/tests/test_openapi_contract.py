"""Testes de contrato OpenAPI — Critérios 2 e 5."""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_openapi_schema_available(client: AsyncClient) -> None:
    resp = await client.get("/api/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert schema["openapi"].startswith("3.")
    assert len(schema.get("paths", {})) > 0


@pytest.mark.asyncio
async def test_openapi_paths_are_versioned(client: AsyncClient) -> None:
    schema = (await client.get("/api/openapi.json")).json()
    for path in schema["paths"]:
        assert path.startswith("/api/v1/"), f"Path sem prefixo versionado: {path}"


@pytest.mark.asyncio
async def test_openapi_declares_bearer_security(client: AsyncClient) -> None:
    schema = (await client.get("/api/openapi.json")).json()
    schemes = schema.get("components", {}).get("securitySchemes", {})
    assert schemes, "Nenhum securityScheme declarado no OpenAPI"


@pytest.mark.asyncio
async def test_login_openapi_has_examples(client: AsyncClient) -> None:
    schema = (await client.get("/api/openapi.json")).json()
    login = schema["paths"]["/api/v1/auth/login"]["post"]
    examples = (
        login.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("examples")
    )
    schema_examples = (
        login.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
        .get("examples")
    )
    component_examples = (
        schema.get("components", {})
        .get("schemas", {})
        .get("LoginRequest", {})
        .get("examples")
    )
    assert examples or schema_examples or component_examples, "Login sem exemplos no OpenAPI (TTFC)"


@pytest.mark.asyncio
async def test_swagger_and_redoc_available(client: AsyncClient) -> None:
    assert (await client.get("/api/docs")).status_code == 200
    assert (await client.get("/api/redoc")).status_code == 200
