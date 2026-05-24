"""
Configurações centrais da aplicação via Pydantic Settings.

Todas as variáveis são lidas do ambiente (ou arquivo .env na raiz do backend).
Nunca coloque segredos diretamente neste arquivo — use o .env ou variáveis Docker.
"""

from __future__ import annotations

import json
from typing import Annotated, List, Optional

from pydantic import Field
from pydantic.functional_validators import BeforeValidator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ── Tipo customizado para CORS_ORIGINS ──────────────────────────────────────
# BeforeValidator intercepta o valor ANTES que o pydantic-settings tente
# deserializá-lo como JSON, evitando o JSONDecodeError quando a variável de
# ambiente é uma string simples separada por vírgulas (ex.: docker-compose).
#
# Formatos aceitos:
#   "http://localhost:3000,http://localhost:5173"   → comma-separated
#   '["http://localhost:3000","http://localhost:5173"]'  → JSON array
#   ["http://localhost:3000", "http://localhost:5173"]   → lista Python (defaults)
#   "*"                                             → wildcard (desenvolvimento)

def _parse_cors_origins(v: object) -> List[str]:
    if isinstance(v, list):
        return [str(item).strip() for item in v if str(item).strip()]
    if isinstance(v, str):
        stripped = v.strip()
        # Tenta JSON array primeiro (ex: '["http://...","http://..."]')
        if stripped.startswith("["):
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, list):
                    return [str(o).strip() for o in parsed if str(o).strip()]
            except json.JSONDecodeError:
                pass
        # Fallback: string simples separada por vírgulas
        return [origin.strip() for origin in stripped.split(",") if origin.strip()]
    return []


CorsOrigins = Annotated[List[str], BeforeValidator(_parse_cors_origins)]


class Settings(BaseSettings):
    # ── Aplicação ──────────────────────────────────────────────
    APP_TITLE: str = "Smart Building API"
    APP_DESCRIPTION: str = "Sistema de controle inteligente de ar-condicionado"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = Field("development", pattern="^(development|staging|production)$")

    # ── Banco de Dados (PostgreSQL + asyncpg) ──────────────────
    DATABASE_URL: str = Field(
        "postgresql+asyncpg://smartbuilding:segura123@postgres:5432/smartbuilding",
        description="URL de conexão assíncrona com o PostgreSQL (runtime FastAPI)",
    )
    SYNC_DATABASE_URL: str = Field(
        "postgresql+psycopg2://smartbuilding:segura123@postgres:5432/smartbuilding",
        description="URL de conexão síncrona para o Alembic (migrations)",
    )

    # ── JWT ────────────────────────────────────────────────────
    JWT_SECRET: str = Field(
        "TROQUE-ESTA-CHAVE-NO-ENV-POR-UMA-SEGURA",
        min_length=32,
        description="Segredo para assinar tokens JWT — use openssl rand -hex 32",
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Redis (blacklist de tokens e cache) ────────────────────
    REDIS_URL: str = "redis://redis:6379/0"

    # ── MQTT Broker ────────────────────────────────────────────
    MQTT_BROKER: str = "mqtt"
    MQTT_PORT: int = 1883
    MQTT_USERNAME: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None
    MQTT_CLIENT_ID: str = "smartbuilding_backend"

    # ── CORS ────────────────────────────────────────────────────
    # CorsOrigins usa BeforeValidator — aceita vírgula, JSON ou wildcard
    # CORS_ORIGINS: CorsOrigins = Field(
    #     default=["http://localhost:3000", "http://localhost:5173"],
    #     description="Origens permitidas pelo CORS — string CSV, JSON array ou '*'",
    # )
    CORS_ORIGINS: str = "*"

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.CORS_ORIGINS or self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    # ── Sensor Service ─────────────────────────────────────────
    SENSOR_SERVICE_TOKEN: str = Field(
        "sensor-service-token-dev",
        description="Token estático usado pelos sensores IoT para autenticar na API",
    )

    # ── Tarifas ────────────────────────────────────────────────
    ENERGIA_TARIFA_KWH_BRL: float = Field(0.75, description="Tarifa de energia em R$/kWh")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
