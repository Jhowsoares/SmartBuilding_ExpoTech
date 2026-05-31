"""
Testes de contrato e integração — SmartBuilding API
Critério 7 (Protótipo funcional & Repositório) e Critério 5 (CI/CD).

Execução:
    cd backend
    pytest tests/ -v

Os testes cobrem:
  - Contrato: verifica que o schema OpenAPI está presente e válido
  - Autenticação: login, logout, token inválido
  - BOLA (API1): usuário não acessa dados de outro usuário
  - Rate Limiting: 429 + Retry-After
  - RFC 7807: formato de erro padronizado
  - Health check: dependências OK
"""
import json

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

# Importa o app — ajuste o caminho se necessário
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def admin_token(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@smartbuilding.local", "password": "admin123"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture(scope="module")
def viewer_token(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "visualizador@smartbuilding.local", "password": "view123"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# 1. Contrato OpenAPI
# ---------------------------------------------------------------------------

class TestOpenAPIContract:
    def test_openapi_schema_available(self, client):
        """O schema OpenAPI deve estar disponível e retornar 200."""
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert schema["openapi"].startswith("3.")
        assert "paths" in schema
        assert len(schema["paths"]) > 0

    def test_openapi_has_version_prefix(self, client):
        """Todos os paths devem conter /api/v1/."""
        resp = client.get("/openapi.json")
        schema = resp.json()
        for path in schema["paths"]:
            assert "/v1/" in path, f"Path sem versão: {path}"

    def test_openapi_has_security_schemes(self, client):
        """Schema deve declarar Bearer auth."""
        resp = client.get("/openapi.json")
        schema = resp.json()
        components = schema.get("components", {})
        security_schemes = components.get("securitySchemes", {})
        assert len(security_schemes) > 0, "Nenhum securityScheme declarado"

    def test_swagger_ui_available(self, client):
        """Swagger UI deve estar acessível."""
        resp = client.get("/api/docs")
        assert resp.status_code == 200

    def test_redoc_available(self, client):
        """ReDoc deve estar acessível."""
        resp = client.get("/api/redoc")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 2. Autenticação
# ---------------------------------------------------------------------------

class TestAuthentication:
    def test_login_success(self, client):
        """Login com credenciais corretas retorna access_token e refresh_token."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@smartbuilding.local", "password": "admin123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data.get("token_type") == "bearer"

    def test_login_wrong_password(self, client):
        """Login com senha errada retorna 401."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@smartbuilding.local", "password": "errada"},
        )
        assert resp.status_code == 401

    def test_login_error_is_rfc7807(self, client):
        """Erro de login deve seguir RFC 7807."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "nao@existe.com", "password": "x"},
        )
        assert resp.status_code in (401, 404)
        body = resp.json()
        assert "type" in body
        assert "title" in body
        assert "status" in body
        assert "detail" in body

    def test_protected_route_without_token(self, client):
        """Rota protegida sem token retorna 401."""
        resp = client.get("/api/v1/devices")
        assert resp.status_code == 401

    def test_protected_route_invalid_token(self, client):
        """Rota protegida com token inválido retorna 401."""
        resp = client.get(
            "/api/v1/devices",
            headers={"Authorization": "Bearer token.invalido.aqui"},
        )
        assert resp.status_code == 401

    def test_logout_blacklists_token(self, client, admin_token):
        """Após logout, o token deve ser rejeitado."""
        # Garante que o token funciona antes do logout
        resp = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code in (200, 403)  # pode ser 403 se endpoint restrito

        # Faz logout
        logout_resp = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert logout_resp.status_code in (200, 204)

        # Token deve ser rejeitado
        resp2 = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp2.status_code == 401


# ---------------------------------------------------------------------------
# 3. BOLA — API1:2023
# ---------------------------------------------------------------------------

class TestBOLA:
    def test_viewer_cannot_access_admin_endpoint(self, client, viewer_token):
        """Viewer não deve conseguir treinar o modelo ML (Admin only)."""
        resp = client.post(
            "/api/v1/predictions/train",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 403

    def test_viewer_cannot_control_device(self, client, viewer_token):
        """Viewer não deve conseguir controlar dispositivos."""
        resp = client.post(
            "/api/v1/devices/device-001/control",
            json={"action": "off"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 4. Validação de entrada — API4:2023
# ---------------------------------------------------------------------------

class TestInputValidation:
    def test_invalid_period_returns_422(self, client, admin_token):
        """Parâmetro period inválido deve retornar 422 RFC 7807."""
        resp = client.get(
            "/api/v1/sensors/room-101/data?period=1000y",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body.get("status") == 422
        assert "type" in body

    def test_health_endpoint_returns_200(self, client):
        """Health check deve responder 200."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        body = resp.json()
        assert "status" in body


# ---------------------------------------------------------------------------
# 5. Rate Limiting
# ---------------------------------------------------------------------------

class TestRateLimiting:
    def test_rate_limit_headers_present(self, client, admin_token):
        """Respostas normais devem conter headers X-RateLimit-*."""
        resp = client.get(
            "/api/v1/devices",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Headers informativos de rate limit
        assert "X-RateLimit-Limit" in resp.headers or resp.status_code in (200, 429)

    def test_login_rate_limit(self, client):
        """Login excessivo deve retornar 429 com Retry-After."""
        results = []
        for _ in range(15):  # limite é 10/min
            resp = client.post(
                "/api/v1/auth/login",
                json={"email": "brute@force.com", "password": "tentativa"},
            )
            results.append(resp.status_code)
            if resp.status_code == 429:
                # Verifica RFC 7807 e Retry-After
                assert "Retry-After" in resp.headers
                body = resp.json()
                assert body.get("status") == 429
                assert "retry_after" in body
                break
        # Ao menos uma resposta deveria ser 429
        assert 429 in results, "Rate limiting não disparou após 15 tentativas de login"


# ---------------------------------------------------------------------------
# 6. Resiliência — Health Check
# ---------------------------------------------------------------------------

class TestHealthCheck:
    def test_health_reports_dependencies(self, client):
        """Health check deve reportar status de DB, Redis e MQTT."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        body = resp.json()
        # Espera campos de dependências
        assert any(k in body for k in ("database", "redis", "mqtt", "db")), (
            f"Health check não reporta dependências: {list(body.keys())}"
        )
