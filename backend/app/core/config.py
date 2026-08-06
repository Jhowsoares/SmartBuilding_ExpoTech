"""
Configurações centrais da aplicação via Pydantic Settings.

Todas as variáveis são lidas do ambiente (ou arquivo .env na raiz do backend).
Nunca coloque segredos diretamente neste arquivo — use o .env ou variáveis Docker.
"""

from __future__ import annotations

import json
from typing import List, Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ── Helper: converte CORS_ORIGINS de qualquer formato para List[str] ────────
# Recebe o valor raw da env var (sempre str quando vem do ambiente) e retorna
# uma lista limpa.  Chamado pelo model_validator após o pydantic-settings ler
# todos os campos, evitando o SettingsError que ocorre quando o tipo anotado
# é List[str] e o pydantic-settings tenta deserializar a string como JSON
# antes de qualquer BeforeValidator.
#
# Formatos aceitos:
#   "*"                                             → ["*"]  (wildcard dev)
#   "http://localhost:3000,http://localhost:5173"   → lista CSV
#   '["http://localhost:3000","http://localhost:5173"]'  → JSON array
def _parse_cors_origins(v: str) -> List[str]:
    stripped = v.strip()
    if stripped.startswith("["):
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return [str(o).strip() for o in parsed if str(o).strip()]
        except json.JSONDecodeError:
            pass
    return [origin.strip() for origin in stripped.split(",") if origin.strip()]


class Settings(BaseSettings):
    # ── Aplicação ──────────────────────────────────────────────
    APP_TITLE: str = "Smart Building API"
    APP_DESCRIPTION: str = "Sistema de controle inteligente de ar-condicionado"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = Field("development", pattern="^(development|staging|production)$")
    DEMO_MODE: bool = Field(
        False,
        description="Quando true, seed de demonstração é esperado no boot (Render/Docker demo)",
    )

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
    # Campo declarado como str para evitar que o pydantic-settings tente
    # deserializar o valor como JSON antes da nossa lógica de parsing.
    # Use cors_origins_list (property abaixo) em vez de CORS_ORIGINS direto.
    #
    # Formatos aceitos no .env / variável Docker:
    #   CORS_ORIGINS=*                                  ← development only
    #   CORS_ORIGINS=http://app.example.com,https://app.example.com
    #   CORS_ORIGINS=["http://app.example.com","https://app.example.com"]
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Origens permitidas — CSV, JSON array ou '*' (apenas development)",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """
        Converte CORS_ORIGINS para lista e bloqueia wildcard fora de development.
        Use esta property para passar ao CORSMiddleware.
        """
        origins = _parse_cors_origins(self.CORS_ORIGINS)
        if "*" in origins and self.ENVIRONMENT != "development":
            raise ValueError(
                "CORS_ORIGINS='*' não é permitido em ENVIRONMENT='%s'. "
                "Defina origens explícitas no .env." % self.ENVIRONMENT
            )
        return origins

    # ── Rate Limiting ──────────────────────────────────────────
    # Limites aplicados via slowapi sobre o IP do cliente.
    # Ajuste os valores no .env para cada ambiente.
    RATE_LIMIT_DEFAULT: str = Field(
        "200/minute",
        description="Limite padrão para endpoints autenticados gerais",
    )
    RATE_LIMIT_AUTH: str = Field(
        "10/minute",
        description="Limite para rotas de autenticação (login / refresh)",
    )
    RATE_LIMIT_SENSOR_INGEST: str = Field(
        "500/minute",
        description="Limite de ingestão para dispositivos IoT",
    )

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
