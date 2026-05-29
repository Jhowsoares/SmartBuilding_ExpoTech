"""
Ponto de entrada da aplicação Smart Building API.

Responsabilidades deste módulo:
  - Criar a instância FastAPI com metadados do openapi.yaml
  - Configurar CORS para o frontend React
  - Registrar handlers de exceção (RFC 7807)
  - Montar todos os routers via api_router
  - Gerenciar o ciclo de vida da aplicação (lifespan)

Execução:
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Swagger UI:  http://localhost:8000/api/docs
ReDoc:       http://localhost:8000/api/redoc
OpenAPI:     http://localhost:8000/api/openapi.json
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers

# ─────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# LIFESPAN (startup / shutdown)
# ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gerencia o ciclo de vida da aplicação.

    Startup:
      - Inicia o cliente MQTT em background (quando configurado)
      - TODO: iniciar pool de conexões do banco (SQLAlchemy)
      - TODO: conectar ao Redis

    Shutdown:
      - Fecha conexões abertas de forma graciosa
    """
    logger.info("========================================")
    logger.info("  Smart Building API  v%s  iniciando", settings.APP_VERSION)
    logger.info("  Ambiente: %s", settings.ENVIRONMENT)
    logger.info("========================================")

    # ── Verificação de conectividade com o banco ────────────
    from app.db.database import ping_db
    if await ping_db():
        logger.info("PostgreSQL: conectado com sucesso")
    else:
        logger.warning(
            "PostgreSQL: falha na conexão inicial — "
            "verifique se o serviço postgres está em execução. "
            "Migrations: docker compose exec backend alembic upgrade head"
        )

    # ── MQTT client ─────────────────────────────────────────
    from app.mqtt.client import mqtt_client
    from app.mqtt.handlers import register_mqtt_subscriptions, set_main_event_loop
    try:
        # Grava o loop principal para que os callbacks MQTT
        # (em thread paho) possam usar run_coroutine_threadsafe
        set_main_event_loop(asyncio.get_running_loop())
        mqtt_client.connect()
        register_mqtt_subscriptions()
        logger.info("MQTT client iniciado e tópicos subscritos.")
    except Exception as exc:
        logger.warning("MQTT client: falha ao conectar — %s (continuando sem MQTT)", exc)

    yield  # aplicação em execução

    logger.info("Smart Building API encerrando...")
    mqtt_client.disconnect()

    # ── Fechamento gracioso do engine do banco ───────────────
    from app.db.database import engine
    await engine.dispose()
    logger.info("Pool de conexões do banco encerrado.")
    logger.info("Até logo.")


# ─────────────────────────────────────────────────────────────
# INSTÂNCIA FASTAPI
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    # Swagger e ReDoc sob /api/docs e /api/redoc (RNF06)
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    # Referência ao contrato externo (Design API-First)
    openapi_tags=[
        {"name": "Health",      "description": "Monitoramento de saúde dos subsistemas"},
        {"name": "Auth",        "description": "Autenticação e gestão de tokens JWT"},
        {"name": "Sensors",     "description": "Ingestão e consulta de dados dos sensores IoT"},
        {"name": "Devices",     "description": "Gestão e controle dos dispositivos (AC)"},
        {"name": "Rooms",       "description": "Gestão das salas do edifício"},
        {"name": "Alerts",      "description": "Alertas e notificações do sistema"},
        {"name": "Consumption", "description": "Histórico e análise de consumo energético"},
        {"name": "Predictions", "description": "Predições de consumo geradas pelo modelo de IA"},
        {"name": "Reports",     "description": "Relatórios consolidados exportáveis"},
        {"name": "Users",       "description": "Gestão de usuários e controle de acesso (RBAC)"},
    ],
    lifespan=lifespan,
    # Segurança: não expor detalhes de servidor no header
    # (configurado via proxy reverso em produção)
)


# ─────────────────────────────────────────────────────────────
# CORS
# Permite que o frontend React (localhost:3000/5173) e o dashboard
# em produção consumam a API sem bloqueios de browser.
# ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)


# ─────────────────────────────────────────────────────────────
# MIDDLEWARE — Cache-Control (LGPD / RFC 7234)
# Respostas da API com dados autenticados nunca devem ser
# armazenadas em caches intermediários (proxies, CDNs).
# Assets estáticos do frontend ficam com public+immutable
# (configurado no nginx.conf do container frontend).
# ─────────────────────────────────────────────────────────────
@app.middleware("http")
async def cache_control_middleware(request: Request, call_next) -> Response:
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        # Dados sensíveis: não cachear em nenhum intermediário (LGPD)
        response.headers.setdefault("Cache-Control", "private, no-store")
        response.headers.setdefault("Pragma", "no-cache")
    return response


# ─────────────────────────────────────────────────────────────
# EXCEPTION HANDLERS (RFC 7807 Problem Details)
# ─────────────────────────────────────────────────────────────
register_exception_handlers(app)


# ─────────────────────────────────────────────────────────────
# ROUTERS
# Todos sob /api/v1 conforme openapi.yaml → servers[0].url
# ─────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")


# ─────────────────────────────────────────────────────────────
# REDIRECT RAIZ → SWAGGER
# ─────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root() -> JSONResponse:
    return JSONResponse(
        content={
            "message": "Smart Building API",
            "version": settings.APP_VERSION,
            "docs": "/api/docs",
            "redoc": "/api/redoc",
            "openapi": "/api/openapi.json",
            "health": "/api/v1/health",
        }
    )
